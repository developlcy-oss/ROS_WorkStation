#!/usr/bin/env python3
"""ex05_rotate_absolute_client — turtlesim 내장 액션 RotateAbsolute 클라이언트 (문제 5).

액션 정의 (ros2 interface show turtlesim/action/RotateAbsolute)
  float32 theta      ← goal     : 목표 절대 각도 [rad]
  ---
  float32 delta      ← result   : 실제로 회전한 양
  ---
  float32 remaining  ← feedback : 남은 각도

사용법
  ros2 run turtle_examples ex05_rotate_absolute_client --theta 3.0
  ros2 run turtle_examples ex05_rotate_absolute_client --theta 3.0 --cancel-after 1.0
      → 1.0 초 뒤 cancel_goal_async() 를 보내고, 그 시점의 /turtle1/pose theta 를 기록합니다.

액션 클라이언트의 3단계 (모두 Future 기반 비동기)
  1. send_goal_async(goal, feedback_callback=...)  → Future[ClientGoalHandle]  (수락/거절)
  2. goal_handle.get_result_async()                → Future[result + status]   (완료)
  3. goal_handle.cancel_goal_async()               → Future[CancelGoal.Response]

[중요] 콜백 안에서 rclpy.shutdown() 을 호출하지 마세요.
  콜백은 executor 가 실행 중입니다. 그 안에서 컨텍스트를 내리면 executor 가 wait-set 을
  정리하는 도중 예외가 나거나 "context already shutdown" 이 터집니다.
  → 콜백은 self.done = True 플래그만 세우고, main() 의 spin 루프가 그 플래그를 보고 빠져나온 뒤
    정상 순서(destroy_node → shutdown) 로 종료합니다.
"""

import argparse
import math
import sys

import rclpy
from action_msgs.msg import GoalStatus
from action_msgs.srv import CancelGoal
from rclpy.action import ActionClient
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import (DurabilityPolicy, HistoryPolicy, QoSProfile,
                       ReliabilityPolicy)
from rclpy.utilities import remove_ros_args
from turtlesim.action import RotateAbsolute
from turtlesim.msg import Pose

STATUS_NAME = {
    GoalStatus.STATUS_SUCCEEDED: 'SUCCEEDED',
    GoalStatus.STATUS_CANCELED: 'CANCELED',
    GoalStatus.STATUS_ABORTED: 'ABORTED',
}


class RotateAbsoluteClient(Node):

    def __init__(self, target_theta: float, cancel_after):
        super().__init__('rotate_absolute_client')
        self._target = target_theta
        self._cancel_after = cancel_after     # None 이면 취소하지 않음

        # 액션 이름도 상대 이름. → /turtle1/rotate_absolute
        self._client = ActionClient(self, RotateAbsolute, 'turtle1/rotate_absolute')

        # 취소 시점의 각도를 기록하려고 /turtle1/pose 도 구독합니다.
        qos = QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=10,
                         reliability=ReliabilityPolicy.RELIABLE,
                         durability=DurabilityPolicy.VOLATILE)
        self._pose_sub = self.create_subscription(Pose, 'turtle1/pose', self._on_pose, qos)
        self._latest_theta = None

        self._goal_handle = None
        self._cancel_timer = None
        self.done = False     # main 루프 종료 플래그 (콜백은 이것만 세운다)

    # ------------------------------------------------------------------
    def _on_pose(self, msg: Pose):
        self._latest_theta = msg.theta

    def send_goal(self):
        if not self._client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('액션 서버 /turtle1/rotate_absolute 가 없습니다 (turtlesim 실행 중?)')
            self.done = True
            return
        goal = RotateAbsolute.Goal()
        goal.theta = float(self._target)
        self.get_logger().info(f'goal 전송: theta = {goal.theta:.3f} rad '
                               f'(현재 theta = {self._latest_theta})')
        send_future = self._client.send_goal_async(goal, feedback_callback=self._on_feedback)
        send_future.add_done_callback(self._on_goal_response)

    def _on_goal_response(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('goal 이 거절되었습니다')
            self.done = True
            return
        self.get_logger().info('goal 수락됨 — 피드백 대기')
        self._goal_handle = goal_handle
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._on_result)

        # --cancel-after 가 주어졌으면 그 시점에 취소하는 타이머를 겁니다.
        if self._cancel_after is not None:
            self._cancel_timer = self.create_timer(self._cancel_after, self._on_cancel_timer)

    def _on_feedback(self, feedback_msg):
        # feedback_msg.feedback 이 실제 Feedback 메시지입니다.
        remaining = feedback_msg.feedback.remaining
        # turtlesim 은 매 주기(약 62.5 Hz) 피드백을 보내므로 0.25 초에 한 번만 찍습니다.
        self.get_logger().info(f'피드백: remaining = {remaining:+.3f} rad',
                               throttle_duration_sec=0.25)

    def _on_cancel_timer(self):
        self._cancel_timer.cancel()               # 한 번만 실행되도록
        theta_at_cancel = self._latest_theta      # 취소 "요청 시점" 의 각도 기록
        self.get_logger().warn(f'취소 요청 전송 (요청 시점 theta = {theta_at_cancel:.3f} rad)')
        cancel_future = self._goal_handle.cancel_goal_async()
        cancel_future.add_done_callback(
            lambda f: self._on_cancel_response(f, theta_at_cancel))

    def _on_cancel_response(self, future, theta_at_cancel):
        resp = future.result()
        # return_code: ERROR_NONE(0) 이고 goals_canceling 에 우리 goal 이 있으면 취소가 "수락" 된 것.
        # 취소가 수락됐다고 끝난 건 아닙니다 — 실제 종료는 _on_result 의 status 로 확인합니다.
        if resp.return_code == CancelGoal.Response.ERROR_NONE and len(resp.goals_canceling) > 0:
            self.get_logger().warn(f'취소 수락됨 (서버가 중단 처리 중). 취소 시점 theta = {theta_at_cancel:.3f} rad')
        else:
            self.get_logger().error(f'취소 거절: return_code={resp.return_code} '
                                    '(이미 끝난 goal 이면 ERROR_GOAL_TERMINATED=3)')

    def _on_result(self, future):
        wrapped = future.result()
        status = wrapped.status
        result = wrapped.result
        name = STATUS_NAME.get(status, str(status))
        self.get_logger().info(f'결과 수신: status={name}, delta={result.delta:+.3f} rad, '
                               f'현재 theta = {self._latest_theta}')
        # 여기서 rclpy.shutdown() 을 부르지 않습니다. 플래그만 세웁니다.
        self.done = True


def main(args=None):
    rclpy.init(args=args)
    # ROS 인자(--ros-args ...) 를 걷어낸 나머지만 argparse 에 넘깁니다.
    parser = argparse.ArgumentParser(description='turtlesim RotateAbsolute action client')
    parser.add_argument('--theta', type=float, default=math.pi / 2,
                        help='목표 절대 각도 [rad] (기본 pi/2)')
    parser.add_argument('--cancel-after', type=float, default=None,
                        help='이 시간[초] 뒤 취소 요청을 보냄 (생략하면 취소 안 함)')
    cli = parser.parse_args(remove_ros_args(sys.argv)[1:])

    node = RotateAbsoluteClient(cli.theta, cli.cancel_after)
    try:
        node.send_goal()
        # spin() 대신 spin_once 루프: done 플래그가 서면 빠져나와 정상 종료합니다.
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.1)
    except (KeyboardInterrupt, ExternalShutdownException):
        node.get_logger().info('Ctrl+C — 중단합니다')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
