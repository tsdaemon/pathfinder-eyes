from launch import LaunchDescription
from launch_ros.actions import Node
from launch.launch_service import LaunchService


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="pico_control",
                executable="vel_to_serial",
                name="vel_to_serial_node",
                output="screen",
                parameters=[{"port": "/dev/ttyAMA0"}],
            ),
        ]
    )


if __name__ == "__main__":
    ld = generate_launch_description()
    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
