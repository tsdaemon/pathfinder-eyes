# Pico hardware/firmware status

Everything about the physical Pico board itself — how to flash it, board identity, and
debugging journal for known issues getting in the way of running `robot/`'s own code. For the
wiring/protocol this firmware implements once the board is in a known-good state, see
[docs/motor-control.md](motor-control.md).

## Flashing

```bash
cd robot
make flash          # mpremote fs cp *.py : && reset
make repl           # interactive REPL
```

Port comes from [.env](../.env) (`PORT=/dev/ttyACM0`).

## Board identity

**Raspberry Pi Pico 2 W** (RP2350, with WiFi)

## Resetting to stock MicroPython

Reflashing means putting the RP2350 into its USB mass-storage bootloader (BOOTSEL mode) and
dragging a firmware image onto it — a different mechanism from `make flash`, which only writes
files to the filesystem of whatever firmware is already running and can't override a firmware
image like `zmyi-control` that never hands off to a filesystem `main.py`.

1. Download the Pico 2 W MicroPython UF2:
   https://micropython.org/download/RPI_PICO2_W/
2. **Cut all power to the board first**: unplug the USB cable, and flip off the driver board's
   power switch (disconnects the 18650 pack from VSYS).
3. Hold down **BOOTSEL**.
4. Plug the USB cable back in (now the only power source) while still holding BOOTSEL.
5. Wait ~2 seconds, then release BOOTSEL. Check status with `ls /mnt`: should come up with `pico`
6. Copy the downloaded `.uf2` onto that drive. It flashes itself and reboots automatically.
7. Confirm with `mpremote connect $(PORT) repl` — should show a plain MicroPython REPL banner.

## Testing the UART link manually

To check the Pi↔Pico UART wiring (see [docs/motor-control.md](motor-control.md)) without
involving ROS, read/write `/dev/ttyAMA0` directly from the Pi:

```bash
cd robot && make test-uart
stty -F /dev/ttyAMA0 115200 raw -echo   # only needed before plain `cat`, see below
cat /dev/ttyAMA0
```

This should show you a repeating message "Hello from Pico!".

The `stty` call is only needed because `cat` doesn't configure the port itself — it just
reads whatever framing the port happens to be left in. `vel_to_serial.py` (the actual ROS
node that talks to the Pico) opens the port with pyserial, which sets baud rate, raw mode,
and no-echo itself at open time, so the ROS pipeline works regardless of `stty` state; this
is purely a convenience step for manual testing, not something that needs to persist across
reboots.
