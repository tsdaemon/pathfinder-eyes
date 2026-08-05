# Wire up motor control

- [x] Pico reflashed to stock MicroPython — was stuck on the old abandoned
      firmware, silently ignoring everything flashed to it. See [docs/pico.md](../pico.md).
- [x] IR remote control debugged and working reliably — receiver wiring/power confirmed, decode
      rewritten to interrupt-driven edge capture (was missing edges under polling), NEC codes
      recaptured for this remote (the old dict's `Up` code was stale).
- [x] Serial vs. IR conflict fixed — both sources were fighting over the motors every loop
      iteration (a stale timeout in `serial_control.py` kept calling `stop()`). Rewritten as
      `robot/control.py`: a single arbitrating control loop, IR takes exclusive control until
      `*` releases it back to serial. See [docs/motor-control.md](../motor-control.md).
- [x] End-to-end motor path confirmed working: I2C → STC8G1K08 driver chip → all 4 wheels,
      driven via IR command (`mecanumCar.Advance()` actually drives the car).

- [x] Continuous-velocity mecanum mixer (`VEL:vx,vy,wz` protocol) — `cmd_vel` magnitude now
      drives wheel PWM via `Driver.drive()`, confirmed working end-to-end through the Foxglove
      Teleop panel. Fully scoped in
      [docs/plans/motor-mixer-and-joystick-control.md](../plans/motor-mixer-and-joystick-control.md)
      Part 1. One tuning note from testing: rotation needs `wz` close to full deflection to
      actually overcome friction and turn (Teleop's default angular scale was too low) — see
      [docs/motor-control.md](../motor-control.md)'s "what's not wired up yet".
- [x] Joystick control (Part 2 of the same plan) — Foxglove's joystick-panel extension → `/joy`
      → `teleop_twist_joy` → `cmd_vel`, confirmed working (forward/back, strafe, and rotate all
      drive correctly). Axis/scale signs and `DRIVE_SPEED` were tuned empirically against the
      actual hardware/extension rather than derived — see
      [docs/remote-control.md](../remote-control.md) and
      [docs/motor-control.md](../motor-control.md)'s "what's not wired up yet" for what's still
      a known limitation (diagonal blending, no minimum-PWM floor).
- [x] `pico_control` and `teleop_joy` registered in `supervisord.conf` — start with the rest of
      the stack now, no longer hand-launched.
