import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, MagneticField
from math import cos, sin

from icm20948 import imuInit, imuDataGet

class ImuNode(Node):
    def __init__(self):
        super().__init__('imu_node')
        self.publisher_imu = self.create_publisher(Imu, 'imu/data_raw', 10)
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
            for i in range(20):
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
            angles, gyro, accel, grav, magn = imuDataGet()

            # Fill linear acceleration subtracting gravity
            msg.linear_acceleration.x = accel.x - grav.x
            msg.linear_acceleration.y = accel.y - grav.y
            msg.linear_acceleration.z = accel.z - grav.z

            # Fill angular velocity
            msg.angular_velocity.x = gyro.x
            msg.angular_velocity.y = gyro.y
            msg.angular_velocity.z = gyro.z

            # Fill orientation
            # Convert roll, pitch, yaw to quaternion
            roll, pitch, yaw = angles., angles.y, angles.z
            
            # Calculate quaternion components
            # cy = cos(yaw * 0.5)
            # sy = sin(yaw * 0.5)
            # cp = cos(pitch * 0.5)
            # sp = sin(pitch * 0.5)
            # cr = cos(roll * 0.5)
            # sr = sin(roll * 0.5)

            # msg.orientation.w = cr * cp * cy + sr * sp * sy
            # msg.orientation.x = sr * cp * cy - cr * sp * sy
            # msg.orientation.y = cr * sp * cy + sr * cp * sy
            # msg.orientation.z = cr * cp * sy - sr * sp * cy

            msg.orientation_covariance[0] = -1.0  # Means orientation not provided

            mag_msg.magnetic_field.x = magn.x
            mag_msg.magnetic_field.y = magn.y
            mag_msg.magnetic_field.z = magn.z

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