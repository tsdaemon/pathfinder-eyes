# Process supervision (supervisord)

Everything on the robot runs as a `supervisord` child process rather than being launched by
hand, so it survives crashes and can be restarted from ROS. Config:
[ros2_ws/supervisord.conf](../ros2_ws/supervisord.conf).

| Program | Command | Role |
|---|---|---|
| `robot_state_publisher` | `ros2 run robot_state_publisher ... robot.urdf` | static TF for the robot body |
| `depthai` | [launch_depthai_inertial.py](../ros2_ws/launch_depthai_inertial.py) | camera + IMU orientation filter |
| `rtabmap` | [launch_rmaptab_inertial.py](../ros2_ws/launch_rmaptab_inertial.py) | visual odometry + SLAM |
| `foxglove_bridge` | `ros2 run foxglove_bridge` on port 8765 | remote visualisation |
| `supervisord_bridge` | [launch_supervisord_bridge.py](../ros2_ws/launch_supervisord_bridge.py) | process control + health from ROS |
| `diagnostics` | [launch_diagnostics.py](../ros2_ws/launch_diagnostics.py) | CPU / RAM monitors |
| `pico_control` | [launch_pico_control.py](../ros2_ws/launch_pico_control.py) | `cmd_vel` → Pico over UART |
| `teleop_joy` | [launch_teleop_joy.py](../ros2_ws/launch_teleop_joy.py) | `/joy` → `cmd_vel` |

See [docs/depthai.md](depthai.md) for what `depthai` and `rtabmap` actually do, and
[docs/motor-control.md](motor-control.md) / [docs/remote-control.md](remote-control.md) for the
Pico link and joystick control.

## Controlling it

```bash
supervisorctl -c ros2_ws/supervisord.conf status
```

Or over ROS, via the bridge described below:

```bash
ros2 topic pub --once /supervisor/restart std_msgs/String "{data: depthai}"
ros2 topic echo /diagnostics
```

The supervisord HTTP/XML-RPC interface listens on `0.0.0.0:9001` **with no authentication**
(supervisord logs a `CRIT` about this on every start) — fine on a private link, not on an
open network.

## supervisord_bridge

[supervisord_bridge_node.py](../ros2_ws/src/supervisord_bridge/supervisord_bridge/supervisord_bridge_node.py)
talks XML-RPC to supervisord at `http://localhost:9001/RPC2` (URL configured in
[config.py](../ros2_ws/config.py)) and:

- subscribes to `supervisor/start`, `supervisor/stop`, `supervisor/restart` (`std_msgs/String` = program name)
- publishes `supervisor/status` (supervisord's own state)
- maps every program's supervisord state onto `diagnostic_msgs/DiagnosticStatus` on `/diagnostics`

This was flagged as a possible standalone OSS package — it's generic, not depthai/robot
specific.

## watchdog

[watchdog_node.py](../ros2_ws/src/supervisord_bridge/supervisord_bridge/watchdog_node.py)
subscribes to an arbitrary heartbeat topic (message type discovered at runtime) and publishes
a restart request for a named supervisord program when messages stop arriving, up to
`max_restarts` before declaring the program dead. Motivation: `depthai` hangs occasionally.

**Currently disabled** — commented out in
[launch_supervisord_bridge.py](../ros2_ws/launch_supervisord_bridge.py). It was configured to
watch `/stereo/camera_info` with a 10 s timeout; re-enabling it is a one-line uncomment plus a
rebuild.

## diagnostics

[launch_diagnostics.py](../ros2_ws/launch_diagnostics.py) runs `cpu_monitor` and
`ram_monitor`. The `diagnostic_aggregator` node (config at
[ros2_ws/config/diagnostics_aggregation.yaml](../ros2_ws/config/diagnostics_aggregation.yaml))
is also commented out there — currently nothing rolls the individual `/diagnostics` entries
into a single summary status.
