import os
import sys
import platform
import ctypes


def load_shared_library(lib_basename="ICM20948", search_dir=None):
    if search_dir is None:
        search_dir = os.path.dirname(__file__)

    # Build suffix like: cpython-312-aarch64-linux-gnu
    py_tag = f"cpython-{sys.version_info.major}{sys.version_info.minor}"
    arch_tag = platform.machine()
    system_tag = platform.system().lower()

    # Construct search pattern
    candidates = [
        f"{lib_basename}.{py_tag}-{arch_tag}-{system_tag}-gnu.so",
        f"{lib_basename}.{py_tag}-{arch_tag}-gnu.so",
        f"{lib_basename}.so",  # fallback
    ]
    
    for candidate in candidates:
        full_path = os.path.join(search_dir, candidate)
        if os.path.exists(full_path):
            return ctypes.CDLL(full_path)

    raise FileNotFoundError(f"No suitable shared library found for {lib_basename} in {search_dir}")

lib = load_shared_library("ICM20948")

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
    
    def to_array(self):
        return [self.x, self.y, self.z]

class IMU_ST_QUATERNION_DATA(ctypes.Structure):
    _fields_ = [("w", ctypes.c_float),
                ("x", ctypes.c_float),
                ("y", ctypes.c_float),
                ("z", ctypes.c_float)]  
    
    def __str__(self):
        return f"W: {self.w}, X: {self.x}, Y: {self.y}, Z: {self.z}"

# Tell ctypes about function argument types
lib.imuDataGet.argtypes = [ctypes.POINTER(IMU_ST_ANGLES_DATA),
                           ctypes.POINTER(IMU_ST_QUATERNION_DATA),
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
    quaternion = IMU_ST_QUATERNION_DATA()

    lib.imuDataGet(ctypes.byref(angles),
                   ctypes.byref(quaternion),
                   ctypes.byref(gyro),
                   ctypes.byref(accel),
                   ctypes.byref(gravity),
                   ctypes.byref(magn))

    return angles, quaternion, gyro, accel, gravity, magn