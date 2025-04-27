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
                'camera_id': 1,
                'image_topic': 'stereo/left/image_raw',
                'camera_info_topic': 'stereo/left/camera_info'
            }]
        ),
        # Left camera image_proc throttle
        Node(
            package='topic_tools',
            executable='throttle',
            name='left_camera_throttle',
            output='screen',
            arguments=['messages', '/stereo/left/image_raw', '2.0'],
        ),

        # Right camera node  
        Node(
            package='pathfinder',
            executable='camera_node',
            name='camera_right',
            output='screen',
            parameters=[{
                'camera_id': 0,
                'image_topic': 'stereo/right/image_raw',
                'camera_info_topic': 'stereo/right/camera_info'
            }]
        ),

        # Right camera image_proc throttle
        Node(
            package='topic_tools',
            executable='throttle',
            name='right_camera_throttle',
            output='screen',
            arguments=['messages', '/stereo/right/image_raw', '2.0'],
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