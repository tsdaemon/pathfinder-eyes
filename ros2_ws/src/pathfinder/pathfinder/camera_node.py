import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
from picamera2 import Picamera2
from rclpy.parameter import Parameter
from rclpy.exceptions import ParameterNotDeclaredException
import yaml
import os
from ament_index_python.packages import get_package_share_directory

FRAME_RATE = 20
HEIGHT = 1080
WIDTH = 1920

CAMERA_CONFIG = dict(
    main={"size": (WIDTH, HEIGHT), "format": "YUV420"},
    display=None,
    buffer_count=6,
    controls={"FrameRate": FRAME_RATE}
)

class CameraNode(Node):
    def __init__(self):
        super().__init__('camera_node')

        # Declare parameters
        self.declare_parameter('camera_id', 0)
        self.declare_parameter('image_topic', 'camera/image_raw')
        self.declare_parameter('camera_info_topic', 'camera/camera_info')
        self.declare_parameter('camera_info_file', '')
        
        try:
            self.camera_id = self.get_parameter('camera_id').value
            self.image_topic = self.get_parameter('image_topic').value
            self.camera_info_topic = self.get_parameter('camera_info_topic').value
            self.camera_info_file = self.get_parameter('camera_info_file').value
        except ParameterNotDeclaredException as e:
            self.get_logger().warn(f'Parameter not set: {str(e)}')
            self.camera_id = 0
            self.image_topic = 'camera/image_raw'
            self.camera_info_topic = 'camera/camera_info'
            self.camera_info_file = ''

        # Initialize the camera
        self.picam2 = None
        self.bridge = CvBridge()
        self.publisher = self.create_publisher(Image, self.image_topic, 10)
        self.camera_info_pub = self.create_publisher(CameraInfo, self.camera_info_topic, 10)
        
        # Load camera calibration data
        self.camera_info_msg = self.load_camera_info()
        
        # Create timer for initialization attempts
        self.init_timer = self.create_timer(1.0, self.try_init_camera)
        
    def load_camera_info(self):
        cam_info = CameraInfo()
        
        # Get absolute path to camera info file
        camera_info_path = os.path.join(get_package_share_directory('pathfinder'), self.camera_info_file)
        if self.camera_info_file and os.path.exists(camera_info_path):
            try:
                with open(camera_info_path, 'r') as f:
                    calib_data = yaml.safe_load(f)
                    
                cam_info.width = calib_data["resolution"][0]
                cam_info.height = calib_data["resolution"][1]

                fx, fy, cx, cy = calib_data["intrinsics"]
                cam_info.k = [fx, 0, cx,
                            0, fy, cy,
                            0, 0, 1]

                cam_info.d = calib_data["distortion_coeffs"]
                cam_info.distortion_model = "plumb_bob"  # for radtan

                # Unrectified — identity rotation
                cam_info.r = [1, 0, 0,
                              0, 1, 0,
                              0, 0, 1]

                # Projection matrix (no stereo baseline in P[3] or P[7])
                cam_info.p = [fx, 0, cx, 0,
                            0, fy, cy, 0,
                            0, 0, 1, 0]
                self.get_logger().info('Loaded camera calibration data')
                
            except Exception as e:
                self.get_logger().error(f'Failed to load camera calibration: {str(e)}')
        else:
            self.get_logger().warn('No camera calibration file provided or file not found. Looking for: ' + camera_info_path)
            
        return cam_info
            
    def try_init_camera(self):
        if self.picam2 is not None:
            self.init_timer.cancel()
            return
            
        try:
            self.picam2 = Picamera2(self.camera_id)
            self.picam2.configure(
                self.picam2.create_video_configuration(
                    **CAMERA_CONFIG
                )
            )
            self.picam2.start()
            
            self.get_logger().info(f'Camera {self.camera_id} initialized successfully')
            self.get_logger().info(f'Publishing to topics: {self.image_topic}, {self.camera_info_topic}')
            self.init_timer.cancel()
            
            # Start publishing images
            self.timer = self.create_timer(1/FRAME_RATE, self.publish_image)
            
        except Exception as e:
            self.get_logger().warn(f'Failed to initialize camera: {str(e)}')
            
    def publish_image(self):
        if self.picam2 is None:
            return
            
        try:
            # Capture frame
            frame = self.picam2.capture_array("main")
            frame = frame[:HEIGHT, :]  # Take only Y channel (top part)
            
            # Get current timestamp
            current_time = self.get_clock().now().to_msg()
            
            # Convert to ROS Image message
            msg = self.bridge.cv2_to_imgmsg(frame, encoding='mono8')
            msg.header.stamp = current_time
            msg.header.frame_id = f'camera_{self.camera_id}_optical_frame'
            
            # Update and publish camera info
            self.camera_info_msg.header.stamp = current_time
            self.camera_info_msg.header.frame_id = f'camera_{self.camera_id}_optical_frame'
            
            # Publish the messages
            self.publisher.publish(msg)
            self.camera_info_pub.publish(self.camera_info_msg)
            
        except Exception as e:
            self.get_logger().error(f'Error capturing image: {str(e)}')
            
    def destroy_node(self):
        if self.picam2 is not None:
            self.picam2.stop()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = CameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()


