import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class SquareController(Node):
    def __init__(self):
        super().__init__('square_controller')

        self.publisher = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)

        self.linear_speed = 2.0
        self.forward_time = 1.5
        self.rotate_time = 2.0
        self.stop_time = 0.5  # 관성 및 궤적 정돈을 위한 정지 시간
        self.angular_speed = (math.pi / 2) / self.rotate_time

        # 상태: 'forward' -> 'stop_before_rotate' -> 'rotate' -> 'stop_before_forward'
        self.state = 'forward'
        self.side_count = 0
        self.start_time = self.get_clock().now()

        # 0.01초(100Hz) 주기로 제어하여 타이머 오버슈트 최소화
        self.timer = self.create_timer(0.01, self.control_loop)

    def control_loop(self):
        cmd = Twist()
        elapsed = (self.get_clock().now() - self.start_time).nanoseconds / 1e9

        if self.state == 'forward':
            if elapsed < self.forward_time:
                cmd.linear.x = self.linear_speed
            else:
                self.side_count += 1
                self.switch_state('stop_before_rotate')

        elif self.state == 'stop_before_rotate':
            if elapsed >= self.stop_time:
                self.switch_state('rotate')

        elif self.state == 'rotate':
            if elapsed < self.rotate_time:
                cmd.angular.z = self.angular_speed
            else:
                if self.side_count >= 4:
                    self.stop_robot()
                    self.get_logger().info('Square completed!')
                    self.timer.cancel()
                    return
                self.switch_state('stop_before_forward')

        elif self.state == 'stop_before_forward':
            if elapsed >= self.stop_time:
                self.switch_state('forward')

        self.publisher.publish(cmd)

    def switch_state(self, new_state):
        self.state = new_state
        self.start_time = self.get_clock().now()

    def stop_robot(self):
        cmd = Twist()
        self.publisher.publish(cmd)
        
    @staticmethod 
    def angle_to_goal(x, y, goal_x, goal_y):
        """Calculate angle from current position to goal."""
        angle = math.atan2(
        goal_y - y,
        goal_x - x
    )

    # 각도를 -pi ~ pi 범위로 정규화
        return (angle + math.pi) % (2 * math.pi) - math.pi

def main(args=None):
    rclpy.init(args=args)
    node = SquareController()
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