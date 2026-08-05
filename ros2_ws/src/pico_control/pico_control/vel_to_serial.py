import rclpy
import serial
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus
from geometry_msgs.msg import Twist
from rclpy.node import Node

SEND_PERIOD_S = 0.05  # 20Hz


def _clamp(value, limit):
    if limit <= 0:
        return 0.0
    return max(-1.0, min(1.0, value / limit))


class VelToSerialNode(Node):
    def __init__(self):
        super().__init__("vel_to_serial_node")

        self.declare_parameter("port", "/dev/ttyAMA0")
        self.declare_parameter("baudrate", 115200)
        self.declare_parameter("max_linear_speed", 0.5)  # m/s at vx/vy = 1.0
        self.declare_parameter("max_angular_speed", 1.5)  # rad/s at wz = 1.0
        port = self.get_parameter("port").value
        baudrate = self.get_parameter("baudrate").value
        self.max_linear_speed = self.get_parameter("max_linear_speed").value
        self.max_angular_speed = self.get_parameter("max_angular_speed").value

        self.ser = serial.Serial(port, baudrate=baudrate, timeout=0.1)

        self.vx = 0.0
        self.vy = 0.0
        self.wz = 0.0
        self._last_sent = None

        self.subscription = self.create_subscription(
            Twist, "cmd_vel", self._on_cmd_vel, 10
        )
        self.create_timer(SEND_PERIOD_S, self._send_vel)

        self.diagnostics_pub = self.create_publisher(
            DiagnosticArray, "/diagnostics", 10
        )
        self.create_timer(0.05, self._read_pico_status)

    def _on_cmd_vel(self, msg: Twist):
        self.vx = _clamp(msg.linear.x, self.max_linear_speed)
        self.vy = _clamp(msg.linear.y, self.max_linear_speed)
        self.wz = _clamp(msg.angular.z, self.max_angular_speed)

    def _send_vel(self):
        values = (self.vx, self.vy, self.wz)
        if values == self._last_sent:
            return

        line = "VEL:{:.3f},{:.3f},{:.3f}\n".format(*values)
        self.get_logger().info(f"Sending: {line.strip()}")
        self.ser.write(line.encode())
        self._last_sent = values

    def _read_pico_status(self):
        if self.ser.in_waiting == 0:
            return
        line = self.ser.readline().decode(errors="replace").strip()
        if not line:
            return

        status = DiagnosticStatus()
        status.name = "pico_motor_driver"
        status.hardware_id = "pico"
        if line.startswith("ERR:"):
            status.level = DiagnosticStatus.ERROR
            status.message = line[len("ERR:") :]
        else:
            status.level = DiagnosticStatus.OK
            status.message = line

        msg = DiagnosticArray()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.status.append(status)
        self.diagnostics_pub.publish(msg)


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
