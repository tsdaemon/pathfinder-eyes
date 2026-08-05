# Motor control (Pi ↔ Pico)

## Hardware

- **Keyestudio KS3029 4WD Mecanum Robot for Pico** — 4 independently driven mecanum wheels
  through an STC8G1K08 PWM driver chip on I²C (`0x30`), plus a servo, an HC-SR04 ultrasonic
  sensor, SK6812 addressable LEDs, and an IR receiver, all wired to the Pico.
- **Raspberry Pi Pico**, running MicroPython, flashed from the Pi over USB
  (`/dev/ttyACM0`, shows up as `2e8a:0005`).
- **18650 battery pack** powers the motors and driver board (separate from the Pi's supply).

Vendor driver: [robot/mecanumCar_v2.py](../robot/mecanumCar_v2.py) — mostly Keyestudio's own
code (kept close to original), exposing directional moves (`Advance`, `Back`, `Turn_Left`,
`Turn_Right`, `L_Move`/`R_Move` strafe, four diagonal moves, `drift_left`/`drift_right`),
`stop`, LED control, and ultrasonic distance — these are the discrete moves `ir.py` calls
directly. On top of those, `drive(vx, vy, wz)` is our own addition: a continuous mecanum mix
(see Protocol below) that blends forward/back, strafe, and rotate into per-wheel PWM, instead
of snapping to one discrete move at a fixed speed.

## Wiring: Pi ↔ Pico over UART

Control runs over the Pico's UART0, wired directly to the Pi's UART0 pins — no USB, no extra
board. Three jumper wires, crossed:

| Pi (GPIO header) | Pico |
|---|---|
| GPIO14 (TXD0, pin 8)  | GP1 (UART0 RX) |
| GPIO15 (RXD0, pin 10) | GP0 (UART0 TX) |
| GND                   | GND |

115200 baud, 3.3V logic on both ends (no level shifting needed). On the Pi side this is
`/dev/ttyAMA0`, enabled by the `uart0` overlay in [infra/config.txt](../infra/config.txt) (also disables
Bluetooth, which otherwise owns the PL011 UART on this board). If the old wiring is gone,
this is all it takes to remake it — three female-female Dupont jumpers.

## Protocol

Plain ASCII, one command per line, newline-terminated, no framing/checksum — deliberately as
simple as the link allows:

```
VEL:vx,vy,wz     # each in [-1, 1] - forward/back, strafe, rotate
LED:r,g,b
```

`VEL:0,0,0` is how you stop — there's no separate `STOP` token. `vx`/`vy`/`wz` map straight onto
`Driver.drive()`'s mecanum mix: `fl = vx-vy-wz`, `fr = vx+vy+wz`, `bl = vx+vy-wz`, `br = vx-vy+wz`,
normalized so nothing clips, then scaled to PWM against the `SPEED` ceiling.

Pico side: [robot/control.py](../robot/control.py) owns dispatch and arbitration between the
two input sources (serial and IR, see below); [robot/serial_control.py](../robot/serial_control.py)
only parses UART0 lines and hands them to `control.py`. Serial only ever calls `drive()` —
`ir.py` is still the one calling the discrete moves (`Advance`, `Turn_Left`, etc.) directly.

### Pico → Pi: status/error reporting

The same UART also carries status lines back the other way. `mecanumCar_v2.Driver` owns this:
its `set_pwm()` — the one place that actually talks I2C to the STC8G1K08 — catches `OSError`
(e.g. `ETIMEDOUT`, the classic symptom of the motor driver board's power switch being off)
instead of letting it propagate, and tracks the current fault on `self.fault`. `Driver.status()`
exposes it as `{"fault": None}` or `{"fault": "<exception text>"}` — a dict so it's easy to grow
(e.g. odometry) without changing every caller.

`control.py`'s `control_loop()` reads `mecanumCar.status()` once per tick and forwards it to the
Pi over UART on change:

```
ERR:<exception text>     # e.g. ERR:[Errno 110] ETIMEDOUT
OK                        # sent once, when the fault clears
```

Before this, an `OSError` from a powered-down driver board would propagate out of
`control_loop()` and kill the whole `main.py` loop — both IR and serial would stop being
serviced entirely until the Pico was manually reset. Now the driver simply reports itself
unhealthy and keeps working once power is back, with no reset needed.

`vel_to_serial.py` reads these lines (non-blocking, polled at 20Hz alongside its own writes)
and republishes them as a `diagnostic_msgs/DiagnosticArray` on `/diagnostics`
(`name: pico_motor_driver`, `hardware_id: pico`, `level` ERROR/OK) — visible in Foxglove's
Diagnostics panel like any other robot health status.

ROS side: [vel_to_serial.py](../ros2_ws/src/pico_control/pico_control/vel_to_serial.py)
subscribes to `cmd_vel` (`geometry_msgs/Twist`) and normalizes `linear.x`/`linear.y`/
`angular.z` directly into `[-1, 1]` by dividing by the `max_linear_speed`/`max_angular_speed`
ROS params (defaults 0.5 m/s, 1.5 rad/s — tune to taste). A 20Hz timer sends the latest values
as `VEL:vx,vy,wz`, deduped against the last-sent tuple so a steady `cmd_vel` doesn't spam the
UART with identical lines. There's no silence-based auto-stop on either end anymore (the
Pico-side one was dropped earlier as unnecessary complexity, and the ROS-side one was pulsing
motion to zero whenever Foxglove's Teleop panel didn't publish a perfectly steady stream) — the
robot now simply keeps doing whatever it was last told until a new command arrives. Launch
with:

```bash
cd ros2_ws && python launch_pico_control.py     # needs /dev/ttyAMA0 and a flashed Pico
```

This isn't in `supervisord.conf` yet, so it doesn't start with the rest of the stack — see
[docs/supervisord.md](supervisord.md) for the process list.

## What's not wired up yet

- No wheel odometry — nothing reports actual motion back to ROS. `Driver.status()` is already
  shaped to grow a field for this once it exists (see status/error reporting above).
- The `SPEED` PWM ceiling is still a single tuned constant, not something `drive()` varies per
  call — full-scale `vx`/`vy`/`wz` all drive at the same top speed there's no separate
  fine/coarse gear.
- The discrete diagonal/drift moves (`LU_Move`, `drift_left`, etc.) and IR's discrete moves are
  no longer reachable from serial at all now that the protocol is `VEL:`/`LED:` only — true
  diagonal motion happens instead as a natural side effect of the continuous mixer (nonzero
  `vx` and `vy` together), not via those preset methods. They're still there for `ir.py`/REPL
  use, just not part of the wire protocol.
- The IR remote ([robot/ir.py](../robot/ir.py)) works as an independent, ROS-free fallback
  control path, decoded straight from the receiver pin. `control.py` arbitrates between it and
  serial: any IR button press takes exclusive control (serial input is still read so it doesn't
  desync, but ignored) until the `*` button releases control back to serial.
