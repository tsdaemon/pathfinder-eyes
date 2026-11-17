#!/usr/bin/env python3
"""Draw VO's features on the camera image in Foxglove: /odom_info -> /vo_features.

Publishes foxglove_msgs/ImageAnnotations stamped like the right camera frame VO used, so
Foxglove's Image panel on /oakd/right/image_rect/compressed can overlay it (panel settings
-> Annotations -> /vo_features). Green = inlier (used for the motion estimate), yellow =
matched to the local map but rejected, red = detected but unmatched. A text line gives the
counts. Unmatched (red) ones are hidden by default (SHOW_ALL). Few greens, or greens bunched in one
corner, is when VO is about to get lost.
"""

import rclpy
from foxglove_msgs.msg import (
    Color,
    ImageAnnotations,
    Point2,
    PointsAnnotation,
    TextAnnotation,
)
from rclpy.node import Node
from rtabmap_msgs.msg import OdomInfo

SHOW_ALL = False  # also draw unmatched (red) features

GREEN = Color(r=0.1, g=0.9, b=0.2, a=1.0)
YELLOW = Color(r=1.0, g=0.85, b=0.0, a=1.0)
RED = Color(r=1.0, g=0.2, b=0.2, a=0.8)
WHITE = Color(r=1.0, g=1.0, b=1.0, a=1.0)
BLACK = Color(r=0.0, g=0.0, b=0.0, a=0.6)


class VoFeatures(Node):
    def __init__(self):
        super().__init__("vo_features")
        self.pub = self.create_publisher(ImageAnnotations, "/vo_features", 10)
        self.create_subscription(OdomInfo, "/odom_info", self.on_info, 10)

    def on_info(self, info):
        stamp = info.header.stamp
        inliers, matches = set(info.word_inliers), set(info.word_matches)
        # Unmatched features aren't drawn: VO detects a fresh set every frame, so they jump
        # around even when parked. SHOW_ALL brings them back.
        green, yellow, red = [], [], []
        for key, kp in zip(info.words_keys, info.words_values):
            group = green if key in inliers else yellow if key in matches else red
            group.append(Point2(x=float(kp.pt.x), y=float(kp.pt.y)))

        msg = ImageAnnotations()
        groups = ((RED, red), (YELLOW, yellow), (GREEN, green))
        for color, pts in groups if SHOW_ALL else groups[1:]:
            if pts:
                msg.points.append(
                    PointsAnnotation(
                        timestamp=stamp,
                        type=PointsAnnotation.POINTS,
                        points=pts,
                        outline_color=color,
                        fill_color=color,
                        thickness=2.0,
                    )
                )
        status = "LOST" if info.lost else f"{info.inliers} inliers"
        msg.texts.append(
            TextAnnotation(
                timestamp=stamp,
                position=Point2(x=8.0, y=20.0),
                text=f"VO {status} / {info.matches} matches / {info.features} features",
                font_size=16.0,
                text_color=WHITE,
                background_color=BLACK,
            )
        )
        self.pub.publish(msg)


def main():
    rclpy.init()
    rclpy.spin(VoFeatures())


if __name__ == "__main__":
    main()
