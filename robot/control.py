from mecanumCar_v2 import mecanumCar
from ir import ir_loop
from serial_control import serial_loop, send_status
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
_last_reported_fault = None


def _report_chassis_status():
    """Forward mecanumCar's own status to the Pi, once per tick, only on
    change. mecanumCar.set_pwm() already catches its own OSErrors and tracks
    the current fault - this just relays whatever it says, so a tick with
    nothing to do can't be mistaken for a success."""
    global _last_reported_fault

    fault = mecanumCar.status()["fault"]
    if fault == _last_reported_fault:
        return

    if fault is not None:
        print("Fault:", fault)
        send_status("ERR:{}".format(fault))
    else:
        send_status("OK")
    _last_reported_fault = fault


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

    print("Serial line:", line)

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
    ir_command = ir_loop()
    if ir_command is not None:
        _handle_ir(ir_command)

    serial_line = serial_loop()

    if not _ir_active and serial_line is not None:
        _handle_serial_line(serial_line)

    _report_chassis_status()
