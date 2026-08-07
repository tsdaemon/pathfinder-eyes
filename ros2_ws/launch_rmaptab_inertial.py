#!/usr/bin/env python

from launch import LaunchDescription, LaunchService
from launch_ros.actions import Node

from config import OAKD_NAME, RTABMAP_INERTIAL_PARAMS


def generate_launch_description():
    remappings = [("imu", "/imu/data")]

    return LaunchDescription(
        [
            # Sync right/depth/camera_info together
            Node(
                package="rtabmap_sync",
                executable="rgbd_sync",
                output="screen",
                parameters=RTABMAP_INERTIAL_PARAMS,
                remappings=[
                    ("rgb/image", "/" + OAKD_NAME + "/right/image_rect"),
                    ("rgb/camera_info", "/" + OAKD_NAME + "/right/camera_info"),
                    ("depth/image", "/" + OAKD_NAME + "/stereo/image_raw"),
                ],
            ),
            # Visual odometry
            Node(
                package="rtabmap_odom",
                executable="rgbd_odometry",
                output="screen",
                parameters=RTABMAP_INERTIAL_PARAMS,
                remappings=remappings,
            ),
            # VSLAM
            Node(
                package="rtabmap_slam",
                executable="rtabmap",
                output="screen",
                parameters=RTABMAP_INERTIAL_PARAMS,
                remappings=remappings,
                arguments=["-d"],
            ),
        ]
    )


if __name__ == "__main__":
    ld = generate_launch_description()
    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
