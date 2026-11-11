#!/usr/bin/env python

from launch import LaunchDescription, LaunchService
from launch.actions import ExecuteProcess
from launch_ros.actions import Node

from config import (
    EKF_ODOM_TOPIC,
    EKF_PARAMS,
    OAKD_NAME,
    ODOM_DROPOUT_MODE,
    RTABMAP_INERTIAL_PARAMS,
    VO_TOPIC,
)


def generate_launch_description():
    remappings = [("imu", "/imu/data")]
    odom_params = RTABMAP_INERTIAL_PARAMS
    slam_params = RTABMAP_INERTIAL_PARAMS
    odom_remappings = remappings
    slam_remappings = remappings
    extra_nodes = []

    if ODOM_DROPOUT_MODE == "ekf_imu":
        # VO stops owning odom -> base_link; the EKF publishes it instead. No null messages
        # when lost, so the EKF coasts on the gyro rather than fusing a zero yaw rate.
        # VO also takes its motion guess from the EKF's odom -> base_link TF (gyro-driven
        # rotation) instead of reading the IMU itself: waiting for "IMU newer than the image"
        # was dropping a large share of frames, and during fast spins the gyro-based guess
        # tells feature matching where to look. VO gets its own odom frame name so it doesn't
        # collide with the EKF's.
        odom_params = [
            p
            | {
                "publish_tf": False,
                "publish_null_when_lost": False,
                "odom_frame_id": "vo_odom",
                "guess_frame_id": "odom",
                "wait_imu_to_init": False,
            }
            for p in RTABMAP_INERTIAL_PARAMS
        ]
        odom_remappings = [("odom", VO_TOPIC)]
        # odom_info is stamped with camera frames and wouldn't sync with EKF output.
        slam_params = [
            p | {"subscribe_odom_info": False} for p in RTABMAP_INERTIAL_PARAMS
        ]
        slam_remappings = remappings + [("odom", EKF_ODOM_TOPIC)]
        extra_nodes.append(
            ExecuteProcess(cmd=["python3", "vo_gate.py"], output="screen")
        )
        extra_nodes.append(
            Node(
                package="robot_localization",
                executable="ekf_node",
                output="screen",
                parameters=EKF_PARAMS,
                remappings=[("odometry/filtered", EKF_ODOM_TOPIC)],
            )
        )
    elif ODOM_DROPOUT_MODE != "new_map":
        raise ValueError(f"Unknown ODOM_DROPOUT_MODE: {ODOM_DROPOUT_MODE!r}")

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
                parameters=odom_params,
                remappings=odom_remappings,
            ),
            *extra_nodes,
            # VSLAM
            Node(
                package="rtabmap_slam",
                executable="rtabmap",
                output="screen",
                parameters=slam_params,
                remappings=slam_remappings,
                arguments=["-d"],
            ),
        ]
    )


if __name__ == "__main__":
    ld = generate_launch_description()
    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
