from machine import UART, Pin

from mecanumCar_v2 import mecanumCar
import time
import struct

# --- Initialize UART ---
uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

# --- MAVLink constants ---
MAVLINK_STX_V2 = 0xFD

# MAVLink minimal message ID mapping
MAV_CMD_MOVE = 200  # Custom command for movement
MAV_CMD_LED = 201  # Custom command for LED control
MAVLINK_MSG_ID_HEARTBEAT = 0

# Movement directions mapping
MOVE_FORWARD = 1
MOVE_BACKWARD = 2
TURN_LEFT = 3
TURN_RIGHT = 4
STOP = 5
MOVE_LEFT = 6
MOVE_RIGHT = 7
MOVE_LEFT_UP = 8
MOVE_LEFT_DOWN = 9
MOVE_RIGHT_UP = 10
MOVE_RIGHT_DOWN = 11
DRIFT_LEFT = 12
DRIFT_RIGHT = 13

# --- Initialize globals ---
buf = bytearray()
heartbeat_timer = time.ticks_ms()

# --- Functions ---


def send_heartbeat():
    pass


def handle_mavlink_message(msg_id, payload):
    if msg_id == 76:  # COMMAND_LONG
        if len(payload) < 30:  # minimum fields to safely decode command
            print("Payload too small!")
            return
        else:
            # Safely unpack only needed fields first
            param1 = struct.unpack("<f", payload[0:4])[0]
            command = struct.unpack("<H", payload[28:30])[0]

            print("param1 =", param1)
            print("command =", command)

        if command == MAV_CMD_MOVE:
            direction = param1
            if direction == MOVE_FORWARD:
                mecanumCar.Advance()
            elif direction == MOVE_BACKWARD:
                mecanumCar.Back()
            elif direction == TURN_LEFT:
                mecanumCar.Turn_Left()
            elif direction == TURN_RIGHT:
                mecanumCar.Turn_Right()
            elif direction == STOP:
                mecanumCar.stop()
            elif direction == MOVE_LEFT:
                mecanumCar.L_Move()
            elif direction == MOVE_RIGHT:
                mecanumCar.R_Move()
            elif direction == MOVE_LEFT_UP:
                mecanumCar.LU_Move()
            elif direction == MOVE_LEFT_DOWN:
                mecanumCar.LD_Move()
            elif direction == MOVE_RIGHT_UP:
                mecanumCar.RU_Move()
            elif direction == MOVE_RIGHT_DOWN:
                mecanumCar.RD_Move()
            elif direction == DRIFT_LEFT:
                mecanumCar.drift_left()
            elif direction == DRIFT_RIGHT:
                mecanumCar.drift_right()

        elif command == MAV_CMD_LED:
            r, g, b = payload[0], payload[1], payload[2]
            mecanumCar.pixels_fill((r, g, b))
            mecanumCar.pixels_show()


def parse_mavlink_packet(buf):
    if len(buf) < 12:
        return None

    # Parse MAVLink v2 header
    (
        stx,
        payload_len,
        incompat_flags,
        compat_flags,
        seq,
        sysid,
        compid,
        msgid1,
        msgid2,
        msgid3,
    ) = struct.unpack("<BBBBBBBBBB", buf[:10])

    if stx != MAVLINK_STX_V2:
        print("Invalid MAVLink packet")
        return None

    msg_id = msgid1 | (msgid2 << 8) | (msgid3 << 16)
    payload = buf[10 : 10 + payload_len]

    return (msg_id, payload)


def mavlink_loop():
    global buf, heartbeat_timer

    if uart.any():
        ch = uart.read(1)
        if ch:
            buf.append(ch[0])

            if len(buf) >= 10:
                payload_len = buf[1]
                total_len = 10 + payload_len + 2  # header + payload + checksum

                if len(buf) >= total_len:
                    packet = buf[:total_len]
                    buf = buf[total_len:]

                    parsed = parse_mavlink_packet(packet)
                    print(f"Parsed mavlink packet: {parsed}")
                    if parsed:
                        msg_id, payload = parsed
                        handle_mavlink_message(msg_id, payload)

    if time.ticks_diff(time.ticks_ms(), heartbeat_timer) > 1000:
        send_heartbeat()
        heartbeat_timer = time.ticks_ms()


def main():
    print("==> MAVLink script started!")
    while True:
        mavlink_loop()
