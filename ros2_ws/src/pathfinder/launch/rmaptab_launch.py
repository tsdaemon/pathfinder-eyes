from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch_ros.substitutions import FindPackageShare
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import yaml

RESIZE_SCALE = 1.0

def generate_launch_description():
    launch_arguments = {
        'namespace': 'stereo_resized',
        'approximate_sync': 'True',
        'use_color': 'False',
    }
    # Load disparity config
    with open(get_package_share_directory('pathfinder') + '/disparity_config.yaml', 'r') as f:
        disparity_config = yaml.safe_load(f)
    launch_arguments.update(disparity_config)
    
    stereo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            FindPackageShare('stereo_image_proc'),
            '/launch/stereo_image_proc.launch.py'
        ]),
        launch_arguments=launch_arguments.items()
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
                'approximate_sync': 'True',
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
                'scale_width': RESIZE_SCALE,
                'approximate_sync': 'True',
            }]
        ),

        stereo_launch,

        # Node(
        #     package='rtabmap_odom',
        #     executable='stereo_odometry',
        #     name='rtabmap',
        #     output='screen',
        #     parameters=[{
        #         'frame_id': 'camera_1_optical_frame',
        #         'subscribe_depth': False,
        #         'subscribe_odom_info':True,
        #         'subscribe_stereo': True,
        #         'approx_sync': True,
        #         'approx_sync_max_interval': 0.03,
        #     }],
        #     remappings=[
        #         ('left/image_rect', '/stereo_resized/left/image_rect'),
        #         ('right/image_rect', '/stereo_resized/right/image_rect'),
        #         ('left/camera_info', '/stereo_resized/left/camera_info'),
        #         ('right/camera_info', '/stereo_resized/right/camera_info'),
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