#!/usr/bin/env python3
"""Live heading check: prints how far the robot has turned since the script started,
according to the EKF (/odometry/filtered), visual odometry alone (/vo), and the raw gyro
alone (/imu/data angular velocity, rotated into base_link and integrated).

Spin the robot a known amount in place (e.g. one full turn = 360 deg) and compare.
VO 'gaps' counts how many times VO stopped publishing for >0.3s (tracking lost).

    cd ros2_ws && source install/setup.bash && python3 tools/yaw_monitor.py
"""
import math

import rclpy
import tf2_ros
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.time import Time
from sensor_msgs.msg import Imu


def rotate(q, v):
    # Rotate vector v by quaternion q (x, y, z, w).
    x, y, z, w = q
    vx, vy, vz = v
    tx = 2 * (y * vz - z * vy)
    ty = 2 * (z * vx - x * vz)
    tz = 2 * (x * vy - y * vx)
    return (
        vx + w * tx + (y * tz - z * ty),
        vy + w * ty + (z * tx - x * tz),
        vz + w * tz + (x * ty - y * tx),
    )


def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


class Unwrapper:
    def __init__(self):
        self.start = self.last = None
        self.total = 0.0

    def update(self, yaw):
        if self.last is None:
            self.start = self.last = yaw
            return
        d = yaw - self.last
        d = (d + math.pi) % (2 * math.pi) - math.pi
        self.total += d
        self.last = yaw


class YawMonitor(Node):
    def __init__(self):
        super().__init__("yaw_monitor")
        self.ekf = Unwrapper()
        self.vo = Unwrapper()
        self.vo_last_t = None
        self.vo_gaps = 0
        self.gyro_total = 0.0
        self.gyro_last_t = None
        self.imu_rot = (
            None  # base_link <- imu frame rotation, looked up once (it's static)
        )
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        self.create_subscription(Odometry, "/odometry/filtered", self.on_ekf, 10)
        self.create_subscription(Odometry, "/vo", self.on_vo, 10)
        self.create_subscription(Imu, "/imu/data", self.on_imu, 200)
        self.create_timer(0.5, self.report)

    def on_imu(self, msg):
        if self.imu_rot is None:
            try:
                r = self.tf_buffer.lookup_transform(
                    "base_link", msg.header.frame_id, Time()
                ).transform.rotation
                self.imu_rot = (r.x, r.y, r.z, r.w)
            except tf2_ros.TransformException:
                return
        t = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        av = msg.angular_velocity
        wz = rotate(self.imu_rot, (av.x, av.y, av.z))[2]
        if self.gyro_last_t is not None and 0 < t - self.gyro_last_t < 0.5:
            self.gyro_total += wz * (t - self.gyro_last_t)
        self.gyro_last_t = t

    def on_ekf(self, msg):
        self.ekf.update(yaw_of(msg.pose.pose.orientation))

    def on_vo(self, msg):
        now = self.get_clock().now().nanoseconds * 1e-9
        if self.vo_last_t is not None and now - self.vo_last_t > 0.3:
            self.vo_gaps += 1
        self.vo_last_t = now
        self.vo.update(yaw_of(msg.pose.pose.orientation))

    def report(self):
        print(
            f"EKF turned {math.degrees(self.ekf.total):8.1f} deg | "
            f"VO turned {math.degrees(self.vo.total):8.1f} deg | "
            f"gyro turned {math.degrees(self.gyro_total):8.1f} deg | VO gaps {self.vo_gaps}",
            flush=True,
        )


def main():
    rclpy.init()
    rclpy.spin(YawMonitor())


if __name__ == "__main__":
    main()
