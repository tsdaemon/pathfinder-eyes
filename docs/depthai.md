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

(Duplicated as a comment in [ros2_ws/launch_depthai_inertial.py](../ros2_ws/launch_depthai_inertial.py).)

## Software

Installed via [infra/install-depthai.sh](../infra/install-depthai.sh):

- `ros-jazzy-depthai-ros` — provides `depthai_ros_driver` and `depthai_examples`
- `depthai` Python bindings (in the venv)

RTAB-Map comes from `ros-jazzy-rtabmap-ros` ([infra/install-ros.sh](../infra/install-ros.sh)),
along with `imu_filter_madgwick`, `image_pipeline`, `robot_localization`.

## Pipeline in use ("inertial")

```
depthai_ros_driver/camera.launch.py  (mono 400P, RGB disabled, depth not aligned to RGB)
  ├── /oakd/right/image_rect , /oakd/right/camera_info
  ├── /oakd/stereo/image_raw
  └── /oakd/imu/data  ──► imu_filter_madgwick (use_mag=false, ENU) ──► /imu/data
                                                                          │
rtabmap_sync/rgbd_sync ◄── right + depth + camera_info                   │
        │                                                                 │
        └──► rtabmap_odom/rgbd_odometry ◄─────────────────────────────────┤
                    │                                                    │
                    └──► rtabmap_slam/rtabmap ◄──────────────────────────┘
```

Launch files: [launch_depthai_inertial.py](../ros2_ws/launch_depthai_inertial.py) and
[launch_rmaptab_inertial.py](../ros2_ws/launch_rmaptab_inertial.py). All parameters (RTAB-Map
tuning, frame ids, camera name) live in [ros2_ws/config.py](../ros2_ws/config.py); the
driver's own per-sensor/IMU tuning is in [ros2_ws/config/oakd.yaml](../ros2_ws/config/oakd.yaml).
`CAMERA_FRAME` is `oak-d-base-frame`; odom/map frames are the conventional `odom`/`map`.

Both `depthai` and `rtabmap` run as supervisord programs — see
[docs/supervisord.md](supervisord.md) for how they're started, restarted and health-checked.

### Why depthai_ros_driver instead of depthai_examples

An earlier RGB+depth pipeline built on `depthai_ros_driver` was tried first and dropped for
being too heavy for the Pi (see [docs/notes/2025.05.04.md](notes/2025.05.04.md) and
[docs/notes/2025.05.10.md](notes/2025.05.10.md)), in favor of `depthai_examples`'
`stereo_inertial_node`. That node turned out to have a persistent ~100-150ms lag between its
`/imu` topic and its camera frames — not a bug, but device-side XLink/VPU bandwidth
contention combined with IMU batch settings hardcoded in C++ (`batchReportThreshold=5`,
`maxBatchReports=20`), un-tunable without a source rebuild. `depthai_ros_driver` exposes the
same batching as ROS params (`imu.i_batch_report_threshold`, `imu.i_max_batch_reports` in
`config/oakd.yaml`), tuned there to eliminate the lag (verified: small negative gap instead of
a persistent +100ms - see [docs/notes/2026.08.07.md](notes/2026.08.07.md)). So we're back on
`depthai_ros_driver`, but configured mono-only (`rgb.i_disable_node: true`) to keep the same
lightweight footprint that made `stereo_inertial_node` the pick in the first place — this
isn't a return to the heavy RGB+depth config that got dropped before.

## TF tree

`oak-d-base-frame` used to have two parents: [ros2_ws/robot.urdf](../ros2_ws/robot.urdf)
parented it under `base_link`, while RTAB-Map separately published `odom → oak-d-base-frame`
(`frame_id` in `config.py`). Fixed by pointing RTAB-Map's `frame_id` at `base_link` instead,
so RTAB-Map owns `odom → base_link` and the URDF's static joint is the sole parent of
`oak-d-base-frame`. Tree is now `map → odom → base_link → oak-d-base-frame → camera optical
frames`. The camera offset in the URDF is now the real measured mounting position (see the
comment on `base_link` in `robot.urdf` for the physical reference point it's measured from).

## History

The project started with two IMX219 CSI cameras and Kalibr calibration
(now in [_archive/](../_archive/)) — abandoned because the stereo disparity was too poor and
too slow for reliable visual odometry. See
[docs/notes/2025.04.13.md](notes/2025.04.13.md) for the decision to switch to the OAK-D, and
the rest of [docs/notes/](notes/) for the full day-by-day story (calibration, WSL/offloading
experiments, VO vs VIO research).
