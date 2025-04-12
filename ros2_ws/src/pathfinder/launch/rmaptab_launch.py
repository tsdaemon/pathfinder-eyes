from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch_ros.substitutions import FindPackageShare
from launch.launch_description_sources import PythonLaunchDescriptionSource
RESIZE_SCALE = 0.25

def generate_launch_description():
    stereo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            FindPackageShare('stereo_image_proc'),
            '/launch/stereo_image_proc.launch.py'
        ]),
        launch_arguments={
            'namespace': 'stereo_resized',
            'approximate_sync': 'True',
            'use_color': 'False',
        }.items()
    )

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
                'image_topic': '/stereo/left/image_raw',
                'camera_info_topic': '/stereo/left/camera_info',
                'camera_info_file': 'camera/left.yaml'
            }]
        ),
        
        # Right camera node  
        Node(
            package='pathfinder',
            executable='camera_node',
            name='camera_right',
            output='screen',
            parameters=[{
                'camera_id': 0,
                'image_topic': '/stereo/right/image_raw',
                'camera_info_topic': '/stereo/right/camera_info',
                'camera_info_file': 'camera/right.yaml'
            }]
        ),

        # Resize left image
        Node(
            package='image_proc',
            executable='resize_node',
            name='resize_left',
            remappings=[
                ('image/image_raw', '/stereo/left/image_raw'),
                ('image/camera_info', '/stereo/left/camera_info'),
                ('resize/image_raw', '/stereo_resized/left/image_raw'),
                ('resize/camera_info', '/stereo_resized/left/camera_info'),
            ],
            parameters=[{
                'scale_height': RESIZE_SCALE,
                'scale_width': RESIZE_SCALE,
            }],
            output='screen'  # Add output to see any errors or warnings
        ),

        # Resize right image
        Node(
            package='image_proc',
            executable='resize_node',
            name='resize_right',
            remappings=[
                ('image/image_raw', '/stereo/right/image_raw'),
                ('image/camera_info', '/stereo/right/camera_info'),
                ('resize/image_raw', '/stereo_resized/right/image_raw'),
                ('resize/camera_info', '/stereo_resized/right/camera_info'),
            ],
            parameters=[{
                'scale_height': RESIZE_SCALE,
                'scale_width': RESIZE_SCALE
            }]
        ),

        stereo_launch,

        # Node(
        #     package='rtabmap_ros',
        #     executable='rtabmap',
        #     name='rtabmap',
        #     output='screen',
        #     parameters=[{
        #         'frame_id': 'base_link',
        #         'subscribe_depth': False,
        #         'subscribe_rgb': True,
        #         'subscribe_stereo': True,
        #         'approx_sync': True
        #     }],
        #     remappings=[
        #         ('stereo/image_left', '/stereo/left/image_resized'),
        #         ('stereo/image_right', '/stereo/right/image_resized'),
        #         ('stereo/camera_info_left', '/stereo/left/camera_info_resized'),
        #         ('stereo/camera_info_right', '/stereo/right/camera_info_resized'),
        #         ('imu', '/imu/data')
        #     ]
        # ),

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