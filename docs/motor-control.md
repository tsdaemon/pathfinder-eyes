# Motor control (Pi ↔ Pico)

## Hardware

- **Keyestudio KS3029 4WD Mecanum Robot for Pico** — 4 independently driven mecanum wheels
  through an STC8G1K08 PWM driver chip on I²C (`0x30`), plus a servo, an HC-SR04 ultrasonic
  sensor, SK6812 addressable LEDs, and an IR receiver, all wired to the Pico.
- **Raspberry Pi Pico**, running MicroPython, flashed from the Pi over USB
  (`/dev/ttyACM0`, shows up as `2e8a:0005`).
- **18650 battery pack** powers the motors and driver board (separate from the Pi's supply).

Vendor driver: [robot/mecanumCar_v2.py](../robot/mecanumCar_v2.py) — this is Keyestudio's own
code (kept close to original), exposing directional moves (`Advance`, `Back`, `Turn_Left`,
`Turn_Right`, `L_Move`/`R_Move` strafe, four diagonal moves, `drift_left`/`drift_right`),
`stop`, LED control, servo angle, and ultrasonic distance.

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
FWD | BACK | LEFT | RIGHT | STOP
STRAFE_L | STRAFE_R
DIAG_LU | DIAG_LD | DIAG_RU | DIAG_RD
DRIFT_L | DRIFT_R
LED:r,g,b
```

Pico side: [robot/control.py](../robot/control.py) owns dispatch and arbitration between the
two input sources (serial and IR, see below); [robot/serial_control.py](../robot/serial_control.py)
only parses UART0 lines and hands them to `control.py`.

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
subscribes to `cmd_vel` (`geometry_msgs/Twist`) and picks the closest matching command from
`linear.x`/`linear.y`/`angular.z` (rotation wins if it dominates, otherwise forward/back vs.
strafe by whichever component is larger; ±0.1 deadzone). It re-sends `STOP` if no `cmd_vel`
message has arrived in the last 0.5s — the same safety idea, enforced from both ends. Launch
with:

```bash
cd ros2_ws && python launch_pico_control.py     # needs /dev/ttyAMA0 and a flashed Pico
```

This isn't in `supervisord.conf` yet, so it doesn't start with the rest of the stack — see
[docs/supervisord.md](supervisord.md) for the process list.

## What's not wired up yet

- Speed is a fixed constant on the Pico (`SPEED = 60` in `mecanumCar_v2.py`) — `cmd_vel`
  magnitude is currently ignored, only direction matters.
- No wheel odometry — nothing reports actual motion back to ROS.
- The diagonal/drift moves and LED command are implemented on both ends but nothing today
  generates `cmd_vel` values that would trigger them (the mapping only ever emits the 6 axis
  directions).
- The IR remote ([robot/ir.py](../robot/ir.py)) works as an independent, ROS-free fallback
  control path, decoded straight from the receiver pin. `control.py` arbitrates between it and
  serial: any IR button press takes exclusive control (serial input is still read so it doesn't
  desync, but ignored) until the `*` button releases control back to serial.
