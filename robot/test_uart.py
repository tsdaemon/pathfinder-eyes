from machine import UART, Pin
import time

uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

while True:
    uart.write(b"Hello from Pico!\n")
    time.sleep(1)
