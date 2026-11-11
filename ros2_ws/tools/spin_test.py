#!/usr/bin/env python3
"""Spin the robot in place and report how well each heading source kept up.

Spins at --speed (wz in [-1, 1], scaled by vel_to_serial's max_angular_speed) until the
bias-compensated gyro has counted --turns full turns, or --timeout seconds pass. Then stops,
waits --settle seconds, and prints how far the robot turned according to the gyro, the EKF
(/odometry/filtered) and VO alone (/vo), plus VO dropouts (>0.3s without a /vo message).

Always sends stop commands on exit, including on Ctrl-C or errors: the Pico has no
silence-based auto-stop, it keeps doing the last command it got.

    cd ros2_ws && source install/setup.bash && python3 tools/spin_test.py --turns 2
"""
import argparse
import math
import time

import rclpy
import tf2_ros
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.time import Time
from sensor_msgs.msg import Imu

MAX_ANGULAR_SPEED = 1.5  # must match vel_to_serial's max_angular_speed


def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def rotate(q, v):
    x, y, z, w = q
    vx, vy, vz = v
    tx, ty, tz = 2 * (y * vz - z * vy), 2 * (z * vx - x * vz), 2 * (x * vy - y * vx)
    return (
        vx + w * tx + (y * tz - z * ty),
        vy + w * ty + (z * tx - x * tz),
        vz + w * tz + (x * ty - y * tx),
    )


class Unwrapper:
    def __init__(self):
        self.last = None
        self.total = 0.0

    def update(self, yaw):
        if self.last is not None:
            self.total += (yaw - self.last + math.pi) % (2 * math.pi) - math.pi
        self.last = yaw


class SpinTest(Node):
    def __init__(self):
        super().__init__("spin_test")
        self.pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.ekf = Unwrapper()
        self.vo = Unwrapper()
        self.gyro = 0.0
        self.gyro_t = None
        self.vo_t = None
        self.vo_gaps = 0
        self.imu_rot = None
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        self.ekf_xy = None
        self.create_subscription(Odometry, "/odometry/filtered", self.on_ekf, 10)
        self.create_subscription(Odometry, "/vo", self.on_vo, 10)
        self.create_subscription(Imu, "/imu/data", self.on_imu, 200)

    def on_ekf(self, msg):
        self.ekf.update(yaw_of(msg.pose.pose.orientation))
        self.ekf_xy = (msg.pose.pose.position.x, msg.pose.pose.position.y)

    def on_vo(self, msg):
        now = time.monotonic()
        if self.vo_t is not None and now - self.vo_t > 0.3:
            self.vo_gaps += 1
        self.vo_t = now
        self.vo.update(yaw_of(msg.pose.pose.orientation))

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
        if self.gyro_t is not None and 0 < t - self.gyro_t < 0.5:
            self.gyro += wz * (t - self.gyro_t)
        self.gyro_t = t

    def send(self, wz):
        msg = Twist()
        msg.angular.z = wz
        self.pub.publish(msg)

    def stop(self):
        for _ in range(10):
            self.send(0.0)
            time.sleep(0.05)

    def spin_for(self, seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            rclpy.spin_once(self, timeout_sec=0.02)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--turns", type=float, default=2.0)
    p.add_argument("--speed", type=float, default=1.0, help="wz in [-1, 1]")
    p.add_argument("--timeout", type=float, default=40.0)
    p.add_argument("--settle", type=float, default=3.0)
    a = p.parse_args()

    rclpy.init()
    n = SpinTest()
    try:
        deadline = time.monotonic() + 10.0  # wait for static TF + first IMU messages
        while n.imu_rot is None and time.monotonic() < deadline:
            n.spin_for(0.2)
        n.spin_for(1.0)
        if n.imu_rot is None:
            raise SystemExit("no IMU / TF yet - is the stack running?")
        n.gyro = 0.0
        n.ekf.total = n.vo.total = 0.0
        n.vo_gaps = 0
        xy0 = n.ekf_xy
        target = a.turns * 2 * math.pi
        wz = max(-1.0, min(1.0, a.speed)) * MAX_ANGULAR_SPEED
        start = time.monotonic()
        while abs(n.gyro) < target and time.monotonic() - start < a.timeout:
            n.send(wz)
            n.spin_for(0.05)
        spin_time = time.monotonic() - start
        n.stop()
        n.spin_for(a.settle)
        g, e, v = (math.degrees(x) for x in (n.gyro, n.ekf.total, n.vo.total))
        print(
            f"spin {spin_time:.1f}s ({g / spin_time if spin_time else 0:.0f} deg/s by gyro)"
        )
        print(
            f"gyro {g:8.1f} deg | EKF {e:8.1f} deg (err {e - g:+.1f}) | "
            f"VO {v:8.1f} deg (err {v - g:+.1f}) | VO gaps {n.vo_gaps}"
        )

        def wrapped(
            x
        ):  # end-heading error, immune to unwrap aliasing from output stalls
            return (x + 180) % 360 - 180

        print(
            f"end-heading error vs gyro: EKF {wrapped(e - g):+.1f} deg | "
            f"VO {wrapped(v - g):+.1f} deg"
        )
        if xy0 and n.ekf_xy:
            moved = math.hypot(n.ekf_xy[0] - xy0[0], n.ekf_xy[1] - xy0[1])
            print(
                f"EKF position moved {moved * 100:.1f} cm (in-place spin: should be ~0)"
            )
    finally:
        n.stop()
        n.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
