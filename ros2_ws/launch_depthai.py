import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription, LaunchService
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from config import OAKD_LAUNCH_ARGUMENTS

# This setup requires running camera via powered USB hub. And make sure that its actually powered: powerbank may
# disable power if its idle for a while. So the best appproach:
# 1. Stop RPi
# 2. Disconnect hub and RPi power bank connections
# 3. Connect hub to powerbank
# 4. Connect RPi to powerbank
# Or just use external power supply for RPi


def generate_launch_description():
    depthai_prefix = get_package_share_directory("depthai_ros_driver")

    return LaunchDescription(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(depthai_prefix, "launch", "camera.launch.py")
                ),
                launch_arguments=OAKD_LAUNCH_ARGUMENTS.items(),
            ),
        ]
    )


if __name__ == "__main__":
    ld = generate_launch_description()
    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
