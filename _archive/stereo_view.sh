ros2 run rqt_reconfigure rqt_reconfigure

ros2 run image_view stereo_view --ros-args \
  -r /stereo/left/image:=/stereo_resized/left/image_rect \
  -r /stereo/right/image:=/stereo_resized/right/image_rect \
  -r /stereo/disparity:=/stereo_resized/disparity \
  -p approximate_sync:=true