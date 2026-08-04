from machine import UART, Pin

uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

buf = b""


def serial_loop():
    """Call every main-loop iteration. Returns the next buffered line (e.g.
    "FWD", "LED:255,0,0") if one is available, else None. Pure signal decode -
    no side effects, no knowledge of the chassis."""
    global buf

    if uart.any():
        buf += uart.read()

    if b"\n" in buf:
        line, buf = buf.split(b"\n", 1)
        return line.decode().strip()

    return None
