from launch import LaunchDescription, LaunchService
from launch_ros.actions import Node

from config import SUPERVISOR_XMLRPC_URL, SUPERVISOR_NAMESPACE


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="supervisord_bridge",
                executable="supervisord_bridge",
                name="supervisord_bridge",
                output="screen",
                namespace=SUPERVISOR_NAMESPACE,
                parameters=[
                    {
                        "xmlrpc_url": SUPERVISOR_XMLRPC_URL,
                    }
                ],
            ),
            Node(
                package="supervisord_bridge",
                executable="watchdog",
                name="watchdog_depthai",
                namespace=SUPERVISOR_NAMESPACE,
                output="screen",
                parameters=[
                    {
                        "program_name": "depthai",
                        "heartbeat_topic": "/stereo/camera_info",
                        "heartbeat_timeout": 10.0,
                    }
                ],
            ),
        ]
    )


if __name__ == "__main__":
    ld = generate_launch_description()
    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
