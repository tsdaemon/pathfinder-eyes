import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, MagneticField
from math import cos, sin

from icm20948 import imuInit, imuDataGet

CYCLES_TO_CALIBRATE = 100
ORIENTATION_COVARIANCE = 0.02
ANGULAR_VELOCITY_COVARIANCE = 0.01
LINEAR_ACCELERATION_COVARIANCE = 0.2

class ImuNode(Node):
    def __init__(self):
        super().__init__('imu_node')
        self.publisher_imu = self.create_publisher(Imu, 'imu/data', 10)
        self.mag_pub = self.create_publisher(MagneticField, 'imu/mag', 10)

        self.publisher_timer = None

        self.imu_initialized = False
        self.imu_init_timer = self.create_timer(1.0, self.try_init_imu)

    def try_init_imu(self):
        if self.imu_initialized:
            self.imu_init_timer.cancel()
            return

        try:
            imuInit()
            for _ in range(CYCLES_TO_CALIBRATE):
                imuDataGet()
            self.get_logger().info("ICM20948 initialized successfully.")
            self.imu_init_timer.cancel()

            # Now start the main publishing timer
            timer_period = 0.05  # 20 Hz
            self.publisher_timer = self.create_timer(timer_period, self.publish_imu_data)

        except Exception as e:
            self.get_logger().warn(f"IMU not ready yet: {e}")

    def publish_imu_data(self):
        msg = Imu()
        now = self.get_clock().now().to_msg()
        msg.header.stamp = now
        msg.header.frame_id = "imu_link"

        mag_msg = MagneticField()
        mag_msg.header.stamp = now
        mag_msg.header.frame_id = "imu_link"

        try:
            _, quaternion, gyro, accel, grav, magn = imuDataGet()

            # Fill linear acceleration subtracting gravity, converting g to m/s^2
            G_TO_M_S2 = 9.80665
            msg.linear_acceleration.x = (accel.x - grav.x) * G_TO_M_S2
            msg.linear_acceleration.y = (accel.y - grav.y) * G_TO_M_S2
            msg.linear_acceleration.z = (accel.z - grav.z) * G_TO_M_S2

            # Fill angular velocity, converting deg/s to rad/s
            msg.angular_velocity.x = gyro.x * (math.pi / 180.0)
            msg.angular_velocity.y = gyro.y * (math.pi / 180.0)
            msg.angular_velocity.z = gyro.z * (math.pi / 180.0)

            # Fill orientation
            msg.orientation.w = quaternion.w
            msg.orientation.x = quaternion.x
            msg.orientation.y = quaternion.y
            msg.orientation.z = quaternion.z

            # Set covariance 
            msg.orientation_covariance = [ORIENTATION_COVARIANCE] * 3 + [0] * 3 + [ORIENTATION_COVARIANCE] * 3
            msg.angular_velocity_covariance = [ANGULAR_VELOCITY_COVARIANCE] * 3 + [0] * 3 + [ANGULAR_VELOCITY_COVARIANCE] * 3  
            msg.linear_acceleration_covariance = [LINEAR_ACCELERATION_COVARIANCE] * 3 + [0] * 3 + [LINEAR_ACCELERATION_COVARIANCE] * 3

            # Fill magnetic field
            MICROTESLA_TO_TESLA = 1e-6
            mag_msg.magnetic_field.x = magn.x * MICROTESLA_TO_TESLA
            mag_msg.magnetic_field.y = magn.y * MICROTESLA_TO_TESLA
            mag_msg.magnetic_field.z = magn.z * MICROTESLA_TO_TESLA

            self.publisher_imu.publish(msg)
            self.mag_pub.publish(mag_msg)

        except Exception as e:
            self.get_logger().error(f"Error reading IMU: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = ImuNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()