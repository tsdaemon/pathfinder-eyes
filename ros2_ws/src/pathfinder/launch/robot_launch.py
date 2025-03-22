from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='pathfinder',
            executable='imu_node',
            name='imu_node',
            output='screen'
        ),
        Node(
            package='foxglove_bridge',
            executable='foxglove_bridge',
            name='foxglove_bridge',
            output='screen',
            parameters=[{
                "port": 8765  # default websocket port for Foxglove
            }]
        ),

        # EKF node (robot_localization)
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[
                {
                    'use_sim_time': False,
                    'odom0': '/imu/data_raw',
                    'imu0': '/imu/data_raw',
                    'imu0_config': [
                        False, False, False,     # position
                        False, False, False,     # orientation
                        False, False, False,     # linear velocity
                        True, True, True,        # angular velocity (gyro)
                        True, True, True         # linear acceleration
                    ],
                    'imu0_differential': False,
                    'imu0_remove_gravitational_acceleration': True,
                    'publish_tf': True,
                    'map_frame': 'map',
                    'odom_frame': 'odom',
                    'base_link_frame': 'base_link',
                    'world_frame': 'odom'
                }
            ]
        ),

        # Static transform publisher for IMU to base_link
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'imu_link'],
        )
    ])