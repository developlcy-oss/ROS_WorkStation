import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32


class DistanceWarning(Node):

    def __init__(self):
        super().__init__('distance_warning')

        # 경고 임계값 파라미터
        self.declare_parameter('warn_distance', 3.0)

        # /turtle_distance 구독
        self.subscription = self.create_subscription(
            Float32,
            '/turtle_distance',
            self.distance_callback,
            10
        )

        self.get_logger().info(
            'Distance warning node started'
        )

    def distance_callback(self, msg):

        # 현재 설정된 임계값 가져오기
        warn_distance = self.get_parameter(
            'warn_distance'
        ).value

        # 임계값을 초과하면 경고
        if msg.data > warn_distance:
            self.get_logger().warn(
                f'Distance warning! '
                f'distance={msg.data:.2f} '
                f'> threshold={warn_distance:.2f}'
            )


def main(args=None):

    rclpy.init(args=args)

    node = DistanceWarning()


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