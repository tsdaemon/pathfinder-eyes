import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription, LaunchService
from launch.actions import IncludeLaunchDescription, Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from config import OAKD_INERTIAL_LAUNCH_ARGUMENTS


def generate_launch_description():
    return LaunchDescription(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [
                        os.path.join(
                            get_package_share_directory("depthai_examples"), "launch"
                        ),
                        "/stereo_inertial_node.launch.py",
                    ]
                ),
                launch_arguments=OAKD_INERTIAL_LAUNCH_ARGUMENTS.items(),
            ),
            # Compute quaternion of the IMU
            Node(
                package="imu_filter_madgwick",
                executable="imu_filter_madgwick_node",
                output="screen",
                parameters=[
                    {"use_mag": False, "world_frame": "enu", "publish_tf": False}
                ],
                remappings=[("imu/data_raw", "/imu")],
            ),
        ]
    )


if __name__ == "__main__":
    ld = generate_launch_description()
    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
