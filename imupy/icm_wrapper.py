import os
import ctypes

# Load the shared library
lib = ctypes.CDLL(os.path.join(os.path.dirname(__file__), "ICM20948.so"))

# Define the structures to match the C definitions

class IMU_EN_SENSOR_TYPE(ctypes.c_int):
    IMU_EN_SENSOR_TYPE_NULL = 0
    IMU_EN_SENSOR_TYPE_ICM20948 = 1
    IMU_EN_SENSOR_TYPE_MAX = 2

# Tell ctypes about imuInit function argument types
lib.imuInit.argtypes = [ctypes.POINTER(IMU_EN_SENSOR_TYPE)]
lib.imuInit.restype = ctypes.c_int


def imuInit(sensor_type=IMU_EN_SENSOR_TYPE.IMU_EN_SENSOR_TYPE_ICM20948):
    """Initialize the IMU with specified sensor type.
    
    Args:
        sensor_type: IMU_EN_SENSOR_TYPE, defaults to ICM20948
        
    Returns:
        int: Status code from the initialization
    """
    sensor_type_arg = IMU_EN_SENSOR_TYPE(sensor_type)
    return lib.imuInit(ctypes.byref(sensor_type_arg))


class IMU_ST_ANGLES_DATA(ctypes.Structure):
    _fields_ = [("roll", ctypes.c_float),
                ("pitch", ctypes.c_float),
                ("yaw", ctypes.c_float)]
    
    def __str__(self):
        return f"Roll: {self.roll}, Pitch: {self.pitch}, Yaw: {self.yaw}"

class IMU_ST_SENSOR_DATA(ctypes.Structure):
    _fields_ = [("x", ctypes.c_float),
                ("y", ctypes.c_float),
                ("z", ctypes.c_float)]

    def __str__(self):
        return f"X: {self.x}, Y: {self.y}, Z: {self.z}"

# Tell ctypes about function argument types
lib.imuDataGet.argtypes = [ctypes.POINTER(IMU_ST_ANGLES_DATA),
                           ctypes.POINTER(IMU_ST_SENSOR_DATA),
                           ctypes.POINTER(IMU_ST_SENSOR_DATA),
                           ctypes.POINTER(IMU_ST_SENSOR_DATA),
                           ctypes.POINTER(IMU_ST_SENSOR_DATA)]

# Define the function to call
def imuDataGet():
    angles = IMU_ST_ANGLES_DATA()
    gyro = IMU_ST_SENSOR_DATA()
    accel = IMU_ST_SENSOR_DATA()
    magn = IMU_ST_SENSOR_DATA()
    gravity = IMU_ST_SENSOR_DATA()

    lib.imuDataGet(ctypes.byref(angles),
                   ctypes.byref(gyro),
                   ctypes.byref(accel),
                   ctypes.byref(gravity),
                   ctypes.byref(magn))

    return angles, gyro, accel, gravity, magn