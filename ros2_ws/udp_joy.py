#!/usr/bin/env python3
"""Receive gamepad state over UDP (from deck/drive.py on the Steam Deck) and publish /joy.

Packets are one JSON object each: {"axes": [8 floats], "buttons": [24 ints]}, laid out like
the 8BitDo in config/teleop_joy.yaml, sent ~50 Hz. UDP rather than TCP so a lost packet is
just replaced by the next one instead of being retransmitted and replayed late.

If packets stop for TIMEOUT, one all-released /joy is published: teleop_twist_joy then sees
the enable button let go and sends a zero cmd_vel (vel_to_serial's own timeout backs this up).
"""

import json
import socket
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy

PORT = 9010
TIMEOUT = 0.3  # s without packets -> release everything
N_AXES, N_BUTTONS = 8, 24
RELEASED_AXES = [0.0] * 4 + [1.0, 1.0] + [0.0] * 2  # triggers read 1.0 when released


class UdpJoy(Node):
    def __init__(self):
        super().__init__("udp_joy")
        self.pub = self.create_publisher(Joy, "/joy", 10)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", PORT))
        self.sock.setblocking(False)
        self.sender = None
        self.last_rx = 0.0
        self.create_timer(0.005, self.poll)
        self.get_logger().info(f"Listening for gamepad packets on UDP {PORT}")

    def publish(self, axes, buttons):
        msg = Joy()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.axes = [float(a) for a in axes]
        msg.buttons = [int(b) for b in buttons]
        self.pub.publish(msg)

    def poll(self):
        latest = None
        while True:  # drain the socket, keep only the newest packet
            try:
                data, addr = self.sock.recvfrom(2048)
            except BlockingIOError:
                break
            try:
                pkt = json.loads(data)
                axes, buttons = pkt["axes"], pkt["buttons"]
                if len(axes) != N_AXES or len(buttons) != N_BUTTONS:
                    raise ValueError(f"expected {N_AXES} axes / {N_BUTTONS} buttons")
            except (ValueError, KeyError, TypeError) as e:
                self.get_logger().warn(
                    f"Bad packet from {addr[0]}: {e}", throttle_duration_sec=5.0
                )
                continue
            latest = (axes, buttons, addr)

        now = time.monotonic()
        if latest is not None:
            axes, buttons, addr = latest
            if self.sender is None:
                self.get_logger().info(f"Gamepad connected from {addr[0]}")
            self.sender, self.last_rx = addr, now
            self.publish(axes, buttons)
        elif self.sender is not None and now - self.last_rx > TIMEOUT:
            self.get_logger().warn(f"Gamepad from {self.sender[0]} timed out")
            self.publish(RELEASED_AXES, [0] * N_BUTTONS)
            self.sender = None


def main():
    rclpy.init()
    rclpy.spin(UdpJoy())


if __name__ == "__main__":
    main()
