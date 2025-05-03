import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription, LaunchService
from launch.actions import (
    IncludeLaunchDescription,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource

from config import OAKD_LAUNCH_ARGUMENTS


def generate_launch_description():
    launch_file = os.path.join(
        get_package_share_directory("depthai_ros_driver"),
        "launch",
        "rgbd_pcl.launch.py",
    )
    return LaunchDescription(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(launch_file),
                launch_arguments=OAKD_LAUNCH_ARGUMENTS,
            ),
        ]
    )


if __name__ == "__main__":
    ld = generate_launch_description()
    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
