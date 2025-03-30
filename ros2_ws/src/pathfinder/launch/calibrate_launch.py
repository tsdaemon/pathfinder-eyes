from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # IMU node
        Node(
            package='pathfinder',
            executable='imu_node',
            name='imu_node',
            output='screen'
        ),

        # Left camera node
        Node(
            package='pathfinder',
            executable='camera_node',
            name='camera_left',
            output='screen',
            parameters=[{
                'camera_id': 0,
                'image_topic': 'stereo/left/image_raw',
                'camera_info_topic': 'stereo/left/camera_info'
            }]
        ),

        # Right camera node  
        Node(
            package='pathfinder',
            executable='camera_node',
            name='camera_right',
            output='screen',
            parameters=[{
                'camera_id': 1,
                'image_topic': 'stereo/right/image_raw',
                'camera_info_topic': 'stereo/right/camera_info'
            }]
        ),

        # Foxglove bridge node
        Node(
            package='foxglove_bridge',
            executable='foxglove_bridge',
            name='foxglove_bridge',
            output='screen',
            parameters=[{
                "port": 8765  # default websocket port for Foxglove
            }]
        ),
    ])