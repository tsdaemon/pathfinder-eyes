sudo apt install -y python3-venv

# https://github.com/raspberrypi/libcamera
# meson setup build --reconfigure --buildtype=release -Dpipelines=rpi/vc4,rpi/pisp -Dipas=rpi/vc4,rpi/pisp -Dv4l2=true -Dgstreamer=enabled -Dtest=false -Dlc-compliance=disabled -Dcam=enabled -Dqcam=disabled -Ddocumentation=disabled -Dpycamera=enabled
# ln -s ~/libcamera/build/src/py/libcamera ~/eyes/env/lib/python3.12/site-packages/libcamera
# and install pycamera2 to the env
# patch picamera2 to not import DrmPreview if not installing desktop

# For remote desktop
sudo apt install -y xterm tigervnc-standalone-server tigervnc-common lxqt-core menu oxygen-icon-theme qterminal openbox python3-xdg pcmanfm-qt --no-install-recommends
sudo apt install -y ros-jazzy-rviz2 ros-jazzy-rqt ros-jazzy-rqt-common-plugins ros-jazzy-desktop
