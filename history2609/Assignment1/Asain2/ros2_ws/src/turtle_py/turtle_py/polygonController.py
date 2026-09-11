import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class PolygonController(Node):

    def __init__(self, n):
        super().__init__('polygon_controller')

        # 정n각형 설정
        self.n = n

        # 정n각형은 최소 3개의 변이 필요
        if self.n < 3:
            raise ValueError("n은 3 이상이어야 합니다.")

        # ROS2 publisher
        self.publisher = self.create_publisher(
            Twist,
            '/turtle1/cmd_vel',
            10
        )

        # 주행 설정
        self.linear_speed = 2.0
        self.forward_time = 1.5

        # 한 번 회전하는 데 걸리는 시간
        self.rotate_time = 2.0

        # 직진과 회전 사이 정지 시간
        self.stop_time = 0.5

        # 정n각형의 외각
        self.turn_angle = (2 * math.pi) / self.n

        # 회전 속도
        self.angular_speed = self.turn_angle / self.rotate_time

        # 상태
        self.state = 'forward'

        # 현재 몇 번째 변까지 주행했는가
        self.side_count = 0

        self.start_time = self.get_clock().now()

        # 100Hz 제어
        self.timer = self.create_timer(
            0.01,
            self.control_loop
        )

        self.get_logger().info(
            f'정{self.n}각형 주행 시작 '
            f'(회전각: {math.degrees(self.turn_angle):.2f}°)'
        )

    def control_loop(self):

        cmd = Twist()

        elapsed = (
            self.get_clock().now() - self.start_time
        ).nanoseconds / 1e9

        # -------------------------
        # 1. 직진
        # -------------------------
        if self.state == 'forward':

            if elapsed < self.forward_time:

                cmd.linear.x = self.linear_speed

            else:

                self.side_count += 1
                self.switch_state('stop_before_rotate')

        # -------------------------
        # 2. 회전 전 정지
        # -------------------------
        elif self.state == 'stop_before_rotate':

            if elapsed >= self.stop_time:
                self.switch_state('rotate')

        # -------------------------
        # 3. 회전
        # -------------------------
        elif self.state == 'rotate':

            if elapsed < self.rotate_time:

                cmd.angular.z = self.angular_speed

            else:

                # 모든 변을 주행했다면 종료
                if self.side_count >= self.n:

                    self.stop_robot()

                    self.get_logger().info(
                        f'정{self.n}각형 주행 완료!'
                    )

                    self.timer.cancel()
                    return

                self.switch_state('stop_before_forward')

        # -------------------------
        # 4. 다음 직진 전 정지
        # -------------------------
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
        """현재 위치에서 목표점까지의 각도를 계산한다."""

        angle = math.atan2(
            goal_y - y,
            goal_x - x
        )

        # -π ~ π 범위로 정규화
        return (angle + math.pi) % (2 * math.pi) - math.pi


def main(args=None):

    rclpy.init(args=args)

    node = None

    try:
        n = int(input('정다각형의 변의 개수를 입력하세요: '))

        if n < 3:
            print('3 이상의 숫자를 입력해야 합니다.')
            return

        node = PolygonController(n)

        try:
            rclpy.spin(node)

        except KeyboardInterrupt:
            pass

    except ValueError:
        print('숫자를 입력해야 합니다.')

    finally:
        if node is not None:
            node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()

