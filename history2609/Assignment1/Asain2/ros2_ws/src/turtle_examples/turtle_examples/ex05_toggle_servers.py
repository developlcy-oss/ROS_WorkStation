#!/usr/bin/env python3
"""ex05_toggle_servers — 자체 서비스 서버 예제 (문제 5, 문제 3 노드에 붙일 구조).

이 노드가 제공하는 서비스
  /enable_driving  std_srvs/srv/SetBool   data=true 면 cmd_vel 발행 시작, false 면 즉시 정지·발행 중단
  /save_home       std_srvs/srv/Trigger   현재 /turtle1/pose 를 "홈" 으로 저장
  /go_home         std_srvs/srv/Trigger   저장한 홈으로 순간이동 — "콜백 안에서 다른 서비스를 올바르게(비동기) 부르는" 예

시험해 보기
  ros2 service call /enable_driving std_srvs/srv/SetBool "{data: true}"
  ros2 service call /save_home      std_srvs/srv/Trigger
  ros2 service call /enable_driving std_srvs/srv/SetBool "{data: false}"
  ros2 service call /go_home        std_srvs/srv/Trigger

구조: "타이머가 발행하고, 서비스는 플래그만 바꾼다"
  cmd_vel 발행은 타이머 콜백 한 곳에서만 합니다. SetBool 서버는 self._enabled 플래그만 바꾸고
  바로 응답합니다. 이렇게 하면 서비스 콜백이 짧게 끝나고(응답 지연 없음), "발행을 멈춘다" 는
  요구가 타이머의 if 문 하나로 해결됩니다.

=====================================================================================
[중요] 구독/서비스 콜백 안에서 다른 서비스 응답을 "동기로" 기다리면 왜 데드락인가
=====================================================================================
  rclpy.spin(node) 는 기본적으로 SingleThreadedExecutor 를 씁니다. 이 executor 는
  "한 번에 콜백 하나" 만 실행합니다. 콜백이 끝나야 다음 이벤트(다른 콜백, 서비스 응답 도착 처리)를 봅니다.

  잘못된 코드 (실행하지 마세요):

      def _on_go_home_WRONG(self, request, response):
          future = self._teleport_cli.call_async(req)
          rclpy.spin_until_future_complete(self, future)   # (a) 또는
          result = self._teleport_cli.call(req)             # (b) 동기 호출
          ...

  왜 멈추는가 (executor 관점, 3줄):
    1. 우리는 지금 executor 의 "유일한 실행 손" 안(콜백 내부)에 있습니다.
    2. teleport 의 "응답" 도 같은 executor 가 wait-set 에서 꺼내 future 에 넣어 줘야 완료됩니다.
    3. 그런데 그 손은 우리 콜백이 끝나기를 기다리고, 우리 콜백은 응답을 기다립니다 → 순환 대기(데드락).
  (a) 의 spin_until_future_complete 는 "이미 돌고 있는 executor 안에서 또 spin" 하려는 것이라
  Humble 에서는 그냥 멈추거나 executor 상태가 꼬입니다. (b) 는 rclpy 문서에도 "콜백 안에서 쓰지 말라" 고 명시돼 있습니다.

  올바른 패턴 = 아래 _on_go_home():
    call_async() 로 요청만 보내고, future.add_done_callback() 으로 "응답이 오면 할 일" 을 등록한 뒤
    서비스 콜백은 즉시 응답을 반환합니다. 응답 처리는 나중에 executor 가 별도 콜백으로 실행합니다.
    (MultiThreadedExecutor + 별도 CallbackGroup 으로 "우회" 할 수도 있지만, 콜백을 오래 붙잡는
    설계 자체가 나쁘므로 비동기 패턴이 정답입니다.)
"""

import math

import rclpy
from geometry_msgs.msg import Twist
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import (DurabilityPolicy, HistoryPolicy, QoSProfile,
                       ReliabilityPolicy)
from std_srvs.srv import SetBool, Trigger
from turtlesim.msg import Pose
from turtlesim.srv import TeleportAbsolute


class ToggleServers(Node):

    def __init__(self):
        super().__init__('turtle_toggle_servers')

        # 시작 시 주행 여부. 기본 false → SetBool 로 켜기 전까지 거북이가 움직이지 않습니다.
        self.declare_parameter('start_enabled', False)
        self.declare_parameter('linear_speed', 1.0)     # [m/s]
        self.declare_parameter('angular_speed', 0.8)    # [rad/s] → 원을 그리며 돕니다
        self._enabled = self.get_parameter('start_enabled').value

        self._latest_pose = None    # 구독 콜백이 채움
        self._home = None           # (x, y, theta) — save_home 이 채움

        qos = QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=10,
                         reliability=ReliabilityPolicy.RELIABLE,
                         durability=DurabilityPolicy.VOLATILE)
        self._pose_sub = self.create_subscription(Pose, 'turtle1/pose', self._on_pose, qos)
        self._cmd_pub = self.create_publisher(Twist, 'turtle1/cmd_vel', 10)

        # cmd_vel 은 10 Hz 타이머에서만 발행
        self._timer = self.create_timer(0.1, self._on_timer)

        # ---------- 서비스 서버 ----------
        # create_service(타입, 이름, 콜백). 콜백 시그니처는 (request, response) → response
        self._enable_srv = self.create_service(SetBool, 'enable_driving', self._on_enable_driving)
        self._save_srv = self.create_service(Trigger, 'save_home', self._on_save_home)
        self._go_home_srv = self.create_service(Trigger, 'go_home', self._on_go_home)

        # go_home 이 사용할 내장 서비스 클라이언트
        self._teleport_cli = self.create_client(TeleportAbsolute, 'turtle1/teleport_absolute')

        self.get_logger().info(f'toggle_servers 시작 (주행 {"ON" if self._enabled else "OFF"}). '
                               '서비스: /enable_driving /save_home /go_home')

    # ------------------------------------------------------------------ 콜백
    def _on_pose(self, msg: Pose):
        self._latest_pose = msg

    def _on_timer(self):
        # SetBool 이 false 면 "아무것도 발행하지 않는다". (0 Twist 를 계속 보내는 것도 방법이지만,
        # 다른 노드가 같은 거북이를 조종할 때 서로 덮어쓰지 않도록 아예 발행을 멈추는 편이 낫습니다.)
        if not self._enabled:
            return
        twist = Twist()
        twist.linear.x = self.get_parameter('linear_speed').value
        twist.angular.z = self.get_parameter('angular_speed').value
        self._cmd_pub.publish(twist)

    def _on_enable_driving(self, request: SetBool.Request, response: SetBool.Response):
        self._enabled = request.data
        if not self._enabled:
            # 끌 때는 0 속도를 한 번 보내 즉시 정지시킵니다.
            # (turtlesim 은 마지막 cmd_vel 을 약 1초간 유지하므로, 안 보내면 잠깐 더 미끄러집니다.)
            self._cmd_pub.publish(Twist())
        response.success = True
        response.message = f'driving {"enabled" if self._enabled else "disabled"}'
        self.get_logger().info(f'/enable_driving ← data={request.data} → {response.message}')
        return response

    def _on_save_home(self, request: Trigger.Request, response: Trigger.Response):
        if self._latest_pose is None:
            response.success = False
            response.message = '아직 /turtle1/pose 를 받지 못해 홈을 저장할 수 없습니다'
        else:
            p = self._latest_pose
            self._home = (p.x, p.y, p.theta)
            response.success = True
            response.message = f'home saved: x={p.x:.2f} y={p.y:.2f} theta={p.theta:.2f}'
        self.get_logger().info(f'/save_home → {response.message}')
        return response

    def _on_go_home(self, request: Trigger.Request, response: Trigger.Response):
        """올바른 비동기 패턴: 요청만 보내고 즉시 응답, 결과는 done 콜백에서 처리."""
        if self._home is None:
            response.success = False
            response.message = '저장된 홈이 없습니다. 먼저 /save_home 을 호출하세요'
            return response
        # 서버가 없으면 wait_for_service 로 "기다리지" 말고(콜백을 붙잡게 됨) 바로 실패로 응답합니다.
        if not self._teleport_cli.service_is_ready():
            response.success = False
            response.message = '/turtle1/teleport_absolute 서버가 없습니다 (turtlesim 실행 중?)'
            return response

        req = TeleportAbsolute.Request()
        req.x, req.y, req.theta = self._home
        future = self._teleport_cli.call_async(req)          # 여기서 블록되지 않음
        future.add_done_callback(self._on_teleport_done)     # 응답 도착 시 executor 가 호출

        # 이 시점에 teleport 는 아직 "완료되지 않았을 수" 있습니다. 그래서 응답 메시지도 "요청함" 으로 씁니다.
        response.success = True
        response.message = f'teleport 요청 전송: ({req.x:.2f}, {req.y:.2f}, {req.theta:.2f}) — 결과는 로그 참조'
        self.get_logger().info(f'/go_home → {response.message}')
        return response

    def _on_teleport_done(self, future):
        # done 콜백은 "서비스 콜백이 끝난 뒤" executor 가 따로 실행합니다. 데드락이 없습니다.
        if future.exception() is not None:
            self.get_logger().error(f'teleport 실패: {future.exception()}')
        else:
            self.get_logger().info('teleport 완료 — 홈으로 이동했습니다')


def main(args=None):
    rclpy.init(args=args)
    node = ToggleServers()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        node.get_logger().info('Ctrl+C — 정상 종료합니다')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
