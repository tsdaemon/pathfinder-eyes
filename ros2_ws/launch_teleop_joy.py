from launch import LaunchDescription
from launch_ros.actions import Node
from launch.launch_service import LaunchService


def generate_launch_description():
    return LaunchDescription(
        [
            # Reads the gamepad paired to the Pi over Bluetooth (8BitDo Ultimate 2 Wireless)
            # and publishes /joy. Picks the controller up when it (re)connects.
            Node(
                package="joy",
                executable="joy_node",
                name="joy_node",
                output="screen",
            ),
            Node(
                package="teleop_twist_joy",
                executable="teleop_node",
                name="teleop_twist_joy_node",
                output="screen",
                parameters=["config/teleop_joy.yaml"],
            ),
        ]
    )


if __name__ == "__main__":
    ld = generate_launch_description()
    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
