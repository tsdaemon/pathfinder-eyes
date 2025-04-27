from ir import ir_loop
from mavlink import mavlink_loop


try:
    while True:
        ir_loop()
        mavlink_loop()
except KeyboardInterrupt:
    print("Interrupted, returning to REPL")
