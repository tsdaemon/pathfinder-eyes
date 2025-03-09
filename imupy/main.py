import time

from icm_wrapper import imuDataGet, imuInit


if __name__ == "__main__":
    imuInit()
    while True:
        angles, gyro, accel, magn = imuDataGet()
        print(f"Angles: {angles}")
        print(f"Gyro: {gyro}")
        print(f"Accel: {accel}")
        print(f"Magn: {magn}")
        time.sleep(2)
