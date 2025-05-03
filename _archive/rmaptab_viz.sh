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
