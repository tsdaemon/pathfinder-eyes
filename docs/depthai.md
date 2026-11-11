# Camera & SLAM (DepthAI + RTAB-Map)

## Hardware

- **Luxonis OAK-D S2** (fixed focus) — stereo pair + RGB + IMU, on-board Movidius MyriadX VPU
  (shows up as `03e7:2485` on USB).
- **IMU: BNO086** (9-axis: accelerometer, gyro, **magnetometer**, plus on-chip fusion that can
  output a ready orientation). Confirmed 2026-11-11 with
  `dai.Device().getConnectedIMU()` (needs the `depthai` program stopped - one client at a
  time). Some OAK-D S2 units ship with a 6-axis BMI270 instead, so don't assume from the model.
- **Powered USB hub** between the camera and the Pi — not optional.
- **The camera must run at USB 3.** The hub connects to the Pi through a USB-C-to-A adapter
  that only carries USB 3 with the USB-C plug in **one orientation** (marked). The wrong way
  round still works, silently, at USB 2 (480 Mbps): camera frames drop to ~24 Hz (right) and
  ~18 Hz (depth) of 30. Check in the driver log for `USB SPEED: SUPER` (not `HIGH`), or with
  the stack stopped: `env/bin/python -c "import depthai as dai; print(dai.Device().getUsbSpeed())"`.
  `lsusb -t` is misleading here: an unstarted camera (bootloader) always shows 480M.

### IMU settings

All in [ros2_ws/config/oakd.yaml](../ros2_ws/config/oakd.yaml) under `imu:`.

- **Gyro bias.** The driver defaults to `GYROSCOPE_RAW`, which has no bias compensation:
  with the robot standing still, integrated yaw crept ~0.2°/s (~12°/min). Set to
  `GYROSCOPE_CALIBRATED` so the chip removes the bias itself.
- **Magnetometer is unused.** `imu_filter_madgwick` runs with `use_mag: false`, and the driver's
  `i_message_type` is `IMU` (no separate mag topic). On a robot with four DC motors, a
  battery pack and a Pi right next to the sensor, compass heading is likely to be pulled by
  tens of degrees, so test it with the motors running before relying on it.
- **On-chip orientation.** `i_enable_rotation: true` with `i_rot_mode: ROTATION_VECTOR`
  (uses the magnetometer) is on by default, but the Madgwick filter overwrites the
  orientation, so it isn't used. `GAME_ROTATION_VECTOR` (gyro + accel, no compass) would be
  the candidate if we ever want the chip's own fusion.

Check heading behaviour live with [ros2_ws/tools/yaw_monitor.py](../ros2_ws/tools/yaw_monitor.py)
(you drive) or [ros2_ws/tools/spin_test.py](../ros2_ws/tools/spin_test.py) (it drives): both
compare how far the robot turned according to the EKF, VO alone, and the raw gyro.

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

On 2026-11-11, after the camera moved to USB 3 at full 30 fps and VO started using ~90% of a
core, the Pi lost power twice within ~10 minutes (no shutdown in the journal, the hub gone
from USB afterwards). Suspected: the power bank cutting out under the higher load. Not yet
confirmed - check the bank and the hub's power first if the Pi drops off again.

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
(simplified - with ODOM_DROPOUT_MODE="ekf_imu" an EKF sits between VO and rtabmap, see below)
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

### Odometry dropouts during fast spins (`ODOM_DROPOUT_MODE`)

Mecanum rotation only works near full speed (see [motor-control.md](motor-control.md)), so
every in-place turn is a fast spin, and visual odometry loses tracking during it
(`Registration failed: Not enough inliers`). In the 2026-11-11 rough-driving test VO reset 7
times. Each `Odom/ResetCountdown` reset resumes from the last good pose, which silently drops
the rotation done while lost. RTAB-Map then rejected every second-lap loop closure (78 in a
row) for disagreeing with odometry by 12-52° of heading (`RGBD/OptimizeMaxError`).

`ODOM_DROPOUT_MODE` in [config.py](../ros2_ws/config.py) switches between two fixes:

- `"ekf_imu"` (current, working): heading comes from the gyro, not from VO.
- `"new_map"`: plain VO, the old setup. `Rtabmap/StartNewMapOnLoopClosure` is now `false` so
  a VO reset starts a new map segment right away (look for `Increment map id` in the rtabmap
  log), to be re-linked by place recognition. Not tested.

#### `ekf_imu` data flow

```
/imu/data (gyro) ─────────────┬──────────────────────────► ekf_node ──► odom → base_link TF
                              ▼                               ▲          /odometry/filtered
rgbd_odometry ──► /vo ──► vo_gate.py ──► /vo_gated (vx, vy) ──┘                │
      ▲                                                                       ▼
      └──── motion guess from odom → base_link TF                        rtabmap
```

- **EKF** (`EKF_PARAMS`, `robot_localization`, 2D): yaw rate from the gyro only; VO provides
  forward/sideways velocity only. Long-term heading drift is corrected by RTAB-Map's loop
  closures (`map → odom`), not by VO.
- **VO** (`rgbd_odometry`) publishes `/vo` without TF in its own `vo_odom` frame, doesn't read
  the IMU itself, and takes its motion guess from the EKF TF (`guess_frame_id: odom`), so
  during spins it knows roughly how far the image rotated.
- **[vo_gate.py](../ros2_ws/vo_gate.py)** relays `/vo` → `/vo_gated`, inflating VO's vx/vy
  covariance whenever the gyro reads > 0.8 rad/s near the frame's stamp.
- **RTAB-Map** subscribes to `/odometry/filtered` with `subscribe_odom_info: false` (odom_info
  is stamped with camera frames and doesn't sync with EKF output).

#### Gotchas found getting there (2026-11-11)

Each of these silently broke heading while everything looked like it was running:

1. **Gyro bias.** `GYROSCOPE_RAW` drifted ~12°/min standing still. Fixed with
   `GYROSCOPE_CALIBRATED` (see IMU settings).
2. **The gyro wasn't fused at all.** `robot_localization` applies `imu0_config` in the IMU's
   own frame, then rotates it into `base_link`. The OAK-D's IMU is mounted ~90° rotated, so
   IMU-frame vyaw landed on base_link vroll/vpitch and `two_d_mode` dropped it. The EKF's
   heading had come entirely from VO. Fix: enable all three angular rates. Found with the
   EKF's `debug: true` output ("After applying transform to base_link, update vector is").
3. **VO's yaw rate is garbage during spins** but reported with high confidence. VO runs
   at only ~4-6 Hz on the Pi (each frame ~90ms), so at ~200°/s the image turns 20-40° between
   frames. Fusing it dragged EKF heading by up to hundreds of degrees. Not fused anymore.
4. **VO's linear velocity is garbage during spins too**: 0.1-0.7 m/s with ~1 cm/s claimed
   confidence (camera is 9cm off the rotation centre). Moved the EKF 27-38cm per two
   in-place turns. Fixed by `vo_gate.py`.
5. **VO dropped many frames waiting for IMU** ("We didn't receive IMU newer than previous
   image"). Fixed by not feeding VO the IMU (it uses the EKF guess instead).
6. **EKF IMU queue.** The default `imu0_queue_size` of 1 drops most 95 Hz gyro messages; now
   100. EKF runs at 20 Hz (30 Hz missed its deadline on the loaded Pi).

#### Results (2026-11-11, in-place spins at ~200°/s)

Tested with [tools/spin_test.py](../ros2_ws/tools/spin_test.py), which drives the robot and
compares the gyro, EKF and VO (always sends stop on exit):

- EKF heading within ±1.5° of the gyro on every run (2-3 full turns either direction, and
  random ¼-1 turn bursts with direction reversals). Before: 55° short over two turns.
- EKF position drift per two in-place turns: 0.2-5 cm (before the gate: 27-38 cm).
- RTAB-Map: 0 rejected and 33 accepted loop closures over ~16 turns of spinning (before: 78
  rejected in a row). Robot's map position stayed within 14cm of the start (some is real wheel
  scrub). Accumulated odometry heading drift was ~18° over ~4.5 min of continuous spinning,
  corrected by loop closures.

#### Frame rates and "Frequency too low"

RTAB-Map's nodes must subscribe **reliably** (`"qos": 1` in `RTABMAP_INERTIAL_PARAMS`). The
default came out best-effort, and the ~0.8 MB RGBD messages are split into many DDS fragments,
so one lost fragment silently drops the whole frame. With best-effort, `rgbd_sync` got ~22 of
the camera's 30 Hz and VO received ~12 Hz of `rgbd_sync`'s ~23; with reliable, every stage
runs at 30 Hz and VO went from ~6 to ~11.5 Hz (2026-11-11). The same applies to any probe
script: subscribe reliably, or you'll measure the losses, not the stream.

The "Frequency too low" diagnostics compare each topic against the camera's 30 Hz (warning
below 50%). With reliable QoS the only remaining one is `rgbd_odometry: Output Status`: VO
processes ~11.5 of 30 frames/s, CPU-bound (~70 ms/frame, ~90% of a core). The lighter VO
settings (500 features, 800-point local map, optical-flow matching) already cut it from
80-100 ms/frame.

Don't set the cameras to 15 fps (`left/right.i_fps` in `oakd.yaml`) to quiet the warnings:
on 2026-11-11 that stopped the IMU entirely and dropped images to 2-6 Hz.

Not tested yet: driving while turning (arcs). `vo_gate.py` ignores VO's linear velocity
during any turn, so the EKF coasts on its last estimate through it.

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
