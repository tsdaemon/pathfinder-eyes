import rclpy
from ros2node.api import get_node_names


def verify_unique_node(node_name):
    rclpy.init()
    node = rclpy.create_node("list_nodes_example")
    available_nodes = get_node_names(node=node, include_hidden_nodes=False)
    for name, namespace, full_name in available_nodes:
        print(f"Found node {name} in namespace {namespace} (full name: {full_name}")
    node.destroy_node()
    rclpy.shutdown()
