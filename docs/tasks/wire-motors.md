# Wire up motor control

- [x] Pico reflashed to stock MicroPython — was stuck on the old abandoned `zmyi-control`
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

- [ ] Continuous-velocity mecanum mixer (`VEL:vx,vy,wz` protocol) — `cmd_vel` magnitude is
      still ignored, only direction matters. This is the actual "teach the robot to move" step.
      Fully scoped in [docs/plans/motor-mixer-and-joystick-control.md](../plans/motor-mixer-and-joystick-control.md)
      Part 1, not yet implemented.
- [ ] Joystick control (Part 2 of the same plan).
- [ ] `pico_control` (and eventually a joystick launch) registered in `supervisord.conf` —
      still hand-launched.
