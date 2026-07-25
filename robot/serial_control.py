from machine import UART, Pin
from mecanumCar_v2 import mecanumCar
import time

uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

COMMANDS = {
    "FWD": mecanumCar.Advance,
    "BACK": mecanumCar.Back,
    "LEFT": mecanumCar.Turn_Left,
    "RIGHT": mecanumCar.Turn_Right,
    "STOP": mecanumCar.stop,
    "STRAFE_L": mecanumCar.L_Move,
    "STRAFE_R": mecanumCar.R_Move,
    "DIAG_LU": mecanumCar.LU_Move,
    "DIAG_LD": mecanumCar.LD_Move,
    "DIAG_RU": mecanumCar.RU_Move,
    "DIAG_RD": mecanumCar.RD_Move,
    "DRIFT_L": mecanumCar.drift_left,
    "DRIFT_R": mecanumCar.drift_right,
}

# Stop if nothing arrives for a while, so a lost UART link does not leave the
# robot driving into something.
COMMAND_TIMEOUT_MS = 1000

buf = b""
last_command_time = time.ticks_ms()


def handle_line(line):
    global last_command_time

    if not line:
        return

    if line.startswith("LED:"):
        r, g, b = (int(v) for v in line[4:].split(","))
        mecanumCar.pixels_fill((r, g, b))
        mecanumCar.pixels_show()
        return

    action = COMMANDS.get(line)
    if action:
        action()
        last_command_time = time.ticks_ms()
    else:
        print("Unknown command:", line)


def serial_loop():
    global buf, last_command_time

    if uart.any():
        buf += uart.read()
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            handle_line(line.decode().strip())

    if time.ticks_diff(time.ticks_ms(), last_command_time) > COMMAND_TIMEOUT_MS:
        mecanumCar.stop()


def main():
    print("==> Serial control started!")
    while True:
        serial_loop()
