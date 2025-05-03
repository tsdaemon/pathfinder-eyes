#!/bin/bash

# kill all ros2 processes
sudo pkill -f /opt/ros/jazzy
sudo pkill -f watchdog
kill $(cat tmp/supervisord.pid) > /dev/null 2>&1 || true
