# Remote control & visualization

How to see what the robot sees, and how to actually drive it, from a laptop rather than
standing over the Pi.

## History

Three approaches have been tried, in order:

1. **VNC + RViz/rqt on the Pi itself.** Remote desktop into the Pi and run the normal ROS GUI
   tools locally on it ([infra/install-ubuntu.sh](../_archive/install-ubuntu.sh) in the
   archive installed the VNC server + desktop packages for this). Works, but the Pi is
   rendering RViz for you as well as running the whole perception stack — heavy, and the
   least practical option once the graphics load and the SLAM load compete for the same
   weak GPU/CPU.
2. **Full ROS 2 on the desktop, joined to the same network.** Run RViz/`rtabmap_viz` directly
   on a laptop as a normal ROS 2 node, discovering the Pi's nodes over DDS. Tried on WSL (broke
   networking) and a dual-boot Ubuntu install (better, but unstable — RTAB-Map's odometry
   quality would periodically collapse to 0 and need a restart). The likely root cause,
   per [docs/notes/2025.04.19.md](notes/2025.04.19.md): raw image topics over Wi-Fi don't hold
   up — full-resolution frames just don't transfer reliably, and DDS discovery over a flaky
   link isn't much better.
3. **`foxglove_bridge`.** What's actually running today ([docs/supervisord.md](supervisord.md)
   lists it as a supervised program on port 8765). This sidesteps both problems above:
   rendering happens on the client, not the Pi, and — unlike raw DDS — you only pay for the
   topics you actually subscribe to in a given Foxglove layout, instead of every image topic
   flowing whether you're looking at it or not. The recorded failure mode is the opposite
   extreme: subscribing to a full-resolution image topic saturates the websocket
   (`Send buffer limit reached`, seen in `ros2_ws/log/`) — so the fix is being selective about
   what a layout subscribes to, not switching approach again.

**Current answer: use Foxglove Studio, connect to `ws://eyes.local:8765`.** It's the right
tool for both monitoring and — see below — basic driving.

Layout: import [foxglove/pathfinder.json](../foxglove/pathfinder.json)
(Layouts → Import). Plots on the left, diagnostics + log in the middle, 3D + camera on the right.
It includes a User Script (`diag_values`) that republishes `/diagnostics` string values as
numbers on `/studio_script/diag_values`. To plot another diagnostic, add a Plot path
`/studio_script/diag_values.values[:]{name=="<status name>"}{key=="<key>"}.value`
(pipeline rates: status `pipeline: /vo`, key `hz`). For the node/topic graph itself, add a
Topic Graph panel — it shows wiring, not whether messages actually flow.

## Manual driving today

Foxglove's **Teleop panel** publishes `geometry_msgs/Twist` directly to `cmd_vel`, which
[vel_to_serial](motor-control.md) already consumes and turns into wheel commands. This works
right now with no additional stack — it's the cheapest option and good enough for
driving-around testing.

**Joystick:** an 8BitDo Ultimate 2 Wireless paired to the Pi over Bluetooth. The
`teleop_joy` supervisord program ([launch_teleop_joy.py](../ros2_ws/launch_teleop_joy.py))
runs `joy_node` (reads the pad, publishes `/joy`) and `teleop_twist_joy` (turns `/joy` into
`/cmd_vel`). No laptop needed. Hold **LB** to drive, **RB** for turbo; left stick = drive and
strafe, right stick X = turn. Mapping in
[config/teleop_joy.yaml](../ros2_ws/config/teleop_joy.yaml).

The controller is paired and trusted, so it reconnects on its own: press **Home** to wake it.
To pair a new one (needs `bluez`, and `dtoverlay=disable-bt` removed from
`/boot/firmware/config.txt` - on a Pi 5 Bluetooth has its own UART, separate from the
Pico's):

```bash
bluetoothctl scan on            # pad in pairing mode; note its MAC
bluetoothctl pair <MAC> && bluetoothctl trust <MAC> && bluetoothctl connect <MAC>
```

The first connection after pairing can fail with `input-hog profile accept failed` in
`journalctl -u bluetooth` and no gamepad device appearing; disconnect and wake it with Home.
To re-map another controller, run `joy_node` and
[tools/joy_probe.py](../ros2_ws/tools/joy_probe.py) and move each control.

Don't run Foxglove's joystick panel in publish mode at the same time - it also publishes
`/joy`.

## Giving it plans (not yet wired up)

"Drive to this point on the map" needs more than a viewer: something has to turn RTAB-Map's
map into a costmap, and something has to plan a path through it and drive the result. Nothing
in this repo does that today — RTAB-Map produces odometry and a map/graph, but nothing
consumes it as a navigation goal.

The standard piece for this is **Nav2** (`nav2_bringup`, a costmap fed from RTAB-Map's
occupancy grid output, plus planner and controller servers). Once that's running, Foxglove's
map panel can click-to-send a goal pose exactly like RViz's "2D Nav Goal" — no new
remote-control mechanism needed, just a consumer for the goal topic on the robot side.

This is a real chunk of new work (costmap tuning, planner/controller parameters, recovery
behaviors), not a config tweak — treat it as its own task rather than folding it into
motor-control or depthai changes.
