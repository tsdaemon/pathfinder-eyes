# Plan: autonomous navigation in the apartment

Goal: the robot accepts a goal pose (or waypoints) and drives there on its own, avoiding
furniture, using the existing OAK-D/RTAB-Map stack for mapping/localization and Nav2 for
planning and control. Today it only does manual teleop
(see [docs/remote_control.md](../remote_control.md)) — this is what closes the gap to "give it
plans."

## Fix first

1. **TF tree conflict** — [docs/depthai.md](../depthai.md#known-issue-tf-tree). Nav2 will not
   tolerate one frame with two parents; this has to be resolved before anything else here.
2. **RTAB-Map occupancy grid** — confirm it's actually publishing a usable `/map`
   (`Grid/...` params aren't currently set in [ros2_ws/config.py](../../ros2_ws/config.py)).
   That grid is the natural static costmap layer; if it's not there, Nav2 has no map to plan
   against.
3. **Continuous velocity control** — [docs/motor-control.md](../motor-control.md) documents
   `vel_to_serial` collapsing everything to 6 fixed-speed direction commands. A path-following
   controller needs real linear x/y + angular z, not discrete directions — this needs a
   mecanum inverse-kinematics mixer on the Pico side before Nav2's output would drive well.

## What to learn

- Nav2 architecture: costmap layers (static/obstacle/inflation), planner server, controller
  server, `bt_navigator`, lifecycle management.
- Holonomic navigation — most Nav2 tutorials assume differential drive. A mecanum base needs
  a controller plugin that actually uses the extra degree of freedom (e.g. `nav2_mppi_controller`
  supports omnidirectional motion) rather than one that ignores strafe.
- Turning OAK-D depth into a costmap obstacle source: RTAB-Map's own grid output vs.
  `depthimage_to_laserscan` into a virtual 2D scan.
- RTAB-Map localization mode (running against a previously saved map, not remapping every
  run) vs. the mapping mode used today.
- Mecanum forward/inverse kinematics, needed either way to build the velocity mixer above.

## Do & test, in order

1. Map the apartment once, carefully, at walking pace; confirm loop closures hold and the map
   doesn't drift room to room. Save the RTAB-Map database.
2. Switch RTAB-Map to localization mode against that saved map; confirm it can localize
   standing still and while being carried around by hand.
3. Replace the discrete command protocol with continuous velocity control end to end
   (`vel_to_serial` → new line protocol → mecanum mixer on the Pico). Test with
   `ros2 topic pub` sweeps before connecting anything else to it.
4. Bring up `nav2_bringup` with a minimal config: static layer from the saved map, obstacle
   layer from the depth-derived scan, an omnidirectional-capable controller. Send goals with
   `ros2 topic pub /goal_pose` first — no Foxglove yet.
5. Test in the apartment incrementally: open room → corridor → doorway → multi-room route.
   Stay next to a kill switch (Ctrl-C `pico_control`) — it will confidently drive into things
   while costmap/controller params are still being tuned.
6. Wire Foxglove's goal-pose panel to `/goal_pose` for click-to-navigate
   ([docs/remote_control.md](../remote_control.md)).
7. Tune recovery behaviors and inflation radius based on where it actually gets stuck.

## What to write

- `docs/navigation.md` once something works: architecture, where the Nav2 params file lives,
  how to save/load a map, how to send a goal.
- Update [docs/motor-control.md](../motor-control.md) once the discrete protocol is replaced —
  retire the old command list, document the new one.
- A `config.py`/`supervisord.conf` entry for Nav2, same pattern as the existing RTAB-Map/depthai config.
- A dated entry alongside this plan after each real test run in the apartment — what broke,
  what worked — same journal style as the rest of the project.

## Open questions

- Does RTAB-Map's own grid output suffice as the Nav2 static layer, or is a separate
  conversion step needed?
- Can the Pi 5 run RTAB-Map + Nav2 + scan conversion at once, or does part of this need to
  move to a desktop? Costmap traffic is much lighter than raw camera streams (unlike the
  earlier remote-desktop attempts in [docs/remote_control.md](../remote_control.md)), so this
  is worth measuring rather than assuming either way.
- Controller plugin choice for the mecanum base — MPPI vs. a custom mixer over a standard
  controller.
