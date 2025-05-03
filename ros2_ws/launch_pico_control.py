from launch import LaunchDescription
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
        ]
    )
