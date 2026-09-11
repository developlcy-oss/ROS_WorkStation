import math

import rclpy
from rclpy.node import Node

from turtlesim.msg import Pose
from std_msgs.msg import Float32

class DistancePublisher(Node):

    def __init__(self):
        super().__init__('distance_publisher')

        # 발행 주기 파라미터
        self.declare_parameter('publish_rate', 10.0)
        publish_rate = self.get_parameter('publish_rate').value

        # 잘못된 발행 주기 예외 처리 
        try: 
            if publish_rate <= 0: 
                raise ValueError( 'publish_rate must be greater than 0.' ) 
            timer_period = 1.0 / publish_rate 

        except (TypeError, ValueError, ZeroDivisionError) as e:
            self.get_logger().warning( f'Invalid publish_rate: {publish_rate}. ' f'{e} Using 10.0 Hz instead.' ) 
            publish_rate = 10.0 
            timer_period = 1.0 / publish_rate

        # 최신 거북이 위치를 저장할 변수
        self.x = 0.0
        self.y = 0.0

        # /turtle1/pose 구독
        self.pose_subscription = self.create_subscription(
            Pose,
            '/turtle1/pose',
            self.pose_callback,
            10
        )

        # /turtle_distance 발행
        self.distance_publisher = self.create_publisher(
            Float32,
            '/turtle_distance',
            10
        )

        # Timer
        timer_period = 1.0 / publish_rate

        self.timer = self.create_timer(
            timer_period,
            self.timer_callback
        )

        self.get_logger().info(
            f'Distance publisher started: {publish_rate} Hz'
        )
        
    @staticmethod 
    def calculate_distance(x, y): 
        """Calculate distance from origin.""" 
        return math.sqrt(x ** 2 + y ** 2)

    def pose_callback(self, msg):
        # 최신 위치만 저장한다.
        self.x = msg.x
        self.y = msg.y

    def timer_callback(self):
        # 원점으로부터의 거리 계산
        distance = self.calculate_distance(self.x, self.y)

        # Float32 메시지 생성
        msg = Float32()
        msg.data = distance

        # 거리 발행
        self.distance_publisher.publish(msg)

        # 발행 로그
        self.get_logger().info(
            f'[rclpy Publisher] Publishing distance: {distance:.2f}'
        )


def calculate_distance(x, y):
    return math.sqrt(x ** 2 + y ** 2)


def main(args=None):

    # ROS2 초기화
    rclpy.init(args=args)

    # Node 생성
    node = DistancePublisher()

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