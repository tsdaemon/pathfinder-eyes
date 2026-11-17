#!/usr/bin/env python3
"""Relay /vo -> /vo_gated for the EKF, distrusting VO's linear velocity during fast turns.

During an in-place spin (~200 deg/s - mecanum rotation only works near full speed) VO
reports 0.1-0.7 m/s of bogus forward/sideways velocity with ~1 cm/s confidence: the camera
sits 9cm off the rotation center and turns 20-40 deg between processed frames. Fusing that
walked the EKF 27-38cm off per two in-place turns (2026-11-11).

So: when the gyro (base_link yaw rate) exceeds TURN_RATE anywhere within WINDOW of the VO
message's stamp, the vx/vy twist covariance is inflated to DISTRUST_VAR, which makes the EKF
effectively ignore it. Otherwise the variance is floored at MIN_VAR (VO is overconfident).
With no motor command for STILL_AFTER, vx/vy are replaced by a confident zero (the robot
can't be moving). Everything else passes through unchanged. See docs/depthai.md.
"""
import collections

import rclpy
import tf2_ros
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.time import Time
from sensor_msgs.msg import Imu

# Between straight driving and the slowest real turn: "straight" driving veers at up to
# ~0.95 rad/s (the chassis isn't balanced; 0.8 gated nearly all VO while driving forward,
# 2026-11-13), and the motors can't turn slower than ~1.3 rad/s (2026-11-17 calibration).
# Was 2.0: slow correction turns then slipped through and VO's bogus translation was fused.
TURN_RATE = 1.1  # rad/s
# The robot tops out at ~0.4 m/s. Faster VO readings are garbage (seen when it faces a dark,
# featureless area) and are distrusted like turns.
MAX_SPEED = 0.6  # m/s
WINDOW = (
    0.3  # s, each side of the VO stamp (VO is ~0.2s behind; spin-up/down transients)
)
DISTRUST_VAR = 100.0  # (m/s)^2
# Floor for VO's vx/vy variance at all times. VO reports ~0.001 m/s std, but parked its
# velocity zig-zags by 0.02-0.04 m/s frame to frame. Taken at face value, each value arrives
# ~0.2-0.3 s late, the EKF rewinds (smooth_lagged_data) and replays it, and the parked pose
# jumped 1.5-5 cm at a time (2026-11-17). (0.03 m/s)^2 lets the EKF average instead.
MIN_VAR = 0.03**2  # (m/s)^2
# Zero-velocity update: with no motor command the robot can't move (no wheel slip, nothing
# pushes it), so VO's noise is replaced by a confident zero. STILL_AFTER covers
# vel_to_serial's 0.5 s timeout plus coasting. Even floored, VO's noise random-walked the
# parked EKF pose ~2 cm per 20 s (2026-11-17). Misses the robot being pushed by hand.
STILL_AFTER = 0.7  # s since the last non-zero /cmd_vel
STILL_VAR = 0.005**2  # (m/s)^2


def rotate_z(q, v):
    # z component of vector v rotated by quaternion q (x, y, z, w).
    x, y, z, w = q
    vx, vy, vz = v
    tx, ty, tz = 2 * (y * vz - z * vy), 2 * (z * vx - x * vz), 2 * (x * vy - y * vx)
    return vz + w * tz + (x * ty - y * tx)


def stamp(msg):
    return msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9


class VoGate(Node):
    def __init__(self):
        super().__init__("vo_gate")
        self.rates = collections.deque()  # (stamp, |base_link yaw rate|)
        self.imu_rot = None
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        self.pub = self.create_publisher(Odometry, "/vo_gated", 10)
        self.create_subscription(Imu, "/imu/data", self.on_imu, 200)
        self.create_subscription(Odometry, "/vo", self.on_vo, 10)
        self.last_move = float("-inf")  # time of the last non-zero /cmd_vel
        self.create_subscription(Twist, "/cmd_vel", self.on_cmd, 10)

    def on_cmd(self, msg):
        if msg.linear.x or msg.linear.y or msg.angular.z:
            self.last_move = self.get_clock().now().nanoseconds * 1e-9

    def on_imu(self, msg):
        if self.imu_rot is None:
            try:
                r = self.tf_buffer.lookup_transform(
                    "base_link", msg.header.frame_id, Time()
                ).transform.rotation
                self.imu_rot = (r.x, r.y, r.z, r.w)
            except tf2_ros.TransformException:
                return
        av = msg.angular_velocity
        t = stamp(msg)
        self.rates.append((t, abs(rotate_z(self.imu_rot, (av.x, av.y, av.z)))))
        while self.rates and self.rates[0][0] < t - 3.0:
            self.rates.popleft()

    def on_vo(self, msg):
        t = stamp(msg)
        turning = self.imu_rot is None or any(
            r > TURN_RATE for s, r in self.rates if t - WINDOW <= s <= t + WINDOW
        )
        cov = list(msg.twist.covariance)
        v = msg.twist.twist.linear
        if t - self.last_move > STILL_AFTER:  # VO stamp is the camera frame's time
            v.x = v.y = 0.0
            cov[0] = cov[7] = STILL_VAR
        elif turning or (v.x**2 + v.y**2) ** 0.5 > MAX_SPEED:
            cov[0] = cov[7] = DISTRUST_VAR  # vx, vy
        else:
            cov[0], cov[7] = max(cov[0], MIN_VAR), max(cov[7], MIN_VAR)
        msg.twist.covariance = cov
        self.pub.publish(msg)


def main():
    rclpy.init()
    rclpy.spin(VoGate())


if __name__ == "__main__":
    main()
