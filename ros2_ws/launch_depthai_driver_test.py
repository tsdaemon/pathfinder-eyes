#!/usr/bin/env python
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription, LaunchService
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

# One-off test of depthai_ros_driver's IMU handling: i_batch_report_threshold and
# i_max_batch_reports are ROS params here, unlike depthai_examples' stereo_inertial_node
# (the one launch_depthai_inertial.py runs), which hardcodes the equivalent values in C++.
# See docs/notes/2026.08.07.md for why this is worth testing.
#
# Deliberately NOT wired into supervisord - this doesn't touch the working pipeline
# (launch_depthai_inertial.py / launch_rmaptab_inertial.py stay untouched) and a depthai
# device only accepts one pipeline connection at a time, so this can't run alongside the
# `depthai` supervisord program anyway:
#
#   supervisorctl -c supervisord.conf stop depthai rtabmap
#   cd ros2_ws && python launch_depthai_driver_test.py
#   ... test with imu_image_sync_check.py, then Ctrl+C ...
#   supervisorctl -c supervisord.conf start depthai rtabmap


def generate_launch_description():
    depthai_driver_prefix = get_package_share_directory("depthai_ros_driver")

    return LaunchDescription(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(depthai_driver_prefix, "launch", "camera.launch.py")
                ),
                launch_arguments={
                    "name": "oakd_test",
                    "params_file": "config/oakd_driver_test.yaml",
                }.items(),
            ),
        ]
    )


if __name__ == "__main__":
    ld = generate_launch_description()
    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
