# Frames
CAMERA_FRAME = "camera_link"

# Namespace
SUPERVISOR_NAMESPACE = "supervisor"
CAMERA_NAMESPACE = "camera"

# rtabmap
RTABMAP_PARAMS = [
    {
        "frame_id": CAMERA_FRAME,
        "subscribe_rgbd": True,
        "subscribe_odom_info": True,
        "approx_sync": False,
        "wait_imu_to_init": True,
        "Vis/CorType": "1",
        "Vis/MaxFeatures": "500",
        "Odom/ResetCountdown": "1",
        "Odom/Strategy": "1",
        "Rtabmap/StartNewMapOnLoopClosure": "true",
        "Mem/IncrementalMemory": "false",
        "RGBD/ForceOdom3DoF": "false",
    }
]

# oakd
OAKD_LAUNCH_ARGUMENTS = {
    "name": CAMERA_NAMESPACE,
    "parent_frame": CAMERA_FRAME,
    "imu_from_descr": "true",
    "params_file": "config/oakd.yaml",
}.items()

# supervisor
SUPERVISOR_XMLRPC_URL = "http://localhost:9001/RPC2"
