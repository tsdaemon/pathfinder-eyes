# Plan: Basalt VIO as RTAB-Map's odometry

**Status (2026-11-13): abandoned after step 3.** Stock `vio.launch.py` (driver v3 3.2.1,
OAK-D S2): heading tracked the gyro within ~0.5-6 deg and it held within 1-2 cm parked, but
translation was unusable. On a 1.5 s forward drive that VO measured at ~40 cm, it reported 58-79
cm at 60 fps (190 cm on one back segment) and 504 cm at 30 fps, sank up to ~1 m vertically, and
stalled ~0.5 s after stops. Fixed exposure made it worse. Likely cause: camera/IMU timing with
the BNO086 (unverified). Installing v3 required removing the v2 driver (both ship the same
DepthAI core headers); roll back with
`sudo apt remove ros-jazzy-depthai-v3 'ros-jazzy-depthai-*-v3' && sudo apt install ros-jazzy-depthai-ros`.

Goal: replace the current odometry chain (RTAB-Map `rgbd_odometry` + robot_localization EKF
+ `vo_gate.py`) with Basalt VIO, which fuses stereo and IMU in one estimator. RTAB-Map stays
for mapping and loop closures.

Why (2026-11-13 tests):
- VO alone barely drifts while parked (keyframe-anchored), but the EKF only fuses VO's velocity,
  so its pose random-walks ~2-3 cm/min.
- `vo_gate.py` gated almost all VO while driving "straight", because the chassis veers at
  ~0.9 rad/s. Raising its threshold to 2 rad/s fixed that, but it's still a hand-tuned patch.
- OpenVINS / VINS-Fusion were skipped earlier because they need camera-IMU temporal
  calibration (docs/notes/2025.05.04.md). Basalt runs inside DepthAI and uses the device's
  own factory calibration and on-device timestamps for both sensors.

## What's available (checked 2026-11-13)

- `ros-jazzy-depthai-ros-v3` 3.2.1 (DepthAI core `ros-jazzy-depthai-v3` 3.10.0) is in the
  regular ROS apt repo. Packages are suffixed `_v3`, so they install next to the current v2
  driver.
- VIO is a switch in the v3 driver: `pipeline_gen.i_enable_vio: true`. Its example config
  (`vio.yaml`) runs stereo and VIO at 60 fps, IMU batch threshold 1 / max 10 reports.
- It publishes `nav_msgs/Odometry` (topic ends in `odometry`, frame `odom`); exact topic, child
  frame and TF behaviour to be checked live.
- Luxonis marks the VSLAM host nodes as early access. RVC2 (our OAK-D S2) is supported.
- Basalt runs on the host (Pi), not on the camera.

## Risks

- **CPU:** today VO alone uses ~90% of a core at ~11 Hz. Basalt at 60 fps plus RTAB-Map may not
  fit. Lower fps is the first knob.
- **IMU:** our IMU is a BNO086. The Basalt example asks for raw accel + gyro at 200 Hz; check the
  BNO086 delivers that and that the driver doesn't need the BMI270 the newer OAK models have.
- **Frames:** Basalt reports the pose of a camera/IMU frame. RTAB-Map and Nav2 want
  `odom -> base_link`, so a fixed camera-to-base offset has to be applied (9 cm off the
  rotation centre).
- **Camera is exclusive:** only one driver can hold the OAK-D, so trials stop the `depthai`
  supervisord program.

## Steps

1. **Install** `ros-jazzy-depthai-ros-v3` (system apt). Nothing else changes yet.
2. **Standalone trial, robot parked.** Stop the `depthai` program, run the v3 driver with VIO
   on. Check: odometry topic/frames/rate, whether it publishes TF, CPU load, IMU rate,
   startup/initialisation behaviour.
3. **Bench tests, same as for the EKF** (scripts from 2026-11-13: parked drift, 1.5 s forward
   and back, `tools/spin_test.py` 2 turns each way). Compare against VO-only and the EKF
   numbers in docs/notes/2026.11.13.md. Also try an arc (forward + turn) - untested so far.
4. **Integrate** if step 3 beats the EKF: new `ODOM_DROPOUT_MODE = "basalt"` in `config.py`;
   depthai launch switches to the v3 driver with VIO; RTAB-Map takes Basalt's odometry and
   runs no `rgbd_odometry`, EKF or `vo_gate.py`. Keep the old modes selectable until Basalt
   has survived a room loop.
5. **Room loop + return-to-start** (the next step in docs/notes/plan.md), then update
   docs/depthai.md and delete what's no longer used.
