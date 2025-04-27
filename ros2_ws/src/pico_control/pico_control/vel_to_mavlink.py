import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial
from pymavlink.dialects.v20 import common as mavlink
from rclpy.exceptions import ParameterNotDeclaredException


class VelToMavlinkNode(Node):
    def __init__(self):
        super().__init__("vel_to_mavlink_node")

        # Declare parameters
        self.declare_parameter("port", "/dev/ttyAMA0")

        try:
            self.port = self.get_parameter("port").value
        except ParameterNotDeclaredException as e:
            self.get_logger().warn(f"Parameter not set: {str(e)}")
            self.port = "/dev/ttyAMA0"

        # Open UART port
        self.ser = serial.Serial(self.port, baudrate=115200, timeout=0.1)

        # MAVLink setup
        self.mav = mavlink.MAVLink(self.ser)
        self.mav.srcSystem = 1
        self.mav.srcComponent = 1

        # Subscribe to cmd_vel topic
        self.subscription = self.create_subscription(
            Twist, "cmd_vel", self.listener_callback, 10
        )

    def listener_callback(self, msg):
        direction = 5  # Default: stop

        if msg.linear.x > 0.1:
            direction = 1  # Forward
        elif msg.linear.x < -0.1:
            direction = 2  # Backward
        elif msg.angular.z > 0.1:
            direction = 3  # Turn Left
        elif msg.angular.z < -0.1:
            direction = 4  # Turn Right

        # Create a real MAVLink command_long message
        mav_msg = mavlink.MAVLink_command_long_message(
            target_system=1,
            target_component=1,
            command=200,
            confirmation=0,
            param1=direction,
            param2=0,
            param3=0,
            param4=0,
            param5=0,
            param6=0,
            param7=0,
        )

        # Send using full packet
        packed_msg = self.mav.finalize_message(
            mav_msg, force_mavlink1=False, not_zero_fill=True
        )
        self.ser.write(packed_msg)
        self.get_logger().info(f"Sent direction {direction} via UART")


def main(args=None):
    rclpy.init(args=args)
    node = VelToMavlinkNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
