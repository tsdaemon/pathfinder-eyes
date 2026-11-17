#!/usr/bin/env python3
"""Drive the robot from a Steam Deck: send the gamepad state to the Pi over UDP at ~50 Hz.

The Pi side is ros2_ws/udp_joy.py, which publishes it as /joy for teleop_twist_joy.
Layout matches the 8BitDo in ros2_ws/config/teleop_joy.yaml: axis 0/1 = left stick X/Y,
axis 2/3 = right stick X/Y (all positive for left/up), axis 4/5 = RT/LT (1.0 released,
-1.0 fully pressed), axis 6/7 = d-pad; button 6 = LB (hold to drive), 7 = RB (turbo).

Uses SDL's game-controller API (via pygame), so the Deck's own controls and any other pad
SDL knows map the same way. Setup: docs/remote-control.md.

    python drive.py [host]      # default eyes.local
"""

import json
import os
import socket
import sys
import time

# Keep reading the pad while another window (Foxglove) is in front; SDL ignores
# joystick input for unfocused windows by default. Must be set before SDL starts.
os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")

import pygame  # noqa: E402
from pygame._sdl2 import controller  # noqa: E402

PORT = 9010
RATE = 50  # Hz
DEADZONE = 0.08  # Deck sticks rest slightly off-centre
RESOLVE_EVERY = 3.0  # s, re-resolve the host while it can't be found (network switch)

LB, RB = 6, 7


def stick(v):
    v = max(-1.0, min(1.0, v / 32767))
    return 0.0 if abs(v) < DEADZONE else v


def trigger(v):
    return 1.0 - 2.0 * max(0.0, min(1.0, v / 32767))


def read(pad):
    a, b = pad.get_axis, pad.get_button
    axes = [
        -stick(a(pygame.CONTROLLER_AXIS_LEFTX)),
        -stick(a(pygame.CONTROLLER_AXIS_LEFTY)),
        -stick(a(pygame.CONTROLLER_AXIS_RIGHTX)),
        -stick(a(pygame.CONTROLLER_AXIS_RIGHTY)),
        trigger(a(pygame.CONTROLLER_AXIS_TRIGGERRIGHT)),
        trigger(a(pygame.CONTROLLER_AXIS_TRIGGERLEFT)),
        float(b(pygame.CONTROLLER_BUTTON_DPAD_LEFT))
        - float(b(pygame.CONTROLLER_BUTTON_DPAD_RIGHT)),
        float(b(pygame.CONTROLLER_BUTTON_DPAD_UP))
        - float(b(pygame.CONTROLLER_BUTTON_DPAD_DOWN)),
    ]
    buttons = [0] * 24
    buttons[LB] = int(b(pygame.CONTROLLER_BUTTON_LEFTSHOULDER))
    buttons[RB] = int(b(pygame.CONTROLLER_BUTTON_RIGHTSHOULDER))
    return axes, buttons


def open_pad():
    for i in range(controller.get_count()):
        if controller.is_controller(i):
            return controller.Controller(i)
    return None


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "eyes.local"
    pygame.init()
    controller.init()
    screen = pygame.display.set_mode((640, 240))
    pygame.display.set_caption("eyes drive")
    font = pygame.font.Font(None, 32)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    clock = pygame.time.Clock()

    pad, addr, error = None, None, ""
    next_resolve = 0.0
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                return
        if pad is None or not pad.attached():
            pad = open_pad()

        now = time.monotonic()
        if addr is None and now >= next_resolve:
            next_resolve = now + RESOLVE_EVERY
            try:
                addr = (socket.gethostbyname(host), PORT)
                error = ""
            except OSError as e:
                error = f"can't resolve {host}: {e}"

        driving = False
        if pad is not None and addr is not None:
            axes, buttons = read(pad)
            driving = bool(buttons[LB])
            try:
                sock.sendto(
                    json.dumps({"axes": axes, "buttons": buttons}).encode(), addr
                )
            except OSError as e:  # network gone - re-resolve, the IP may change
                error, addr = f"send failed: {e}", None

        lines = [
            f"robot: {host} ({addr[0] if addr else 'not found'})",
            f"pad: {pad.name if pad else 'none'}",
            "DRIVING" if driving else "hold LB to drive, RB for turbo",
            error,
        ]
        screen.fill((20, 20, 20))
        for i, text in enumerate(lines):
            color = (80, 220, 80) if text == "DRIVING" else (220, 220, 220)
            screen.blit(font.render(text, True, color), (20, 20 + i * 50))
        pygame.display.flip()
        clock.tick(RATE)


if __name__ == "__main__":
    main()
