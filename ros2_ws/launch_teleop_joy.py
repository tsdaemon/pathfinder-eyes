from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node
from launch.launch_service import LaunchService


def generate_launch_description():
    return LaunchDescription(
        [
            # Gamepad state from the Steam Deck over Wi-Fi (deck/drive.py) -> /joy. Replaced
            # the Bluetooth gamepad + joy_node, which lagged and replayed inputs late with the
            # camera's USB 3 traffic next to the Pi's antenna (2026-11-17). Only one /joy
            # source at a time: to use a BT pad instead, swap this for joy_node.
            ExecuteProcess(cmd=["python3", "udp_joy.py"], output="screen"),
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
