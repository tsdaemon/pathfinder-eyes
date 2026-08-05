"""
STC8G1K0B PWM OUT
WS2812
colorfur light
FOR KEYES MECANUMCAR_V2(RASPBERRY PI PICO)
2022/7/1
DengFei
www.keyestudio.com
"""
from machine import Pin, time_pulse_us, I2C
import array
import time
import rp2

SPEED = 60

# Separate, higher ceiling for drive()'s continuous mix, decoupled from SPEED (which the
# vendor discrete moves use). Turning/strafing scrub the wheels sideways against the floor and
# need more torque to overcome friction than rolling forward does - SPEED=60 wasn't enough for
# either, even at full deflection (which reduces to the same wheel commands as Turn_Left()/
# L_Move() - not a mixer-specific bug). Tune by feel; keep it decoupled from SPEED so
# IR's already-working forward speed doesn't change while this gets retuned.
DRIVE_SPEED = 100


trigger = Pin(3, Pin.OUT)
echo = Pin(4, Pin.IN)


@rp2.asm_pio(
    sideset_init=rp2.PIO.OUT_LOW,
    out_shiftdir=rp2.PIO.SHIFT_LEFT,
    autopull=True,
    pull_thresh=24,
)
def sk6812():
    # ruff: noqa
    # This is a PIO (Programmable I/O) assembly program for driving SK6812/WS2812 addressable RGB LEDs
    # It uses precise timing to generate the signal protocol required by these LEDs
    # The timing constants T1, T2, T3 define the pulse widths for the protocol
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1).side(0)[T3 - 1]  # Output 1 bit and set side pin low with delay
    jmp(not_x, "do_zero").side(1)[T1 - 1]  # Jump based on bit value with side pin high
    jmp("bitloop").side(1)[T2 - 1]  # Continue loop with side pin high (for "1" bit)
    label("do_zero")
    nop().side(0)[T2 - 1]  # No operation with side pin low (for "0" bit)
    wrap()


# Create the StateMachine with the sk6812 program, outputting on Pin(7).
sm = rp2.StateMachine(0, sk6812, freq=8_000_000, sideset_base=Pin(7))

# Start the StateMachine, it will wait for data on its FIFO.
sm.active(1)


# Configure the number of sk6812 LEDs.
NUM_LEDS = 4
# Display a pattern on the LEDs via an array of LED RGB values.
ar = array.array("I", [0 for _ in range(NUM_LEDS)])


class Driver(object):
    """Driver for the STC8G1K08"""

    def __init__(self, i2c, addr=0x30):
        self.i2c = i2c
        self.addr = addr
        self.brightness = 0.1
        self.speed_Upper_L = SPEED
        self.speed_Lower_L = SPEED
        self.speed_Upper_R = SPEED
        self.speed_Lower_R = SPEED
        self.fault = None
        time.sleep(1)

    def status(self):
        """Current chassis health as reported by the driver itself - the one
        place that actually talks I2C to the STC8G1K08, so it's the one place
        that knows whether it's working. A dict so it's easy to grow (e.g.
        odometry) without changing every caller.
        """
        return {"fault": self.fault}

    # Set LED brightness
    def set_brightness(self, brightness=None):
        if brightness is None:
            return self.brightness
        self.brightness = brightness
        self.pixels_show()

    # Refresh LED display
    def pixels_show(self):
        dimmer_ar = array.array("I", [0 for _ in range(NUM_LEDS)])
        for i, c in enumerate(ar):
            r = int(((c >> 8) & 0xFF) * self.brightness)
            g = int(((c >> 16) & 0xFF) * self.brightness)
            b = int((c & 0xFF) * self.brightness)
            dimmer_ar[i] = (g << 16) + (r << 8) + b
        sm.put(dimmer_ar, 8)
        time.sleep_ms(10)

    # Set a specific LED
    def pixels_set(self, i, color):
        ar[i] = (color[1] << 16) + (color[0] << 8) + color[2]

    # Set all 4 LEDs
    def pixels_fill(self, color):
        for i in range(len(ar)):
            self.pixels_set(i, color)

    # Set speed
    def set_speed(
        self,
        speed_Upper_L=None,
        speed_Lower_L=None,
        speed_Upper_R=None,
        speed_Lower_R=None,
    ):
        if speed_Upper_L is None:
            pass
        else:
            self.speed_Upper_L = speed_Upper_L

        if speed_Lower_L is None:
            pass
        else:
            self.speed_Lower_L = speed_Lower_L

        if speed_Upper_R is None:
            pass
        else:
            self.speed_Upper_R = speed_Upper_R

        if speed_Lower_R is None:
            pass
        else:
            self.speed_Lower_R = speed_Lower_R

    # Continuous mecanum mix: blend forward/back (vx), strafe (vy), and
    # rotate (wz), each in [-1, 1], into per-wheel PWM. Alongside, not
    # replacing, the discrete moves below - ir.py calls those directly.
    def drive(self, vx, vy, wz):
        fl = vx - vy - wz
        fr = vx + vy + wz
        bl = vx + vy - wz
        br = vx - vy + wz

        largest = max(abs(fl), abs(fr), abs(bl), abs(br))
        if largest > 1:
            fl /= largest
            fr /= largest
            bl /= largest
            br /= largest

        self.Motor_Upper_L(1 if fl >= 0 else 0, round(abs(fl) * DRIVE_SPEED))
        self.Motor_Upper_R(1 if fr >= 0 else 0, round(abs(fr) * DRIVE_SPEED))
        self.Motor_Lower_L(1 if bl >= 0 else 0, round(abs(bl) * DRIVE_SPEED))
        self.Motor_Lower_R(1 if br >= 0 else 0, round(abs(br) * DRIVE_SPEED))

    # Stop
    def stop(self):
        self.Motor_Upper_L(0, 0)
        self.Motor_Lower_L(0, 0)
        self.Motor_Upper_R(0, 0)
        self.Motor_Lower_R(0, 0)

    # Forward
    def Advance(self):
        self.Motor_Upper_L(1, self.speed_Upper_L)
        self.Motor_Lower_L(1, self.speed_Lower_L)
        self.Motor_Upper_R(1, self.speed_Upper_R)
        self.Motor_Lower_R(1, self.speed_Lower_R)

    # Backward
    def Back(self):
        self.Motor_Upper_L(0, self.speed_Upper_L)
        self.Motor_Lower_L(0, self.speed_Lower_L)
        self.Motor_Upper_R(0, self.speed_Upper_R)
        self.Motor_Lower_R(0, self.speed_Lower_R)

    # Turn left
    def Turn_Left(self):
        self.Motor_Upper_L(0, self.speed_Upper_L)
        self.Motor_Lower_L(0, self.speed_Lower_L)
        self.Motor_Upper_R(1, self.speed_Upper_R)
        self.Motor_Lower_R(1, self.speed_Lower_R)

    # Turn right
    def Turn_Right(self):
        self.Motor_Upper_L(1, self.speed_Upper_L)
        self.Motor_Lower_L(1, self.speed_Lower_L)
        self.Motor_Upper_R(0, self.speed_Upper_R)
        self.Motor_Lower_R(0, self.speed_Lower_R)

    # Move left
    def L_Move(self):
        self.Motor_Upper_L(0, self.speed_Upper_L)
        self.Motor_Lower_L(1, self.speed_Lower_L)
        self.Motor_Upper_R(1, self.speed_Upper_R)
        self.Motor_Lower_R(0, self.speed_Lower_R)

    # Move right
    def R_Move(self):
        self.Motor_Upper_L(1, self.speed_Upper_L)
        self.Motor_Lower_L(0, self.speed_Lower_L)
        self.Motor_Upper_R(0, self.speed_Upper_R)
        self.Motor_Lower_R(1, self.speed_Lower_R)

    # Move left-up
    def LU_Move(self):
        self.Motor_Upper_L(0, 0)
        self.Motor_Lower_L(1, self.speed_Lower_L)
        self.Motor_Upper_R(1, self.speed_Upper_R)
        self.Motor_Lower_R(0, 0)

    # Move left-down
    def LD_Move(self):
        self.Motor_Upper_L(0, self.speed_Upper_L)
        self.Motor_Lower_L(0, 0)
        self.Motor_Upper_R(0, 0)
        self.Motor_Lower_R(0, self.speed_Lower_R)

    # Move right-up
    def RU_Move(self):
        self.Motor_Upper_L(1, self.speed_Upper_L)
        self.Motor_Lower_L(0, 0)
        self.Motor_Upper_R(0, 0)
        self.Motor_Lower_R(1, self.speed_Lower_R)

    # Move right-down
    def RD_Move(self):
        self.Motor_Upper_L(0, 0)
        self.Motor_Lower_L(0, self.speed_Lower_L)
        self.Motor_Upper_R(0, self.speed_Upper_R)
        self.Motor_Lower_R(0, 0)

    # Drift right
    def drift_left(self):
        self.Motor_Upper_L(0, 0)
        self.Motor_Lower_L(0, self.speed_Lower_L)
        self.Motor_Upper_R(0, 0)
        self.Motor_Lower_R(1, self.speed_Lower_R)

    # Drift left
    def drift_right(self):
        self.Motor_Upper_L(0, 0)
        self.Motor_Lower_L(1, self.speed_Lower_L)
        self.Motor_Upper_R(0, 0)
        self.Motor_Lower_R(0, self.speed_Lower_R)

    # Rainbow light
    def left_led(self, state):
        self.set_pwm(0x09, state)

    def right_led(self, state):
        self.set_pwm(0x0A, state)

    # Front-left motor
    def Motor_Upper_L(self, stateL, left1):
        if stateL == 1:
            self.set_pwm(3, 0)
            self.set_pwm(4, left1)
        elif stateL == 0:
            self.set_pwm(3, left1)
            self.set_pwm(4, 0)

    # Rear-left motor
    def Motor_Lower_L(self, stateL, left1):
        if stateL == 1:
            self.set_pwm(7, 0)
            self.set_pwm(8, left1)
        elif stateL == 0:
            self.set_pwm(7, left1)
            self.set_pwm(8, 0)

    # Front-right motor
    def Motor_Upper_R(self, stateR, right1):
        if stateR == 1:
            self.set_pwm(1, 0)
            self.set_pwm(2, right1)
        elif stateR == 0:
            self.set_pwm(1, right1)
            self.set_pwm(2, 0)

    # Rear-right motor
    def Motor_Lower_R(self, stateR, right1):
        if stateR == 1:
            self.set_pwm(5, 0)
            self.set_pwm(6, right1)
        elif stateR == 0:
            self.set_pwm(5, right1)
            self.set_pwm(6, 0)

    def set_pwm(self, channel, value):
        try:
            self.i2c.writeto_mem(self.addr, channel, bytearray([value & 0xFF]))
        except OSError as e:
            errno = e.args[0] if e.args else None
            self.fault = "I2C write to addr 0x{:02x} channel {} (value {}) failed: errno {} ({})".format(
                self.addr, channel, value, errno, e
            )
        else:
            self.fault = None


# --- Initialize car driver ---
i2c = I2C(0, sda=Pin(20), scl=Pin(21), freq=400000)
mecanumCar = Driver(i2c)
