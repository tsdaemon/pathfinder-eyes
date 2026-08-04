from machine import Pin
import time

p = Pin(6, Pin.IN)


def handler(pin):
    print(time.ticks_us())


p.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=handler)

print("IR pin monitor started - point remote and press buttons")
while True:
    time.sleep(1)
