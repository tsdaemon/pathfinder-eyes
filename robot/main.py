from ir import ir_loop
from serial_control import serial_loop


try:
    while True:
        ir_loop()
        serial_loop()
except KeyboardInterrupt:
    print("Interrupted, returning to REPL")
