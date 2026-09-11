#!/usr/bin/env python3
"""ex06_polygon_action_server — DrawPolygon 액션 서버 (문제 6).

액션 이름 : /draw_polygon        타입 : turtle_interfaces/action/DrawPolygon
  goal     : int32 sides, float64 side_length
  feedback : int32 completed_sides, float32 progress (0~1)
  result   : float64 total_distance

시험해 보기 (삼각형·오각형·팔각형을 각각 캡처)
  ros2 action send_goal /draw_polygon turtle_interfaces/action/DrawPolygon "{sides: 3, side_length: 2.0}" --feedback
  ros2 action send_goal /draw_polygon turtle_interfaces/action/DrawPolygon "{sides: 5, side_length: 1.5}" --feedback
  ros2 action send_goal /draw_polygon turtle_interfaces/action/DrawPolygon "{sides: 8, side_length: 1.0}" --feedback
  실행 중 Ctrl+C 를 누르면 ros2 CLI 가 취소 요청을 보냅니다 → 거북이가 "즉시" 멈춰야 합니다.

=====================================================================================
왜 ReentrantCallbackGroup + MultiThreadedExecutor 인가
=====================================================================================
  execute 콜백은 다각형을 다 그릴 때까지(수 초~수십 초) 돌아가는 "긴 콜백" 입니다.
  SingleThreadedExecutor 라면 그동안 다른 콜백이 전혀 실행되지 못합니다. 그러면
    - /turtle1/pose 구독 콜백이 안 돌아서 self._latest_pose 가 갱신되지 않고 (→ 전진 거리 판정 불가)
    - 취소 요청(cancel 서비스) 콜백도 안 돌아서 goal_handle.is_cancel_requested 가 영원히 False 입니다.
  그래서 (1) 콜백들을 ReentrantCallbackGroup 에 넣어 "동시에 실행돼도 된다" 고 표시하고,
  (2) MultiThreadedExecutor 로 실제 스레드를 여러 개 돌립니다. 둘 중 하나만 하면 효과가 없습니다.

왜 "1회 발행 + sleep" 이 아니라 "주기적 연속 발행" 인가
  turtlesim 은 마지막 cmd_vel 을 약 1초만 유지하고 멈춥니다. 한 번 보내고 3초 자면 1초만 움직입니다.
  또한 취소 요청을 "즉시" 반영하려면 루프가 짧은 주기로 돌면서 매 주기 is_cancel_requested 를
  검사해야 합니다. 3초짜리 sleep 안에서는 취소를 볼 수 없습니다.

거리·각도 판정을 시간이 아니라 /turtle1/pose 로 하는 이유
  "1 m/s 로 2초" 는 이론값입니다. 실제로는 발행 지연·turtlesim 주기(62.5 Hz)·벽 충돌 때문에 어긋납니다.
  pose 로 "실제 이동량" 을 재면 결과 total_distance 도 실측치가 되고, 벽에 막혔을 때 타임아웃으로
  abort 할 수 있습니다.
"""

import math
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import (DurabilityPolicy, HistoryPolicy, QoSProfile,
                       ReliabilityPolicy)
from turtle_interfaces.action import DrawPolygon
from turtlesim.msg import Pose


def normalize_angle(a: float) -> float:
    """각도를 -pi ~ pi 로 정규화. (문제 10 의 pytest 대상 함수 중 하나)"""
    return math.atan2(math.sin(a), math.cos(a))


class _Interrupted(Exception):
    """취소 요청 또는 노드 종료로 실행 루프를 빠져나올 때 쓰는 내부 예외."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason   # 'cancel' | 'shutdown' | 'timeout'


class PolygonActionServer(Node):

    def __init__(self):
        super().__init__('polygon_action_server')

        # params.yaml (문제 9) 에서 주입되는 값들
        self.declare_parameter('linear_speed', 1.0)      # [m/s]
        self.declare_parameter('angular_speed', 1.0)     # [rad/s]
        self.declare_parameter('control_rate', 20.0)     # [Hz] cmd_vel 발행·취소 검사 주기
        self.declare_parameter('segment_timeout_factor', 3.0)  # 이론 시간의 몇 배까지 기다릴지

        self._cb_group = ReentrantCallbackGroup()
        self._latest_pose = None
        self._busy = False   # 동시에 goal 하나만 실행 (두 번째는 거절)

        qos = QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=10,
                         reliability=ReliabilityPolicy.RELIABLE,
                         durability=DurabilityPolicy.VOLATILE)
        # pose 구독도 같은 reentrant 그룹 → execute 가 도는 동안에도 계속 갱신됩니다.
        self._pose_sub = self.create_subscription(
            Pose, 'turtle1/pose', self._on_pose, qos, callback_group=self._cb_group)
        self._cmd_pub = self.create_publisher(Twist, 'turtle1/cmd_vel', 10)

        self._server = ActionServer(
            self, DrawPolygon, 'draw_polygon',
            execute_callback=self._execute,
            goal_callback=self._on_goal,          # goal 수락/거절 판단
            cancel_callback=self._on_cancel,      # 취소 요청 수락/거절 판단
            callback_group=self._cb_group,
        )
        self.get_logger().info('polygon_action_server 시작: 액션 /draw_polygon 대기 중')

    # ------------------------------------------------------------------ 콜백
    def _on_pose(self, msg: Pose):
        self._latest_pose = msg

    def _on_goal(self, goal_request: DrawPolygon.Goal):
        """goal 을 받을지 결정. 여기서 거절하면 execute 는 호출되지 않습니다."""
        if goal_request.sides < 3:
            self.get_logger().warn(f'goal 거절: sides={goal_request.sides} (3 이상이어야 함)')
            return GoalResponse.REJECT
        if goal_request.side_length <= 0.0:
            self.get_logger().warn(f'goal 거절: side_length={goal_request.side_length} (양수여야 함)')
            return GoalResponse.REJECT
        if self._busy:
            self.get_logger().warn('goal 거절: 이미 다른 다각형을 그리는 중')
            return GoalResponse.REJECT
        self.get_logger().info(f'goal 수락: sides={goal_request.sides}, side_length={goal_request.side_length}')
        return GoalResponse.ACCEPT

    def _on_cancel(self, goal_handle):
        # 취소를 "수락" 한다는 뜻일 뿐, 실제 정지는 execute 루프가 is_cancel_requested 를 보고 합니다.
        self.get_logger().warn('취소 요청 수신 — 실행 루프에서 즉시 정지합니다')
        return CancelResponse.ACCEPT

    # ------------------------------------------------------------------ 실행
    def _stop(self):
        """0 속도 Twist 발행 = 즉시 정지."""
        self._cmd_pub.publish(Twist())

    def _check_interrupt(self, goal_handle):
        """매 주기 호출: 취소 요청이나 노드 종료면 예외로 루프를 빠져나갑니다."""
        if not rclpy.ok():
            raise _Interrupted('shutdown')
        if goal_handle.is_cancel_requested:
            raise _Interrupted('cancel')

    def _drive_straight(self, goal_handle, length, v_max, period, timeout_factor):
        """pose 기준으로 length 만큼 전진. 실제 이동 거리를 반환."""
        start = self._latest_pose
        deadline = time.monotonic() + (length / v_max) * timeout_factor + 1.0
        twist = Twist()
        traveled = 0.0
        while True:
            self._check_interrupt(goal_handle)
            cur = self._latest_pose
            traveled = math.hypot(cur.x - start.x, cur.y - start.y)
            remaining = length - traveled
            if remaining <= 0.0:
                break
            if time.monotonic() > deadline:
                # 벽에 막혀 더 못 가는 경우가 대표적. turtlesim 은 벽 밖으로 못 나갑니다.
                raise _Interrupted('timeout')
            # 끝에 가까워지면 감속해 오버슈트를 줄입니다 (간단한 P 제어).
            twist.linear.x = min(v_max, max(0.2, 2.0 * remaining))
            self._cmd_pub.publish(twist)
            time.sleep(period)
        self._stop()
        return traveled

    def _turn(self, goal_handle, angle, w_max, period, timeout_factor):
        """pose 의 theta 변화량을 누적해 angle 만큼 좌회전."""
        prev = self._latest_pose.theta
        turned = 0.0
        deadline = time.monotonic() + (angle / w_max) * timeout_factor + 1.0
        twist = Twist()
        while True:
            self._check_interrupt(goal_handle)
            cur = self._latest_pose.theta
            turned += normalize_angle(cur - prev)   # theta 는 -pi~pi 로 감기므로 차이를 정규화
            prev = cur
            remaining = angle - turned
            if remaining <= 0.0:
                break
            if time.monotonic() > deadline:
                raise _Interrupted('timeout')
            twist.angular.z = min(w_max, max(0.2, 2.0 * remaining))
            self._cmd_pub.publish(twist)
            time.sleep(period)
        self._stop()

    def _execute(self, goal_handle):
        goal = goal_handle.request
        sides, length = goal.sides, goal.side_length
        v_max = self.get_parameter('linear_speed').value
        w_max = self.get_parameter('angular_speed').value
        period = 1.0 / self.get_parameter('control_rate').value
        timeout_factor = self.get_parameter('segment_timeout_factor').value
        exterior_angle = 2.0 * math.pi / sides   # 정n각형의 외각 = 한 꼭짓점에서 도는 각

        feedback = DrawPolygon.Feedback()
        result = DrawPolygon.Result()
        total = 0.0
        self._busy = True
        try:
            # pose 가 아직 없으면 잠깐 기다림 (turtlesim 이 늦게 뜬 경우)
            t0 = time.monotonic()
            while self._latest_pose is None:
                self._check_interrupt(goal_handle)
                if time.monotonic() - t0 > 3.0:
                    self.get_logger().error('/turtle1/pose 가 오지 않아 abort')
                    goal_handle.abort()
                    result.total_distance = 0.0
                    return result
                time.sleep(period)

            for i in range(sides):
                total += self._drive_straight(goal_handle, length, v_max, period, timeout_factor)
                self._turn(goal_handle, exterior_angle, w_max, period, timeout_factor)
                # 변 하나 완료 → 피드백
                feedback.completed_sides = i + 1
                feedback.progress = float(i + 1) / float(sides)
                goal_handle.publish_feedback(feedback)
                self.get_logger().info(f'변 {i + 1}/{sides} 완료 (누적 {total:.2f} m)')

            goal_handle.succeed()
            result.total_distance = total
            self.get_logger().info(f'다각형 완성: 총 이동 거리 {total:.2f} m')
            return result

        except _Interrupted as e:
            # 어떤 이유든 먼저 멈추고, 그 다음 상태를 정합니다.
            if rclpy.ok():
                self._stop()
            result.total_distance = total
            if e.reason == 'cancel':
                goal_handle.canceled()
                self.get_logger().warn(f'취소됨 — 정지. 그때까지 이동 거리 {total:.2f} m')
            elif e.reason == 'timeout':
                goal_handle.abort()
                self.get_logger().error('구간 타임아웃(벽에 막혔나요?) — abort')
            else:
                # 노드 종료 중: 상태를 못 바꿀 수 있으므로 시도만 합니다.
                try:
                    goal_handle.abort()
                except Exception:   # noqa: BLE001 — 종료 중 rcl 예외는 무시
                    pass
            return result
        finally:
            self._busy = False


def main(args=None):
    rclpy.init(args=args)
    node = PolygonActionServer()
    # 스레드 수는 최소 2 이상이어야 execute + (pose 콜백 / cancel 콜백) 이 동시에 돕니다.
    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node)
    try:
        executor.spin()
    except (KeyboardInterrupt, ExternalShutdownException):
        node.get_logger().info('Ctrl+C — 정상 종료합니다')
    finally:
        executor.shutdown(timeout_sec=1.0)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
