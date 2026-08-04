"""
Keyestudio 4WD Mecanum Robot for Pico
lesson 11
IRremote Control Robot
http://www.keyestudio.com
"""

from machine import Pin, disable_irq, enable_irq
import time


# --- Globals ---
ird = Pin(6, Pin.IN)

_MAX_EDGES = 140  # NEC frame is ~67 edges; ample margin, bounds worst-case noise growth
_FRAME_GAP_US = 15000  # longer than the 9ms leader mark
_edges = []


def _ir_edge(pin):
    if len(_edges) < _MAX_EDGES:
        _edges.append(time.ticks_us())


ird.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=_ir_edge)

# IR decoder dictionary: NEC code -> button
act = {
    "LLLLLLLLHHHHHHHHLHHLHLLLHLLHLHHH": "1",
    "LLLLLLLLHHHHHHHHHLLHHLLLLHHLLHHH": "2",
    "LLLLLLLLHHHHHHHHHLHHLLLLLHLLHHHH": "3",
    "LLLLLLLLHHHHHHHHLLHHLLLLHHLLHHHH": "4",
    "LLLLLLLLHHHHHHHHLLLHHLLLHHHLLHHH": "5",
    "LLLLLLLLHHHHHHHHLHHHHLHLHLLLLHLH": "6",
    "LLLLLLLLHHHHHHHHLLLHLLLLHHHLHHHH": "7",
    "LLLLLLLLHHHHHHHHLLHHHLLLHHLLLHHH": "8",
    "LLLLLLLLHHHHHHHHLHLHHLHLHLHLLHLH": "9",
    "LLLLLLLLHHHHHHHHLHLLHLHLHLHHLHLH": "0",
    "LLLLLLLLHHHHHHHHLHHLLLHLHLLHHHLH": "Up",
    "LLLLLLLLHHHHHHHHHLHLHLLLLHLHLHHH": "Down",
    "LLLLLLLLHHHHHHHHLLHLLLHLHHLHHHLH": "Left",
    "LLLLLLLLHHHHHHHHHHLLLLHLLLHHHHLH": "Right",
    "LLLLLLLLHHHHHHHHLLLLLLHLHHHHHHLH": "Ok",
    "LLLLLLLLHHHHHHHHLHLLLLHLHLHHHHLH": "*",
    "LLLLLLLLHHHHHHHHLHLHLLHLHLHLHHLH": "#",
}


def ir_loop():
    """Call every main-loop iteration. Returns a decoded button string (e.g.
    "Up", "*") if a new IR frame just completed and matched a known code, else
    None. Pure signal decode - no side effects, no knowledge of the chassis."""
    if _edges and time.ticks_diff(time.ticks_us(), _edges[-1]) > _FRAME_GAP_US:
        state = disable_irq()
        edges = _edges[:]
        _edges.clear()
        enable_irq(state)
        if len(edges) >= 10:
            return decode_ir_command(edges)
    return None


def decode_ir_command(edges):
    # diffs alternate mark, space, mark, space, ... starting with the leader mark
    # (diffs[0]) and leader space (diffs[1]) - skip those two, then each remaining
    # pair (mark_i, space_i) sums to one bit's full period: ~1.12ms = "0", ~2.25ms = "1".
    diffs = [time.ticks_diff(edges[i + 1], edges[i]) for i in range(len(edges) - 1)]
    bit_diffs = diffs[2:]
    periods = [bit_diffs[i] + bit_diffs[i + 1] for i in range(0, len(bit_diffs) - 1, 2)]

    code = ""
    for val in periods:
        if val < 3000:
            code += "L" if val < 1600 else "H"

    command = act.get(code)
    if not command:
        print("IR: unrecognized code", code)
        return None

    print("IR:", command)
    return command
