# Camera & SLAM (DepthAI + RTAB-Map)

## Hardware

- **Luxonis OAK-D S2** (fixed focus) — stereo pair + RGB + IMU, on-board Movidius MyriadX VPU
  (shows up as `03e7:2485` on USB).
- **Powered USB hub** between the camera and the Pi — not optional.

### Power gotcha

Powering the camera straight from the Pi, while the Pi itself runs off a power bank, makes
the OAK-D flap between USB speed modes and the depthai bridge dies. Fix: a powered USB hub,
and the hub has to actually stay powered — power banks cut their output when idle. Safe
bring-up order:

1. Stop the Pi
2. Disconnect hub and Pi power-bank connections
3. Connect the hub to power
4. Connect the Pi to power

(Duplicated as a comment in [ros2_ws/launch_depthai.py](../ros2_ws/launch_depthai.py).)

## Software

Installed via [infra/install-depthai.sh](../infra/install-depthai.sh):

- `ros-jazzy-depthai-ros` — provides `depthai_ros_driver` and `depthai_examples`
- `depthai` Python bindings (in the venv)

RTAB-Map comes from `ros-jazzy-rtabmap-ros` ([infra/install-ros.sh](../infra/install-ros.sh)),
along with `imu_filter_madgwick`, `image_pipeline`, `robot_localization`.

## Pipeline in use ("inertial")

```
depthai_examples/stereo_inertial_node  (mono 400p, depth_aligned=false)
  ├── /right/image_rect , /right/camera_info
  ├── /stereo/depth
  └── /imu  ──► imu_filter_madgwick (use_mag=false, ENU) ──► /imu/data
                                                               │
rtabmap_sync/rgbd_sync ◄── right + depth + camera_info         │
        │                                                      │
        └──► rtabmap_odom/rgbd_odometry ◄──────────────────────┤
                    │                                          │
                    └──► rtabmap_slam/rtabmap ◄────────────────┘
```

Launch files: [launch_depthai_inertial.py](../ros2_ws/launch_depthai_inertial.py) and
[launch_rmaptab_inertial.py](../ros2_ws/launch_rmaptab_inertial.py). All parameters (RTAB-Map
tuning, frame ids, depthai launch args) live in one place:
[ros2_ws/config.py](../ros2_ws/config.py). `CAMERA_FRAME` is `oak-d-base-frame`; odom/map
frames are the conventional `odom`/`map`.

Both `depthai` and `rtabmap` run as supervisord programs — see
[docs/supervisord.md](supervisord.md) for how they're started, restarted and health-checked.

### The other pipeline (unused)

[launch_depthai.py](../ros2_ws/launch_depthai.py) + [launch_rmaptab.py](../ros2_ws/launch_rmaptab.py)
build on `depthai_ros_driver` instead, loading RTAB-Map as composable nodes into the driver's
container and using RGB+depth rather than right+depth. It was benchmarked as too heavy for
the Pi — the "inertial" pipeline above is the one that's actually been run. Both are compared
in [docs/notes/2025.05.04.md](notes/2025.05.04.md) and [docs/notes/2025.05.10.md](notes/2025.05.10.md).

## Known issue: TF tree

[ros2_ws/robot.urdf](../ros2_ws/robot.urdf) parents `oak-d-base-frame` under `base_link`
with a placeholder offset (`xyz="0 0.5 0.5"` — not the real mounting position), while
RTAB-Map also publishes `odom → oak-d-base-frame` (`frame_id` in `config.py`). That gives one
frame two parents. Fix by either pointing RTAB-Map's `frame_id` at `base_link`, or dropping
the camera link from the URDF and letting depthai's own robot_description own it — and
measure the actual camera offset while at it.

## History

The project started with two IMX219 CSI cameras and Kalibr calibration
(now in [_archive/](../_archive/)) — abandoned because the stereo disparity was too poor and
too slow for reliable visual odometry. See
[docs/notes/2025.04.13.md](notes/2025.04.13.md) for the decision to switch to the OAK-D, and
the rest of [docs/notes/](notes/) for the full day-by-day story (calibration, WSL/offloading
experiments, VO vs VIO research).
