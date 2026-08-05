from mecanumCar_v2 import mecanumCar
from ir import ir_loop
from serial_control import serial_loop, send_status

IR_ACTIONS = {
    "Up": mecanumCar.Advance,
    "Down": mecanumCar.Back,
    "Left": mecanumCar.Turn_Left,
    "Right": mecanumCar.Turn_Right,
    "Ok": mecanumCar.stop,
}

# While a human is actively driving with the IR remote, serial (ROS/UART) input
# is ignored entirely so the two sources can't fight over the motors. Pressing
# "*" hands control back to serial.
IR_RELEASE_BUTTON = "*"

_ir_active = False
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
    print("Serial line:", line)

    if not line:
        return

    if line.startswith("LED:"):
        r, g, b = (int(v) for v in line[4:].split(","))
        mecanumCar.pixels_fill((r, g, b))
        mecanumCar.pixels_show()
        return

    if line.startswith("VEL:"):
        vx, vy, wz = (float(v) for v in line[4:].split(","))
        mecanumCar.drive(vx, vy, wz)
        return

    print("Unknown command:", line)


def control_loop():
    ir_command = ir_loop()
    if ir_command is not None:
        _handle_ir(ir_command)

    serial_line = serial_loop()

    if not _ir_active and serial_line is not None:
        _handle_serial_line(serial_line)

    _report_chassis_status()
