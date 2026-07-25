import time

import rclpy
import serial
from geometry_msgs.msg import Twist
from rclpy.node import Node

DEADZONE = 0.1
COMMAND_TIMEOUT_S = 0.5


class VelToSerialNode(Node):
    def __init__(self):
        super().__init__("vel_to_serial_node")

        self.declare_parameter("port", "/dev/ttyAMA0")
        self.declare_parameter("baudrate", 115200)
        port = self.get_parameter("port").value
        baudrate = self.get_parameter("baudrate").value

        self.ser = serial.Serial(port, baudrate=baudrate, timeout=0.1)

        self.last_command = None
        self.last_msg_time = time.monotonic()

        self.subscription = self.create_subscription(
            Twist, "cmd_vel", self._on_cmd_vel, 10
        )
        self.create_timer(0.1, self._check_timeout)

    def _on_cmd_vel(self, msg: Twist):
        self.last_msg_time = time.monotonic()
        self._send(self._to_command(msg))

    def _check_timeout(self):
        if time.monotonic() - self.last_msg_time > COMMAND_TIMEOUT_S:
            self._send("STOP")

    @staticmethod
    def _to_command(msg: Twist) -> str:
        vx, vy, wz = msg.linear.x, msg.linear.y, msg.angular.z

        if abs(wz) > DEADZONE and abs(wz) >= max(abs(vx), abs(vy)):
            return "LEFT" if wz > 0 else "RIGHT"
        if abs(vx) < DEADZONE and abs(vy) < DEADZONE:
            return "STOP"
        if abs(vx) >= abs(vy):
            return "FWD" if vx > 0 else "BACK"
        return "STRAFE_L" if vy > 0 else "STRAFE_R"

    def _send(self, command: str):
        if command == self.last_command:
            return
        self.last_command = command
        self.ser.write((command + "\n").encode())
        self.get_logger().info(f"Sent: {command}")


def main(args=None):
    rclpy.init(args=args)
    node = VelToSerialNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
