from launch import LaunchDescription, LaunchService
from launch_ros.actions import Node

from config import SUPERVISOR_XMLRPC_URL, SUPERVISOR_NAMESPACE


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="supervisor_bridge",
                executable="supervisor_bridge",
                name="supervisor_bridge",
                output="screen",
                parameters=[
                    {
                        "xmlrpc_url": SUPERVISOR_XMLRPC_URL,
                        "namespace": SUPERVISOR_NAMESPACE,
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
