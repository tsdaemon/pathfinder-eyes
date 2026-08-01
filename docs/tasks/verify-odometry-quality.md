# Verify RTAB-Map odometry quality

`rgbd_odometry` was logging repeated IMU/image desync errors ("didn't receive IMU newer than
previous image"). Hold the robot still and watch `ros2 run tf2_ros tf2_echo odom base_link`;
it should stay near identity. If it drifts while stationary, that's a real problem to chase
before trusting anything built on top of odometry.
