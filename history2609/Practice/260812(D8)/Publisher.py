import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class VelocityPublisher(Node):
    def __init__(self):
        super().__init__('velocity_publisher')      # 노드 이름
        # 발행자 생성: (메시지타입, 토픽명, 큐깊이)
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10) # topic이름은 /cmd_vel이고, 큐 깊이는 10개
        # 0.05초(20Hz)마다 tick 호출
        self.timer = self.create_timer(0.05, self.tick)
        self.get_logger().info('발행 시작')

    def tick(self):
        msg = Twist()
        msg.linear.x = 0.2      # 0.2 m/s 전진
        msg.angular.z = 0.1     # 약간 회전
        self.pub.publish(msg)

def main():
    rclpy.init()
    node = VelocityPublisher()
    rclpy.spin(node)            # 콜백이 돌기 시작
    rclpy.shutdown()

if __name__ == '__main__':
    main()