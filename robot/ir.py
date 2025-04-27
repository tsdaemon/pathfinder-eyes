"""
Keyestudio 4WD Mecanum Robot for Pico
lesson 11
IRremote Control Robot
http://www.keyestudio.com
"""

from machine import Pin
from mecanumCar_v2 import mecanumCar
import time


# --- Globals ---
ird = Pin(6, Pin.IN)
ir_state = 0
ir_seq0 = []
ir_seq1 = []
ir_command_ready = False
ir_code_buffer = ""
ir_last_time = 0

# IR decoder dictionary
act = {
    "1": "LLLLLLLLHHHHHHHHLHHLHLLLHLLHLHHH",
    "2": "LLLLLLLLHHHHHHHHHLLHHLLLLHHLLHHH",
    "3": "LLLLLLLLHHHHHHHHHLHHLLLLLHLLHHHH",
    "4": "LLLLLLLLHHHHHHHHLLHHLLLLHHLLHHHH",
    "5": "LLLLLLLLHHHHHHHHLLLHHLLLHHHLLHHH",
    "6": "LLLLLLLLHHHHHHHHLHHHHLHLHLLLLHLH",
    "7": "LLLLLLLLHHHHHHHHLLLHLLLLHHHLHHHH",
    "8": "LLLLLLLLHHHHHHHHLLHHHLLLHHLLLHHH",
    "9": "LLLLLLLLHHHHHHHHLHLHHLHLHLHLLHLH",
    "0": "LLLLLLLLHHHHHHHHLHLLHLHLHLHHLHLH",
    "Up": "LLLLLLLLHHHHHHHHLHHLLLHLHLLHHHLH",
    "Down": "LLLLLLLLHHHHHHHHHLHLHLLLLHLHLHHH",
    "Left": "LLLLLLLLHHHHHHHHLLHLLLHLHHLHHHLH",
    "Right": "LLLLLLLLHHHHHHHHHHLLLLHLLLHHHHLH",
    "Ok": "LLLLLLLLHHHHHHHHLLLLLLHLHHHHHHLH",
    "*": "LLLLLLLLHHHHHHHHLHLLLLHLHLHHHHLH",
    "#": "LLLLLLLLHHHHHHHHLHLHLLHLHLHLHHLH",
}


def ir_loop():
    global ir_state, ir_seq0, ir_seq1, ir_command_ready, ir_code_buffer, ir_last_time

    now = time.ticks_us()

    if ir_state == 0:
        if ird.value() == 0:
            ir_state = 1
            ir_seq0.clear()
            ir_seq1.clear()
            ir_last_time = now

    elif ir_state == 1:
        if ird.value() == 1:
            diff = time.ticks_diff(now, ir_last_time)
            ir_seq0.append(diff)
            ir_last_time = now
            ir_state = 2

    elif ir_state == 2:
        if ird.value() == 0:
            diff = time.ticks_diff(now, ir_last_time)
            if diff > 10000:
                ir_command_ready = True
                ir_state = 0
            else:
                ir_seq1.append(diff)
                ir_last_time = now
                ir_state = 1

    if ir_command_ready:
        decode_ir_command()
        ir_command_ready = False


def decode_ir_command():
    global ir_seq1

    code = ""
    for val in ir_seq1:
        if val < 2000:
            if val < 700:
                code += "L"
            else:
                code += "H"

    command = ""
    for k, v in act.items():
        if code == v:
            command = k
    if command == "":
        command = code

    print(command)

    # Now act
    if command == "Up":
        mecanumCar.Advance()
    elif command == "Down":
        mecanumCar.Back()
    elif command == "Left":
        mecanumCar.Turn_Left()
    elif command == "Right":
        mecanumCar.Turn_Right()
    elif command == "Ok":
        mecanumCar.stop()


def main():
    print("==> IR script started!")
    while True:
        ir_loop()
