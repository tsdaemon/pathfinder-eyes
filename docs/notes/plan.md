# Plan: autonomous navigation

## Next step

Get robot VIO to work: see that it can move through the room in complex motion, and then
return to the same spot.

Status (2026-11-11): in-place spinning works (see [docs/depthai.md](../depthai.md)); driving
while turning is untested. Next, in order:

1. Sort out power: the Pi lost power twice under the new full-rate load.
2. Plot pipeline frequencies in Foxglove (diagnostic values are strings - may need a small
   node republishing them as numbers). Layout with a Foxglove User Script doing the
   conversion is in `foxglove/pathfinder.json` — not yet checked in Studio.
3. Pair the joystick with the Pi over Bluetooth and drive without Foxglove.
4. Keep tuning VIO: arcs and room loops, then the two-lap return-to-start test.
