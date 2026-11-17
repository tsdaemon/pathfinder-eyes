#!/usr/bin/env python3
"""Publish /diagnostics for whether data is actually flowing through the VIO pipeline.

A node can advertise a topic and publish nothing: on 2026-11-17 the OAK-D came up with images
but no IMU after a reset, with no error anywhere - the EKF never published odom -> base_link
and VO aborted every frame. Each stage below gets a "pipeline: ..." status with its rate,
ERROR when silent. Messages are taken raw (not deserialised) to keep the cost low; images are
watched through their camera_info topics.
"""

import rclpy
import tf2_ros
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import CameraInfo, Imu

# (topic, type, warn below Hz). Normal rates: IMU ~75-95, cameras 30, VO 5-11, EKF 20.
TOPICS = [
    ("/oakd/imu/data", Imu, 50.0),
    ("/imu/data", Imu, 50.0),
    ("/oakd/right/camera_info", CameraInfo, 20.0),
    ("/oakd/stereo/camera_info", CameraInfo, 20.0),
    ("/vo", Odometry, 3.0),
    ("/odometry/filtered", Odometry, 15.0),
]
TF_PAIR = ("odom", "base_link")
TF_MAX_AGE = 0.5  # s
PERIOD = 2.0  # s, rate window and publish period


class PipelineMonitor(Node):
    def __init__(self):
        super().__init__("pipeline_monitor")
        self.counts = {t: 0 for t, _, _ in TOPICS}
        for topic, msg_type, _ in TOPICS:
            # Sensor-data QoS (best effort) matches both reliable and best-effort publishers.
            self.create_subscription(
                msg_type,
                topic,
                lambda _m, t=topic: self.counts.__setitem__(t, self.counts[t] + 1),
                qos_profile_sensor_data,
                raw=True,
            )
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        self.pub = self.create_publisher(DiagnosticArray, "/diagnostics", 10)
        self.create_timer(PERIOD, self.report)

    def status(self, name, level, message, values):
        return DiagnosticStatus(
            name=f"pipeline: {name}",
            hardware_id="eyes",
            level=level,
            message=message,
            values=[KeyValue(key=k, value=v) for k, v in values.items()],
        )

    def report(self):
        msg = DiagnosticArray()
        msg.header.stamp = self.get_clock().now().to_msg()
        for topic, _, warn_hz in TOPICS:
            hz = self.counts[topic] / PERIOD
            self.counts[topic] = 0
            if hz == 0:
                level, text = DiagnosticStatus.ERROR, "no messages"
            elif hz < warn_hz:
                level, text = DiagnosticStatus.WARN, f"slow: {hz:.1f} Hz"
            else:
                level, text = DiagnosticStatus.OK, f"{hz:.1f} Hz"
            msg.status.append(self.status(topic, level, text, {"hz": f"{hz:.1f}"}))

        parent, child = TF_PAIR
        try:
            stamp = self.tf_buffer.lookup_transform(parent, child, Time()).header.stamp
            age = (self.get_clock().now() - Time.from_msg(stamp)).nanoseconds * 1e-9
            level = DiagnosticStatus.OK if age < TF_MAX_AGE else DiagnosticStatus.ERROR
            text, values = f"age {age:.2f} s", {"age": f"{age:.2f}"}
        except tf2_ros.TransformException:
            level, text, values = DiagnosticStatus.ERROR, "no transform", {}
        msg.status.append(self.status(f"tf {parent} -> {child}", level, text, values))
        self.pub.publish(msg)


def main():
    rclpy.init()
    rclpy.spin(PipelineMonitor())


if __name__ == "__main__":
    main()
