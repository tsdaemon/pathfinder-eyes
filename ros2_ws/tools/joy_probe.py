#!/usr/bin/env python3
"""Print which /joy axis or button changes, to map a controller for config/teleop_joy.yaml.

Needs joy_node running (it's part of the teleop_joy program). Move one control at a time.

    cd ros2_ws && source install/setup.bash && python3 tools/joy_probe.py
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy


class JoyProbe(Node):
    def __init__(self):
        super().__init__("joy_probe")
        self.last = None
        self.create_subscription(Joy, "/joy", self.on_joy, 10)

    def on_joy(self, msg):
        if self.last is not None:
            for i, (a, b) in enumerate(zip(self.last.axes, msg.axes)):
                if abs(a - b) > 0.5:
                    print(f"axis {i}: {a:+.2f} -> {b:+.2f}", flush=True)
            for i, (a, b) in enumerate(zip(self.last.buttons, msg.buttons)):
                if a != b:
                    print(f"button {i}: {'pressed' if b else 'released'}", flush=True)
        if (
            self.last is None
            or any(abs(a - b) > 0.5 for a, b in zip(self.last.axes, msg.axes))
            or self.last.buttons != msg.buttons
        ):
            self.last = msg


def main():
    rclpy.init()
    rclpy.spin(JoyProbe())


if __name__ == "__main__":
    main()
