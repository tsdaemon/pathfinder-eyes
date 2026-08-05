# Pi system configuration

Pieces of Raspberry Pi OS-level setup this project depends on, outside the ROS workspace
(`ros2_ws/`) and the Pico firmware (`robot/`). Nothing here is applied automatically — these
are reference copies and install commands to run by hand when setting up a Pi from scratch or
recovering after an SD card swap (see [docs/tasks/upgrade-after-sd-card.md](../docs/tasks/upgrade-after-sd-card.md)).

## `config.txt`

Not a full replacement — `/boot/firmware/config.txt` ships with many more default sections
than this. This file holds just the four lines added on top of the default, to be merged in
by hand:

```
dtoverlay=disable-bt
dtoverlay=uart0,txd0_pin=14,rxd0_pin=15
enable_uart=1
dtoverlay=dwc2
```

- `dtoverlay=disable-bt` — frees the PL011 UART from Bluetooth (which owns it by default on
  this board) so it's available as a plain UART.
- `dtoverlay=uart0,txd0_pin=14,rxd0_pin=15` + `enable_uart=1` — bring up UART0 on GPIO14/15 as
  `/dev/ttyAMA0`, the link to the Pico. See [docs/motor-control.md](../docs/motor-control.md)
  for the wiring and protocol.
- `dtoverlay=dwc2` — USB OTG gadget mode, used for the USB-C ethernet/power setup (see
  `usb-c-connection.txt` below).

## `cmdline.txt`

Unlike `config.txt`, this one is a full, drop-in replacement for
`/boot/firmware/cmdline.txt` — kernel cmdline is a single line, so there's nothing to merge.
Notably: no `console=serial0,...`, i.e. no login shell on the serial console — required so
`/dev/ttyAMA0` is free for the Pico link instead of being grabbed by a getty. Confirm this
stayed disabled after any fresh install with `systemctl is-enabled serial-getty@ttyAMA0.service`
(should print `disabled`) and `raspi-config nonint get_serial` (should print `1`) while
`get_serial_hw` stays `0` (hardware still enabled, just no login shell on it).

`modules-load=dwc2,g_ether` pairs with `config.txt`'s `dtoverlay=dwc2` for USB-C gadget
ethernet — see `usb-c-connection.txt`.

## Install scripts

Plain `apt install` lists, run by hand, one per concern:

- `install.sh` — base tools (`raspi-config`, `i2c-tools`).
- `install-pico.sh` — `minicom`, `micropython-mpremote` for flashing/talking to the Pico.
- `install-ros.sh` — ROS 2 Jazzy packages this project needs beyond the base install
  (localization, foxglove-bridge, rtabmap, image-pipeline, etc.).
- `install-depthai.sh` — Luxonis DepthAI dependencies + `ros-jazzy-depthai-ros`, for the
  camera (see [docs/depthai.md](../docs/depthai.md)).
- `install-desktop.sh` — for a ground-station machine, not the robot's own Pi: full ROS 2
  desktop + rqt/rviz tooling.

## `usb-c-connection.txt`

Pointer to the guide used for powering the Pi and getting an ethernet link over a single
USB-C cable (Pi5 ethernet-over-USB-C gadget mode).

## Setting up a fresh Pi

1. Flash Raspberry Pi OS, run `install.sh`.
2. Merge `config.txt`'s four lines into `/boot/firmware/config.txt`; copy `cmdline.txt` wholesale
   to `/boot/firmware/cmdline.txt`. Reboot.
3. Run `install-ros.sh`, `install-depthai.sh`, `install-pico.sh` as needed.
4. Follow `usb-c-connection.txt` for the USB-C ethernet/power link.
5. Wire and flash the Pico — see [docs/pico.md](../docs/pico.md) and
   [docs/motor-control.md](../docs/motor-control.md).
