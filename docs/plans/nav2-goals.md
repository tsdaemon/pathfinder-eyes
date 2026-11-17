# Plan: give the robot goals (Nav2 on RTAB-Map)

Goal: click a pose in Foxglove's 3D panel, the robot plans a path through RTAB-Map's map and
drives there. Frontier exploration ("explore on its own") comes after this works.

Starting point (2026-11-17): VIO + RTAB-Map hold within ~4 cm / 7 deg in the `map` frame
after a room loop; RTAB-Map is 2D (`Reg/Force3DoF`) and publishes `/map`, but its `Grid/*`
parameters are defaults. Nav2 1.3.14 is installed; `twist_mux` isn't.

## Architecture

```
RTAB-Map ── /map (OccupancyGrid) ──► Nav2 global + local costmap
RTAB-Map ── map → odom TF;  EKF ── odom → base_link TF   (no AMCL, no map_server)
Foxglove 3D panel ── /goal_pose ──► bt_navigator → planner → controller ── /cmd_vel_nav
teleop (joystick/Deck) ── /cmd_vel_joy ┐
Nav2 ── /cmd_vel_nav ──────────────────┴► twist_mux (joystick wins) ── /cmd_vel ──► vel_to_serial
```

Nav2 runs `navigation_launch.py` only (planner, controller, behaviors, bt_navigator,
velocity smoother), not its SLAM/localization parts.

## Steps

1. **Occupancy grid fit for Nav2.** In `RTABMAP_SLAM_PARAMS`: `Grid/3D false`,
   `Grid/RayTracing true` (clears space that freed up), `Grid/RangeMax 3.0` (400P stereo is
   noisy further out), `Grid/NormalsSegmentation false` with `Grid/MaxGroundHeight 0.03` and
   `Grid/MaxObstacleHeight 0.4` (robot is ~0.2 m tall; ignore table tops). Check `/map` in
   Foxglove after a drive: walls solid, floor free, no ghost obstacles. Closes
   docs/tasks/confirm-occupancy-grid.md.
2. **Keep the map across restarts.** Drop `-d` from the rtabmap launch; DB at a fixed path
   (`~/.ros/rtabmap.db`); a way to start fresh (delete the DB, or a launch flag). Check that a
   restart relocalizes in the saved map (`map → odom` jumps to the right place after the
   robot sees a known spot).
3. **Calibrate velocity.** Nav2 sends real m/s and rad/s; `vel_to_serial`'s
   `max_linear_speed`/`max_angular_speed` must be the actual speed at full PWM (measured so
   far: 0.25 m/s command → 0.19 m/s, so full ≈ 0.38 m/s; full turn ≈ 3.4 rad/s, not 1.5).
   Also find the smallest command that still moves the wheels (deadband) - Nav2 will ask for
   slow speeds near the goal.
4. **twist_mux.** `apt install ros-jazzy-twist-mux`; teleop → `/cmd_vel_joy` (priority),
   Nav2 → `/cmd_vel_nav`, mux → `/cmd_vel`. Holding LB overrides Nav2 at any time; releasing
   it hands control back after the mux timeout.
5. **Nav2 config + launch** (`config/nav2.yaml`, `launch_nav2.py`, supervisord program
   `nav2`): global and local costmap from `/map` (static + inflation; no depth obstacle
   layer yet), footprint from the chassis (~0.18 x 0.15 m plus wheels - measure), planner
   NavFn, controller DWB with lateral (vy) samples for mecanum, max 0.15 m/s / 1.0 rad/s to
   start, velocity smoother on. Leave out docking, collision monitor and route server.
6. **First goals.** Foxglove 3D panel → Publish → "Pose" on `/goal_pose`. 1 m straight, then
   around a corner, then across the room. Watch CPU: VO already takes ~85% of a core.
7. **Depth obstacles in the local costmap** if `/map` (updated ~1 Hz) reacts too slowly to
   things that appear: a point cloud from the depth image into an obstacle layer.

Then: frontier exploration (`explore_lite`, source build - not packaged for Jazzy).

## Risks

- **CPU:** 4 cores, VO + RTAB-Map + depthai already busy. If Nav2 doesn't fit, lower the
  controller rate first (10 Hz), then costmap update rates.
- **Low-speed control:** fixed-gear PWM, no wheel encoders; slow commands may stall. Step 3
  decides the controller's minimum speeds.
- **VO resets during spins** still happen (~13 per room loop); Nav2 rotating in place will
  trigger them. Keep max rotation speed low.
