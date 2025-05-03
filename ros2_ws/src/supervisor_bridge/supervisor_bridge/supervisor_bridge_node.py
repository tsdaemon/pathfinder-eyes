#!/usr/bin/env python3

from functools import partial
import rclpy
from rclpy.node import Node
from xmlrpc.client import ServerProxy
from std_msgs.msg import String, Empty
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
        self.declare_parameter("namespace", "supervisor")
        self.namespace = (
            self.get_parameter("namespace").get_parameter_value().string_value
        )

        self.declare_parameter("status_poll_interval", 1.0)
        self.status_poll_interval = (
            self.get_parameter("status_poll_interval")
            .get_parameter_value()
            .double_value
        )

        # Declare and get the config file parameter
        self.declare_parameter("xmlrpc_url", "http://localhost:9001/RPC2")
        xmlrpc_url = self.get_parameter("xmlrpc_url").get_parameter_value().string_value

        self.get_logger().info(f"XML-RPC URL: {xmlrpc_url}")
        self.client = ServerProxy(xmlrpc_url)

        # Init publishers and subscribers
        self.programs = {}
        self.status_publishers = {}
        self.stop_subscribers = {}
        self.start_subscribers = {}
        self.restart_subscribers = {}
        self.diagnostics_publisher = self.create_publisher(
            DiagnosticArray, "/diagnostics", 10
        )

        # Supervisor timers
        self.bridge_initialized = False
        self.supervisor_status_publisher = self.create_publisher(
            String, f"{self.namespace}/status", 10
        )
        self.supervisor_status_timer = self.create_timer(
            1.0, self._check_supervisor_status
        )

    def _check_supervisor_status(self):
        try:
            state = self.client.supervisor.getState()
            if state["statename"] == "RUNNING" and not self.bridge_initialized:
                self.initialize_bridge()
            msg = String()
            msg.data = state["statename"]
            self.supervisor_status_publisher.publish(msg)
        except Exception as e:
            self.get_logger().error(f"Error checking supervisor status: {str(e)}")

    def initialize_bridge(self):
        try:
            self.get_logger().info("Initializing bridge...")
            self.bridge_initialized = True
            self._init_supervisor_resources()
            self.get_logger().info("Bridge initialized")
        except Exception as e:
            self.get_logger().error(f"Error initializing bridge: {str(e)}")
            self.bridge_initialized = False

    def _init_supervisor_resources(self):
        self.programs = {
            program["name"]: program
            for program in self.client.supervisor.getAllProcessInfo()
        }

        for program_name in self.programs:
            self.get_logger().info(f"Initializing program: {program_name}")

            # Create publishers
            self.status_publishers[program_name] = self.create_publisher(
                String, f"{self.namespace}/{program_name}/status", 10
            )

            # Create subscribers
            self.stop_subscribers[program_name] = self.create_subscription(
                Empty,
                f"{self.namespace}/{program_name}/stop",
                partial(self._stop_program, program_name),
                10,
            )
            self.start_subscribers[program_name] = self.create_subscription(
                Empty,
                f"{self.namespace}/{program_name}/start",
                partial(self._start_program, program_name),
                10,
            )
            self.restart_subscribers[program_name] = self.create_subscription(
                Empty,
                f"{self.namespace}/{program_name}/restart",
                partial(self._restart_program, program_name),
                10,
            )

        self.status_timer = self.create_timer(
            self.status_poll_interval, self._poll_status
        )

    def _poll_status(self):
        status_array = DiagnosticArray()
        status_array.header.stamp = self.get_clock().now().to_msg()
        status_array.header.frame_id = "supervisor"
        status_array.status = []

        for program_name in self.programs:
            process_info = self.client.supervisor.getProcessInfo(program_name)
            msg = String()
            msg.data = process_info["statename"]
            status = DiagnosticStatus()
            status.name = f"/{self.namespace}/{program_name}"
            status.level = SUPERVISOR_STATUS_TO_DIAGNOSTIC_STATUS[
                process_info["statename"]
            ]
            if status.level == DiagnosticStatus.ERROR and "exitstatus" in process_info:
                status.message = f"Exit code: {process_info['exitstatus']}"
            else:
                status.message = process_info["description"]
            status_array.status.append(status)

        self.diagnostics_publisher.publish(status_array)

    def _stop_program(self, program_name, msg):
        self.get_logger().info(f"Stopping program: {program_name}")
        self.client.supervisor.stopProcess(program_name)

    def _start_program(self, program_name, msg):
        self.get_logger().info(f"Starting program: {program_name}")
        self.client.supervisor.startProcess(program_name)

    def _restart_program(self, program_name, msg):
        self.get_logger().info(f"Stopping {program_name}...")
        self.client.supervisor.stopProcess(program_name)
        self.get_logger().info(f"Restarting {program_name}...")
        self.client.supervisor.startProcess(program_name)


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
