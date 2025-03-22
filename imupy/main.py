import time

from ros2_ws.src.icm20948.icm20948.icm_wrapper import imuDataGet, imuInit


if __name__ == "__main__":
    imuInit()
    while True:
        angles, gyro, accel, gravity, magn = imuDataGet()
        print(f"Angles: {angles}")
        print(f"Gyro: {gyro}")
        print(f"Accel: {accel}")
        print(f"Gravity: {gravity}")
        print(f"Magn: {magn}")
        time.sleep(2)
