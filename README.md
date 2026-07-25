# Pathfinder Eyes

Visual SLAM rover: a Raspberry Pi 5 running ROS 2 Jazzy drives a Luxonis OAK-D S2 camera into
RTAB-Map for odometry and mapping, with a Raspberry Pi Pico driving a 4WD mecanum chassis over
UART. Everything runs under `supervisord`, health-reported to ROS `/diagnostics`, and streamed
to a ground station via `foxglove_bridge`.

Docs, by topic:

- [docs/depthai.md](docs/depthai.md) — camera, RTAB-Map pipeline, calibration history
- [docs/supervisord.md](docs/supervisord.md) — process supervision, health bridge, watchdog
- [docs/motor-control.md](docs/motor-control.md) — Pico wiring, protocol, firmware
- [docs/remote_control.md](docs/remote_control.md) — visualization, driving, and planning from a laptop
- [docs/notes/](docs/notes/) — dated engineering journal

## Hardware

| Part | Notes |
|---|---|
| Raspberry Pi 5, Ubuntu 24.04 | hostname `eyes`, reachable as `eyes.local` over mDNS |
| Luxonis OAK-D S2 + powered USB hub | hub is required, see [docs/depthai.md](docs/depthai.md) |
| Keyestudio KS3029 4WD Mecanum Robot for Pico | chassis + Pico, see [docs/motor-control.md](docs/motor-control.md) |
| 18650 battery pack | motors + driver board |
| Power bank | Pi + hub |

## Setting up a new Pi

```bash
# Boot config — copy onto the boot partition (enables camera UART, disables Bluetooth)
cp config.txt cmdline.txt /boot/firmware/

# System + ROS packages
infra/install.sh
infra/install-ros.sh
infra/install-depthai.sh
infra/install-pico.sh

# Python venv
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

# Build the custom ROS packages
cd ros2_ws
source /opt/ros/jazzy/setup.bash
make build
```

On a ground station (for RViz/Foxglove/rqt instead of headless): `infra/install-desktop.sh`.

## Running

```bash
cd ros2_ws
./run.sh             # starts supervisord + the whole stack in the foreground
./stop.sh             # stops it
supervisorctl -c supervisord.conf status
```

Connect Foxglove Studio to `ws://eyes.local:8765` for live camera/map/diagnostics, and for
driving — see [docs/remote_control.md](docs/remote_control.md).

Motor control is not yet part of the supervised stack — see
[docs/motor-control.md](docs/motor-control.md) for wiring, flashing the Pico, and running it
by hand.
