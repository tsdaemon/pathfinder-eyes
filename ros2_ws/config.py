# Constants
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
        "approx_sync": False,
    }
    | RTABMAP_COMMON_PARAMS
]

# oakd
OAKD_INERTIAL_LAUNCH_ARGUMENTS = {
    "depth_aligned": "false",
    "enableRviz": "false",
    "monoResolution": "400p",
}

# supervisor
SUPERVISOR_XMLRPC_URL = "http://localhost:9001/RPC2"
