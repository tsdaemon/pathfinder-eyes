#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Empty
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus
from rosidl_runtime_py.utilities import get_message
from ros2node.api import get_node_names

import time


class WatchdogNode(Node):
    def __init__(self):
        super().__init__("watchdog")

        # Declare parameters
        self.declare_parameter("name", "")
        self.declare_parameter("heartbeat_topic", "")
        self.declare_parameter("restart_topics", [""])
        self.declare_parameter("max_restarts", 3)
        self.declare_parameter("heartbeat_timeout", 5.0)  # seconds
        self.declare_parameter("poll_interval", 1.0)  # seconds
        # Get parameters
        self.heartbeat_topic = (
            self.get_parameter("heartbeat_topic").get_parameter_value().string_value
        )
        if self.heartbeat_topic == "":
            self.get_logger().error("Heartbeat topic is not set")
            return

        self.name = self.get_parameter("name").get_parameter_value().string_value
        self.restart_topics = (
            self.get_parameter("restart_topics")
            .get_parameter_value()
            .string_array_value
        )
        self.max_restarts = (
            self.get_parameter("max_restarts").get_parameter_value().integer_value
        )
        self.heartbeat_timeout = (
            self.get_parameter("heartbeat_timeout").get_parameter_value().double_value
        )
        self.poll_interval = (
            self.get_parameter("poll_interval").get_parameter_value().double_value
        )

        # Initialize state
        self.last_heartbeat = time.time()
        self.restart_count = 0
        self.status = DiagnosticStatus.STALE

        # Create publishers for restart topics
        self.restart_publishers = []
        for topic in self.restart_topics:
            if topic == "":
                continue
            pub = self.create_publisher(Empty, topic, 10)
            self.restart_publishers.append(pub)

        # Create status publisher
        self.status_pub = self.create_publisher(DiagnosticArray, "/diagnostics", 10)

        # Create timer for checking heartbeat
        self.timer = self.create_timer(1.0, self.check_heartbeat)
        self.init_timer = self.create_timer(self.poll_interval, self.init_subscription)

    def init_subscription(self):
        self.get_logger().info(f"Looking for heartbeat topic {self.heartbeat_topic}")
        topic_list = self.get_topic_names_and_types()
        topic_type = None

        for name, types in topic_list:
            if name == self.heartbeat_topic and types:
                topic_type = types[0]
                break
        else:
            self.get_logger().warning(
                f"Heartbeat topic {self.heartbeat_topic} not found"
            )
            return

        try:
            MsgType = get_message(topic_type)
        except Exception as e:
            self.get_logger().error(f"Failed to load message type '{topic_type}': {e}")
            self.init_timer.cancel()
            self.timer.cancel()
            return

        self.subscription = self.create_subscription(
            MsgType, self.heartbeat_topic, self.heartbeat_callback, 10
        )

        self.get_logger().info(f"Started monitoring {self.heartbeat_topic}")
        self.get_logger().info(f"Restart topics: {self.restart_topics}")
        self.get_logger().info(f"Max restarts: {self.max_restarts}")
        self.get_logger().info(f"Heartbeat timeout: {self.heartbeat_timeout} seconds")
        self.init_timer.cancel()

    def heartbeat_callback(self, msg):
        self.last_heartbeat = time.time()
        if self.status == DiagnosticStatus.WARN:
            self.get_logger().info("Recovered from stale status")

        if self.status == DiagnosticStatus.ERROR:
            self.get_logger().info("Recovered from error status")

        self.status = DiagnosticStatus.OK
        self.restart_count = 0

    def check_heartbeat(self):
        current_time = time.time()
        time_since_heartbeat = current_time - self.last_heartbeat

        if (
            time_since_heartbeat > self.heartbeat_timeout
            and not self.status == DiagnosticStatus.ERROR
        ):
            self.restart_count += 1

            if not self.restart_publishers:
                self.get_logger().error("No restart publishers found")
                self.status = DiagnosticStatus.ERROR
            elif self.restart_count > self.max_restarts:
                self.status = DiagnosticStatus.ERROR
                self.get_logger().error("Declared dead - max restarts reached")
            else:
                self.status = DiagnosticStatus.WARN
                self.get_logger().warning(
                    f"Heartbeat timeout! Restart attempt {self.restart_count}/{self.max_restarts}"
                )
                # Publish restart messages
                for pub in self.restart_publishers:
                    pub.publish(Empty())
                # Reset heartbeat timeout
                self.last_heartbeat = time.time()
                self.get_logger().info("Restart commands sent")

        # Publish current status
        status_msg = DiagnosticArray()
        status_msg.header.stamp = self.get_clock().now().to_msg()
        status = DiagnosticStatus()
        status.name = self.name
        status.level = self.status
        if (
            status.level == DiagnosticStatus.ERROR
            or status.level == DiagnosticStatus.WARN
        ):
            status.message = f"Heartbeat timeout: {time_since_heartbeat} seconds"
        status_msg.status.append(status)
        self.status_pub.publish(status_msg)


def main(args=None):
    rclpy.init(args=args)

    try:
        list_nodes = rclpy.create_node("list_nodes_example")
        available_nodes = get_node_names(node=list_nodes, include_hidden_nodes=True)
        node_names = [name for name, _, _ in available_nodes]
        list_nodes.destroy_node()

        node = WatchdogNode()
        # if there is more than one watchdog node, raise an error
        if node_names.count(node.get_name()) > 1:
            raise Exception(f"{node.get_name()} already started")

        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
