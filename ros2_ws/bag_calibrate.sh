#!/bin/bash
source install/setup.bash
ros2 bag record -o pathfinder_calibrate.bag /imu/data /stereo/left/image_raw /stereo/right/image_raw