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
                'image_topic': '/stereo/left/image_raw',
                'camera_info_topic': '/stereo/left/camera_info',
                'camera_info_file': 'camera/left.yaml'
            }]
        ),
        
        # Left camera rectification
        Node(
            package='image_proc',
            executable='rectify_node',
            name='rectify_left',
            remappings=[
                ('image', '/stereo/left/image_raw'),
                ('camera_info', '/stereo/left/camera_info'),
                ('image_rect', '/stereo/left/image_rect')
            ]
        ),
        
        # Right camera node  
        Node(
            package='pathfinder',
            executable='camera_node',
            name='camera_right',
            output='screen',
            parameters=[{
                'camera_id': 1,
                'image_topic': '/stereo/right/image_raw',
                'camera_info_topic': '/stereo/right/camera_info',
                'camera_info_file': 'camera/right.yaml'
            }]
        ),
        
        # Right camera rectification
        Node(
            package='image_proc',
            executable='rectify_node',
            name='rectify_right',
            remappings=[
                ('image', '/stereo/right/image_raw'),
                ('camera_info', '/stereo/right/camera_info'),
                ('image_rect', '/stereo/right/image_rect')
            ]
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