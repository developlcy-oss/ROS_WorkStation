
import math

import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker


class WaypointMarker(Node):

    def __init__(self):
        super().__init__('waypoint_marker')

        self.publisher = self.create_publisher(
            Marker,
            '/waypoints',
            10
        )

        # 경유점 목록
        self.waypoints = [
            (2.0, 2.0),
            (8.0, 2.0),
            (8.0, 8.0),
            (2.0, 8.0),
        ]

        # 빈 경유점 목록 예외 처리
        if not self.waypoints:
            self.get_logger().warning(
                'Waypoint list is empty.'
            )

        self.timer = self.create_timer(
            1.0,
            self.publish_waypoints
        )

    @staticmethod
    def is_waypoint_reached(
        x,
        y,
        waypoint_x,
        waypoint_y,
        tolerance
    ):
        """Check whether the current position reached the waypoint."""

        if tolerance < 0:
            raise ValueError(
                'Tolerance must be non-negative.'
            )

        distance = math.sqrt(
            (x - waypoint_x) ** 2 +
            (y - waypoint_y) ** 2
        )

        return distance <= tolerance

    def publish_waypoints(self):

        # 빈 경유점 목록이면 경고 후 종료
        if not self.waypoints:
            self.get_logger().warning(
                'No waypoints to publish.'
            )
            return

        for i, (x, y) in enumerate(self.waypoints):

            marker = Marker()

            marker.header.frame_id = 'world'
            marker.header.stamp = (
                self.get_clock().now().to_msg()
            )

            marker.ns = 'waypoints'
            marker.id = i

            marker.type = Marker.SPHERE
            marker.action = Marker.ADD

            marker.pose.position.x = x
            marker.pose.position.y = y
            marker.pose.position.z = 0.0

            marker.pose.orientation.w = 1.0

            marker.scale.x = 0.3
            marker.scale.y = 0.3
            marker.scale.z = 0.3

            marker.color.a = 1.0
            marker.color.r = 1.0
            marker.color.g = 0.0
            marker.color.b = 0.0

            self.publisher.publish(marker)


def main(args=None):
    rclpy.init(args=args)

    node = WaypointMarker()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
