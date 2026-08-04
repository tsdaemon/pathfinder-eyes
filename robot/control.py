from mecanumCar_v2 import mecanumCar
from ir import ir_loop
from serial_control import serial_loop
import time

IR_ACTIONS = {
    "Up": mecanumCar.Advance,
    "Down": mecanumCar.Back,
    "Left": mecanumCar.Turn_Left,
    "Right": mecanumCar.Turn_Right,
    "Ok": mecanumCar.stop,
}

SERIAL_ACTIONS = {
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

# While a human is actively driving with the IR remote, serial (ROS/UART) input
# is ignored entirely so the two sources can't fight over the motors. Pressing
# "*" hands control back to serial.
IR_RELEASE_BUTTON = "*"

# Stop if serial goes quiet for a while, so a lost UART link does not leave the
# robot driving into something. Only armed once serial has actually sent a real
# drive command, and only checked while serial is the active source.
SERIAL_TIMEOUT_MS = 1000

_ir_active = False
_last_serial_command_time = None


def _handle_ir(command):
    global _ir_active

    if command == IR_RELEASE_BUTTON:
        _ir_active = False
        return

    _ir_active = True
    action = IR_ACTIONS.get(command)
    if action:
        action()


def _handle_serial_line(line):
    global _last_serial_command_time

    if not line:
        return

    if line.startswith("LED:"):
        r, g, b = (int(v) for v in line[4:].split(","))
        mecanumCar.pixels_fill((r, g, b))
        mecanumCar.pixels_show()
        return

    action = SERIAL_ACTIONS.get(line)
    if action:
        action()
        _last_serial_command_time = time.ticks_ms()
    else:
        print("Unknown command:", line)


def control_loop():
    global _last_serial_command_time

    ir_command = ir_loop()
    if ir_command is not None:
        _handle_ir(ir_command)

    serial_line = serial_loop()

    if _ir_active:
        # IR has control - keep draining serial so it doesn't desync, but
        # don't act on it until "*" releases control.
        return

    if serial_line is not None:
        _handle_serial_line(serial_line)

    if (
        _last_serial_command_time is not None
        and time.ticks_diff(time.ticks_ms(), _last_serial_command_time)
        > SERIAL_TIMEOUT_MS
    ):
        mecanumCar.stop()
        _last_serial_command_time = None
