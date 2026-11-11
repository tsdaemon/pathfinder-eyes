# Constants
OAKD_NAME = "oakd"
SUPERVISOR_NAMESPACE = "supervisor"

# rtabmap
RTABMAP_COMMON_PARAMS = {
    "frame_id": "base_link",
    "odom_frame_id": "odom",
    "map_frame_id": "map",
    "publish_tf": True,
    "Odom/ResetCountdown": "1",
    "Rtabmap/StartNewMapOnLoopClosure": "true",
    "RGBD/ForceOdom3DoF": "false",
    # "Reg/Force3DoF": "true",
    # "Optimizer/Slam2D": "true",
    "wait_imu_to_init": True,
}

RTABMAP_INERTIAL_PARAMS = [
    {
        "subscribe_rgbd": True,
        "subscribe_odom_info": True,
        # depthai_ros_driver's right/image_rect, right/camera_info and stereo/image_raw come
        # from separate composable nodes (rectify, stereo depth) rather than one node like
        # stereo_inertial_node did, so their timestamps don't line up exactly even though each
        # stream is individually healthy - exact sync (False) never fires. Matches the
        # approx_sync=True the old depthai_ros_driver-based RTAB-Map config used, before it
        # was dropped for being too heavy (see docs/depthai.md).
        "approx_sync": True,
    }
    | RTABMAP_COMMON_PARAMS
]

# oakd
# Switched from depthai_examples' stereo_inertial_node to depthai_ros_driver: the former
# hardcodes IMU batching in C++ (batchReportThreshold=5, maxBatchReports=20), which produces
# a persistent ~100-150ms IMU-behind-camera-frames lag (device-side XLink/VPU contention -
# see docs/notes/2026.08.07.md). depthai_ros_driver exposes the same knobs as ROS params
# (config/oakd.yaml), tuned there to a small negative (healthy) gap instead.
OAKD_INERTIAL_LAUNCH_ARGUMENTS = {
    "name": OAKD_NAME,
    "params_file": "config/oakd.yaml",
    "imu_from_descr": "true",
    "publish_tf_from_calibration": "true",
}

# supervisor
SUPERVISOR_XMLRPC_URL = "http://localhost:9001/RPC2"
