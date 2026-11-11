#!/usr/bin/env python3
"""Relay /vo -> /vo_gated for the EKF, distrusting VO's linear velocity during fast turns.

During an in-place spin (~200 deg/s - mecanum rotation only works near full speed) VO
reports 0.1-0.7 m/s of bogus forward/sideways velocity with ~1 cm/s confidence: the camera
sits 9cm off the rotation center and turns 20-40 deg between processed frames. Fusing that
walked the EKF 27-38cm off per two in-place turns (2026-11-11).

So: when the gyro (base_link yaw rate) exceeds TURN_RATE anywhere within WINDOW of the VO
message's stamp, the vx/vy twist covariance is inflated to DISTRUST_VAR, which makes the EKF
effectively ignore it. Everything else passes through unchanged. See docs/depthai.md.
"""
import collections

import rclpy
import tf2_ros
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.time import Time
from sensor_msgs.msg import Imu

TURN_RATE = 0.8  # rad/s
WINDOW = (
    0.3  # s, each side of the VO stamp (VO is ~0.2s behind; spin-up/down transients)
)
DISTRUST_VAR = 100.0  # (m/s)^2


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
        if turning:
            cov = list(msg.twist.covariance)
            cov[0] = cov[7] = DISTRUST_VAR  # vx, vy
            msg.twist.covariance = cov
        self.pub.publish(msg)


def main():
    rclpy.init()
    rclpy.spin(VoGate())


if __name__ == "__main__":
    main()
