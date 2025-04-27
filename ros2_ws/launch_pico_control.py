#!/usr/bin/env python

from launch import LaunchDescription, LaunchService
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="pico_control",
                executable="vel_to_mavlink",
                name="vel_to_mavlink",
                output="screen",
                parameters=[{"port": "/dev/ttyAMA0"}],
            ),
            Node(
                package="foxglove_bridge",
                executable="foxglove_bridge",
                name="foxglove_bridge",
                output="screen",
                parameters=[
                    {"port": 8765},  # WebSocket port
                    {"use_compression": False},
                ],
            ),
        ]
    )


if __name__ == "__main__":
    ld = generate_launch_description()
    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
