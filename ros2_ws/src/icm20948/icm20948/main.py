import time

from icm_wrapper import imuDataGet, imuInit


if __name__ == "__main__":
    imuInit()
    for i in range(100):
        imuDataGet()

    while True:
        angles, quaternion, gyro, accel, gravity, magn = imuDataGet()
        print(f"Angles: {angles}")
        print(f"Quaternion: {quaternion}")
        print(f"Gyro: {gyro}")
        print(f"Accel: {accel}")
        print(f"Gravity: {gravity}")
        print(f"Magn: {magn}")
        time.sleep(5)
