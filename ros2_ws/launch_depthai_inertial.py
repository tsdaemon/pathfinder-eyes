import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription, LaunchService
from launch.actions import IncludeLaunchDescription
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from config import OAKD_INERTIAL_LAUNCH_ARGUMENTS

# This setup requires running camera via powered USB hub. And make sure that its actually powered: powerbank may
# disable power if its idle for a while. So the best appproach:
# 1. Stop RPi
# 2. Disconnect hub and RPi power bank connections
# 3. Connect hub to powerbank
# 4. Connect RPi to powerbank
# Or just use external power supply for RPi


def generate_launch_description():
    return LaunchDescription(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        get_package_share_directory("depthai_ros_driver"),
                        "launch",
                        "camera.launch.py",
                    )
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
                remappings=[("imu/data_raw", "/oakd/imu/data")],
            ),
        ]
    )


if __name__ == "__main__":
    ld = generate_launch_description()
    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
