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
only parses UART0 lines and hands them to `control.py`. If no serial command arrives for 1s
while serial is the active source, `control.py` calls `stop()` — a dead link should not leave
the robot driving blind.

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
