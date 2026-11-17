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
VO's features over the camera image: Image panel on `/oakd/right/image_rect/compressed`,
settings → Annotations → enable `/vo_features` (green = inliers, yellow = matched but rejected, plus counts; from
[vo_features.py](../ros2_ws/vo_features.py)).

## Manual driving today

Foxglove's **Teleop panel** publishes `geometry_msgs/Twist` directly to `cmd_vel`, which
[vel_to_serial](motor-control.md) already consumes and turns into wheel commands. This works
right now with no additional stack — it's the cheapest option and good enough for
driving-around testing.

**Steam Deck (main way to drive):** [deck/drive.py](../deck/drive.py) reads the Deck's
controls and sends them over Wi-Fi (UDP port 9010, ~50 Hz) to `eyes.local`.
[udp_joy.py](../ros2_ws/udp_joy.py) on the Pi publishes them as `/joy`, and
`teleop_twist_joy` turns that into `/cmd_vel`; both run in the `teleop_joy` supervisord
program ([launch_teleop_joy.py](../ros2_ws/launch_teleop_joy.py)). Hold **LB** to drive,
**RB** for turbo; left stick = drive and strafe, right stick X = turn. Mapping in
[config/teleop_joy.yaml](../ros2_ws/config/teleop_joy.yaml). If packets stop for 0.3 s the
bridge releases everything and the robot stops.

Setup on the Deck (Desktop Mode, Konsole), once:

```bash
git clone <this repo> ~/eyes          # or copy the deck/ folder
python -m venv ~/eyes-drive && ~/eyes-drive/bin/pip install pygame
~/eyes/deck/drive.sh                  # test: window shows robot IP and pad name
```

For Game Mode: Steam → Add a Non-Steam Game → browse to `~/eyes/deck/drive.sh`; keep the
default Gamepad controller layout. Pass another host as an argument if `eyes.local` doesn't
resolve (e.g. on a hotspot): `drive.sh 192.168.x.y`.

Control station: run Foxglove on the Deck (camera, diagnostics, map - see the layout above)
next to `drive.py`. Driving deliberately stays on its own UDP channel instead of Foxglove's
websocket (TCP: after a Wi-Fi hiccup it delivers stale inputs late), and `drive.py` keeps
reading the pad while Foxglove has focus. Not yet checked on the Deck: how Foxglove installs
on SteamOS, and whether Steam Input's desktop layout (trackpad mouse, etc.) gets in the way
when both run in Desktop Mode - launching `drive.sh` through Steam applies a Gamepad layout.

Network: the Deck and the Pi only need the same Wi-Fi. Away from home, start a hotspot whose
SSID/password the Pi already knows (`nmcli connection show` on the Pi lists them). Use
5 GHz where possible: the camera's USB 3 traffic interferes with 2.4 GHz next to the Pi.

**Bluetooth gamepad (dropped 2026-11-17):** an 8BitDo paired to the Pi lagged and replayed
inputs late. To use one anyway, swap `udp_joy.py` for `joy_node` in
[launch_teleop_joy.py](../ros2_ws/launch_teleop_joy.py); pair with
`bluetoothctl pair/trust/connect <MAC>`, map with
[tools/joy_probe.py](../ros2_ws/tools/joy_probe.py). Only one `/joy` source at a time -
that includes Foxglove's joystick panel in publish mode.

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
