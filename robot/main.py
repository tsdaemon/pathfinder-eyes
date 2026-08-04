from control import control_loop


try:
    while True:
        control_loop()
except KeyboardInterrupt:
    print("Interrupted, returning to REPL")
