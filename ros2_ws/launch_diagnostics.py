from launch import LaunchDescription
from launch_ros.actions import Node

aggregation_params_filepath = "config/diagnostics_aggregation.yaml"


def generate_launch_description():
    aggregator = Node(
        package="diagnostic_aggregator",
        executable="aggregator_node",
        output="screen",
        parameters=[aggregation_params_filepath],
    )

    cpu_monitor = Node(
        package="diagnostic_common_diagnostics",
        executable="cpu_monitor.py",
        output="screen",
        parameters=[],
    )

    memory_monitor = Node(
        package="diagnostic_common_diagnostics",
        executable="ram_monitor.py",
        output="screen",
        parameters=[],
    )

    return LaunchDescription(
        [
            aggregator,
            cpu_monitor,
            memory_monitor,
        ]
    )
