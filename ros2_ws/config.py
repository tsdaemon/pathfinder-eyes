# Constants
CAMERA_FRAME = "oak-d-base-frame"
OAKD_NAME = "oakd"
SUPERVISOR_NAMESPACE = "supervisor"

# rtabmap
RTABMAP_COMMON_PARAMS = {
    "frame_id": CAMERA_FRAME,
    "odom_frame_id": "odom",
    "map_frame_id": "map",
    "publish_tf": True,
    "Vis/CorType": "1",
    "Vis/MaxFeatures": "500",
    "Odom/ResetCountdown": "1",
    "Rtabmap/StartNewMapOnLoopClosure": "true",
    "Mem/IncrementalMemory": "false",
    "RGBD/ForceOdom3DoF": "false",
    "Reg/Force3DoF": "false",
    "wait_imu_to_init": True,
}

RTABMAP_PARAMS = [
    {
        "subscribe_rgb": True,
        "subscribe_depth": True,
        "subscribe_odom_info": True,
        "approx_sync": True,
    }
    | RTABMAP_COMMON_PARAMS
]
RTABMAP_REMAPPINGS = [
    ("rgb/image", OAKD_NAME + "/rgb/image_rect"),
    ("rgb/camera_info", OAKD_NAME + "/rgb/camera_info"),
    ("depth/image", OAKD_NAME + "/stereo/image_raw"),
    ("imu", OAKD_NAME + "/imu/data"),
]

RTABMAP_INERTIAL_PARAMS = [
    {
        "subscribe_rgbd": True,
        "subscribe_odom_info": True,
        "approx_sync": False,
    }
    | RTABMAP_COMMON_PARAMS
]

# oakd
OAKD_LAUNCH_ARGUMENTS = {
    "name": OAKD_NAME,
    "imu_from_descr": "true",
    "params_file": "config/oakd.yaml",
}

OAKD_INERTIAL_LAUNCH_ARGUMENTS = {
    "depth_aligned": "false",
    "enableRviz": "false",
    "monoResolution": "400p",
    "params_file": "oakd.yaml",
}

# supervisor
SUPERVISOR_XMLRPC_URL = "http://localhost:9001/RPC2"
