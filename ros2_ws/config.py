# Constants
OAKD_NAME = "oakd"
SUPERVISOR_NAMESPACE = "supervisor"

# How to survive visual-odometry dropouts during fast spins (2026-11-11: VO lost tracking 7x
# during rough driving, each reset silently dropped the rotation done while lost, and
# RTAB-Map then rejected every loop closure for disagreeing with odometry by 12-52 deg):
#   "new_map" - on a VO reset, RTAB-Map starts a new map segment right away instead of
#               chaining it onto the old one, and re-links the segments by place recognition,
#               so there's no wrong odometry link for loop closures to fight.
#   "ekf_imu" - a robot_localization EKF fuses VO velocity with the IMU gyro, so heading keeps
#               integrating through dropouts; RTAB-Map uses the EKF output as its odometry.
#               (VO resets don't trigger new maps in this mode - external odometry.)
ODOM_DROPOUT_MODE = "ekf_imu"
EKF_ODOM_TOPIC = "/odometry/filtered"
VO_TOPIC = "/vo"

# rtabmap
RTABMAP_COMMON_PARAMS = {
    "frame_id": "base_link",
    "odom_frame_id": "odom",
    "map_frame_id": "map",
    "publish_tf": True,
    "Odom/ResetCountdown": "1",
    # Was "true": that defers the new map until a loop closure with the old one is found,
    # which didn't kick in at all during the 2026-11-11 test (no "Increment map id" in the log).
    "Rtabmap/StartNewMapOnLoopClosure": "false",
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
        # Reliable subscriptions. Default (0) came out best-effort, and with ~0.8 MB RGBD
        # messages split into many DDS fragments, one lost fragment drops the whole frame:
        # rgbd_sync published ~23 Hz but rgbd_odometry received ~12 Hz (2026-11-11).
        "qos": 1,
        # Lighter visual odometry for the Pi. RTAB-Map defaults (1000 features, 2000-point
        # local map, descriptor matching) took 80-100ms/frame. Same values as the old
        # non-inertial config removed in PR #2.
        "Vis/MaxFeatures": "500",
        "OdomF2M/MaxSize": "800",
        "Vis/CorType": "1",  # optical flow instead of descriptor matching
        "GFTT/MinDistance": "10",
    }
    | RTABMAP_COMMON_PARAMS
]

# robot_localization EKF for ODOM_DROPOUT_MODE="ekf_imu". Ground robot, so 2D. Config arrays
# are [x y z roll pitch yaw  vx vy vz  vroll vpitch vyaw  ax ay az].
# Yaw rate comes ONLY from the gyro: VO runs at ~4Hz on the Pi, and during a ~190 deg/s
# spin its yaw rate is garbage reported with high confidence - fusing it dragged the EKF
# heading off by hundreds of degrees (2026-11-11). VO contributes vx/vy only; long-term yaw
# drift is RTAB-Map's job (loop closures correct map -> odom).
EKF_PARAMS = [
    {
        # 30Hz kept missing its deadline on the loaded Pi ("Failed to meet update rate").
        "frequency": 20.0,
        # Without this the "odometry/filtered topic status" diagnostic is never ticked and
        # always reports 0 Hz, even while the EKF publishes at full rate (2026-11-13).
        "print_diagnostics": True,
        # IMU messages arrive stamped slightly older than VO's camera frames. Without this,
        # once a VO message is applied every later-arriving IMU message is "in the past" and
        # gets silently dropped - with yaw from the gyro only, EKF heading never moved.
        "smooth_lagged_data": True,
        "history_length": 1.0,
        "two_d_mode": True,
        "publish_tf": True,
        "map_frame": "map",
        "odom_frame": "odom",
        "base_link_frame": "base_link",
        "world_frame": "odom",
        # VO via vo_gate.py, which distrusts VO's linear velocity during fast turns.
        "odom0": VO_TOPIC + "_gated",
        "odom0_config": [
            False,
            False,
            False,
            False,
            False,
            False,
            True,
            True,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
        ],
        "odom0_queue_size": 5,
        # IMU publishes ~95Hz; the default queue of 1 drops most of it between EKF cycles,
        # and 20 (0.2s) still overflowed when the loaded Pi stalled the EKF.
        "imu0_queue_size": 100,
        "imu0": "/imu/data",
        # robot_localization applies this mask in the IMU's own frame, then rotates it into
        # base_link. The OAK-D's IMU is mounted ~90 deg rotated, so IMU-frame vyaw alone lands
        # on base_link's vroll/vpitch and two_d_mode throws it away - the gyro silently
        # contributed nothing (seen in the EKF debug output, 2026-11-11). Enable all three
        # angular rates; after rotation two_d_mode keeps only the base_link yaw rate.
        "imu0_config": [
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            True,
            True,
            True,
            False,
            False,
            False,
        ],
        # Teleop's /cmd_vel as a control input: the EKF's prediction accelerates vx/vy towards
        # the commanded speed, and with no command for control_timeout it decelerates to zero,
        # so a parked robot predicts zero velocity between noisy VO readings. Yaw rate isn't
        # controlled - the gyro is better, and commanded wz is uncalibrated (1.5 rad/s command
        # vs ~3.4 rad/s real spin). Commanded vx/vy magnitude is uncalibrated too (teleop
        # 0.5 m/s = full PWM), so VO still sets the actual speed.
        # control_timeout must be set: robot_localization's default 0 counts every command as
        # already stale.
        "use_control": True,
        "control_timeout": 0.5,
        # [vx vy vz vroll vpitch vyaw]; limits in m/s^2, gains in 1/s. robot_localization's
        # example values for vx, copied to vy for mecanum strafing.
        "control_config": [True, True, False, False, False, False],
        "acceleration_limits": [1.3, 1.3, 0.0, 0.0, 0.0, 0.0],
        "acceleration_gains": [0.8, 0.8, 0.0, 0.0, 0.0, 0.0],
        "deceleration_limits": [1.3, 1.3, 0.0, 0.0, 0.0, 0.0],
        "deceleration_gains": [1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    }
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
