import cv2
import numpy as np
import asyncio


class Eyes:
    def __init__(
        self, 
        left_camera_id, 
        right_camera_id,
        camera_matrix, 
        dist_coeffs, 
        R, 
        T, 
        width, 
        height,
        on_update_callback=None
    ):
        self.left_camera_id = left_camera_id
        self.right_camera_id = right_camera_id
        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs
        self.R = R
        self.T = T
        self.width = width
        self.height = height

        self.on_update_callback = on_update_callback

        self.prepare_rectification()

    def prepare_rectification(self):
        rectify_scale = 1  # Should be 0 if size is the same, 1 if not
        R1, R2, P1, P2, _, _, _ = cv2.stereoRectify(
            self.camera_matrix, self.dist_coeffs,
            self.camera_matrix, self.dist_coeffs,
            (self.width, self.height), self.R, self.T,
            rectify_scale, (0, 0)
        )

        left_map1, left_map2 = cv2.initUndistortRectifyMap(
            self.camera_matrix, self.dist_coeffs, R1, P1, (self.width, self.height), 5
        )
        right_map1, right_map2 = cv2.initUndistortRectifyMap(
            self.camera_matrix, self.dist_coeffs, R2, P2, (self.width, self.height), 5
        )
        self.left_map1 = left_map1
        self.left_map2 = left_map2
        self.right_map1 = right_map1
        self.right_map2 = right_map2

    def start(self):
        try:
            self.left_camera = cv2.VideoCapture(self.left_camera_id)
            self.right_camera = cv2.VideoCapture(self.right_camera_id)
            self.left_camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.left_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.right_camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.right_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

            prev_gray_left = None
            while True:
                # Capture frames from both cameras
                ret_left, frame_left = self.left_camera.read()
                ret_right, frame_right = self.right_camera.read()

                if not ret_left or not ret_right:
                    break
                
                # Rectify the images
                # rectified_left = cv2.remap(frame_left, self.left_map1, self.left_map2, cv2.INTER_LINEAR)
                # rectified_right = cv2.remap(frame_right, self.right_map1, self.right_map2, cv2.INTER_LINEAR)

                # Convert frames to grayscale
                gray_left = cv2.cvtColor(frame_left, cv2.COLOR_BGR2GRAY)
                gray_right = cv2.cvtColor(frame_right, cv2.COLOR_BGR2GRAY)
                gray_left = np.uint8(gray_left)
                gray_right = np.uint8(gray_right)
                
                # Calculate disparity and depth map
                disparity = self.calculate_disparity(gray_left, gray_right)
                depth_map = self.estimate_depth(disparity, np.linalg.norm(self.T), self.camera_matrix[0, 0])

                # Calculate 3D motion
                if prev_gray_left is not None:
                    flow = self.compute_optical_flow(prev_gray_left, gray_left)
                    rotation, translation = self.estimate_3d_motion(depth_map, flow)

                    self.on_update_callback(frame_left, frame_right, disparity, depth_map, rotation, translation)

                prev_gray_left = gray_left
        finally:
            self.release()

    def release(self):
        self.left_camera.release()
        self.right_camera.release()
    
    def calculate_disparity(self, img_left, img_right):
        stereo = cv2.StereoBM_create(numDisparities=16*9, blockSize=9)
        disparity = stereo.compute(img_left, img_right).astype(np.float32) / 16.0
        return disparity

    def estimate_depth(self, disparity, baseline, focal_length):
        valid_mask = disparity > 0
        depth_map = np.zeros_like(disparity)
        depth_map[valid_mask] = (focal_length * baseline) / disparity[valid_mask]
        return depth_map

    def compute_optical_flow(self, prev_frame, curr_frame):
        flow = cv2.calcOpticalFlowFarneback(prev_frame, curr_frame, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        return flow

    def estimate_3d_motion(self, depth_map, flow):
        focal_length = self.camera_matrix[0, 0]
        height, width = depth_map.shape

        # Create a grid of 3D points
        x, y = np.meshgrid(np.arange(width), np.arange(height))
        z = depth_map
        x3d = (x - self.camera_matrix[0, 2]) * z / focal_length
        y3d = (y - self.camera_matrix[1, 2]) * z / focal_length

        # Compute 3D flow
        flow_3d = np.dstack((flow[..., 0] * z / focal_length,
                            flow[..., 1] * z / focal_length,
                            np.zeros_like(z)))

        # Estimate rotation and translation
        # This is a simplified example; in practice, you would use more robust methods
        rotation = np.nanmean(flow_3d, axis=(0, 1))
        translation = np.nanmean(np.dstack((x3d, y3d, z)), axis=(0, 1))

        return rotation, translation





