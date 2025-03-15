def get_imx219_gstreamer_pipeline(id, capture_width, capture_height, framerate):
    return (
        f"libcamerasrc camera-index={id} ! "
        f"video/x-raw, format=(string)YUY2, width=(int){capture_width}, height=(int){capture_height}, framerate=(fraction){framerate}/1 ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! "
        "appsink"
    )