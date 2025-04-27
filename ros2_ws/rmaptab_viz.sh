ros2 run rtabmap_viz rtabmap_viz \
  --ros-args \
  -p frame_id:=camera_1_optical_frame \
  -p subscribe_depth:=false \
  -p subscribe_odom_info:=true \
  -p subscribe_stereo:=true \
  -p approx_sync:=true \
  -p cloud_decimation:=3 \
  --remap left/image_rect:=/stereo_resized/left/image_rect \
  --remap right/image_rect:=/stereo_resized/right/image_rect \
  --remap left/camera_info:=/stereo_resized/left/camera_info \
  --remap right/camera_info:=/stereo_resized/right/camera_info \
  --remap imu:=/imu/data


# With Oak
ros2 run rtabmap_viz rtabmap_viz \
    --ros-args --remap rgb/image:=/oak/rgb/image_rect \
                --remap rgb/camera_info:=/oak/rgb/camera_info \
                --remap depth/image:=/oak/stereo/image_raw \
                -p frame_id:=oak \
                -p subscribe_rgb:=true \
                -p subscribe_depth:=true \
                -p subscribe_odom_info:=true \
                -p approx_sync:=true \
                -p Rtabmap/DetectionRate:=3.5