#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from xmlrpc.client import ServerProxy
from std_msgs.msg import String
from diagnostic_msgs.msg import DiagnosticStatus, DiagnosticArray

SUPERVISOR_STATUS_TO_DIAGNOSTIC_STATUS = {
    "STOPPED": DiagnosticStatus.ERROR,  # (0) Process stopped due to stop request or never started
    "STARTING": DiagnosticStatus.WARN,  # (10) Process is starting due to start request
    "RUNNING": DiagnosticStatus.OK,  # (20) Process is running
    "BACKOFF": DiagnosticStatus.ERROR,  # (30) Process started but exited too quickly
    "STOPPING": DiagnosticStatus.WARN,  # (40) Process is stopping due to stop request
    "EXITED": DiagnosticStatus.ERROR,  # (100) Process exited from RUNNING state
    "FATAL": DiagnosticStatus.ERROR,  # (200) Process could not be started successfully
    "UNKNOWN": DiagnosticStatus.WARN,  # (1000) Process is in an unknown state
}


class SupervisorBridgeNode(Node):
    def __init__(self):
        super().__init__("supervisor_bridge")

        # Declare parameters
        self.declare_parameter("status_poll_interval", 1.0)
        self.declare_parameter("xmlrpc_url", "http://localhost:9001/RPC2")

        # Get parameters
        self.status_poll_interval = (
            self.get_parameter("status_poll_interval")
            .get_parameter_value()
            .double_value
        )
        xmlrpc_url = self.get_parameter("xmlrpc_url").get_parameter_value().string_value

        self.get_logger().info(f"XML-RPC URL: {xmlrpc_url}")
        self.client = ServerProxy(xmlrpc_url)

        # Init publishers and subscribers
        self.stop_sub = self.create_subscription(String, "stop", self._stop_program, 10)
        self.start_sub = self.create_subscription(
            String, "start", self._start_program, 10
        )
        self.restart_sub = self.create_subscription(
            String, "restart", self._restart_program, 10
        )
        self.diagnostics_publisher = self.create_publisher(
            DiagnosticArray, "/diagnostics", 10
        )

        # Supervisor timers
        self.bridge_initialized = False
        self.supervisor_status_publisher = self.create_publisher(String, "status", 10)
        self.supervisor_status_timer = self.create_timer(
            1.0, self._check_supervisor_status
        )

    def _check_supervisor_status(self):
        try:
            state = self.client.supervisor.getState()
            if state["statename"] == "RUNNING" and not self.bridge_initialized:
                self.status_timer = self.create_timer(
                    self.status_poll_interval, self._poll_status
                )
            self.supervisor_status_publisher.publish(String(data=state["statename"]))
        except Exception as e:
            self.get_logger().error(f"Error checking supervisor status: {str(e)}")

    def _poll_status(self):
        status_array = DiagnosticArray()
        status_array.header.stamp = self.get_clock().now().to_msg()
        status_array.header.frame_id = "supervisor"
        status_array.status = []

        for process_info in self.client.supervisor.getAllProcessInfo():
            program_name = process_info["name"]

            status = DiagnosticStatus()
            status.name = f"{self.get_namespace()}/{program_name}"
            status.level = SUPERVISOR_STATUS_TO_DIAGNOSTIC_STATUS[
                process_info["statename"]
            ]
            if status.level == DiagnosticStatus.ERROR and "exitstatus" in process_info:
                status.message = f"Exit code: {process_info['exitstatus']}"
            else:
                status.message = process_info["description"]
            status_array.status.append(status)

        self.diagnostics_publisher.publish(status_array)

    def _stop_program(self, msg: String):
        self.get_logger().info(f"Stopping program: {msg.data}")
        self.client.supervisor.stopProcess(msg.data)

    def _start_program(self, msg: String):
        self.get_logger().info(f"Starting program: {msg.data}")
        self.client.supervisor.startProcess(msg.data)

    def _restart_program(self, msg: String):
        self.get_logger().info(f"Stopping {msg.data}...")
        self.client.supervisor.stopProcess(msg.data)
        self.get_logger().info(f"Restarting {msg.data}...")
        self.client.supervisor.startProcess(msg.data)


def main(args=None):
    rclpy.init(args=args)
    node = SupervisorBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
