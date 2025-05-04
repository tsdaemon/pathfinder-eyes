#!/usr/bin/env python

from launch import LaunchDescription, LaunchService
from launch_ros.actions import LoadComposableNodes
from launch_ros.descriptions import ComposableNode

from config import RTABMAP_PARAMS, RTABMAP_REMAPPINGS, OAKD_NAME


def generate_launch_description():
    return LaunchDescription(
        [
            LoadComposableNodes(
                target_container=OAKD_NAME + "_container",
                composable_node_descriptions=[
                    ComposableNode(
                        package="rtabmap_odom",
                        plugin="rtabmap_odom::RGBDOdometry",
                        name="rgbd_odometry",
                        parameters=RTABMAP_PARAMS,
                        remappings=RTABMAP_REMAPPINGS,
                    ),
                ],
            ),
            LoadComposableNodes(
                target_container=OAKD_NAME + "_container",
                composable_node_descriptions=[
                    ComposableNode(
                        package="rtabmap_slam",
                        plugin="rtabmap_slam::CoreWrapper",
                        name="rtabmap",
                        parameters=RTABMAP_PARAMS,
                        remappings=RTABMAP_REMAPPINGS,
                    ),
                ],
            ),
        ]
    )


if __name__ == "__main__":
    ld = generate_launch_description()
    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
