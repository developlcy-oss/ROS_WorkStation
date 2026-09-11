#!/usr/bin/env python3
"""ex03_distance_publisher — 거북이 원점 거리 발행자 (launch 데모용 최소 구현).

[주의] 이 파일은 문제 3 의 "정답" 이 아닙니다. 문제 9 launch 예제가 turtle_examples
패키지만으로도 돌아가도록 넣어 둔 최소 구현입니다. 학생은 문제 3 규격을 자신의
turtle_py 패키지에 직접 구현해야 합니다. (정사각형 주행 노드 등은 여기 없습니다.)

규격 (고정)
  - 구독 : /turtle1/pose      (turtlesim/msg/Pose)
  - 발행 : /turtle_distance   (std_msgs/msg/Float32), 10 Hz
  - 파라미터 : publish_rate (double, 기본 10.0) — 실행 중 변경 가능
  - 구독 콜백은 최신 자세를 "보관만" 하고, 발행은 "타이머 콜백" 에서 합니다.

왜 구독 콜백에서 바로 발행하지 않는가?
  /turtle1/pose 는 turtlesim 이 약 62.5 Hz 로 쏩니다. 콜백에서 바로 발행하면 발행
  주기가 "입력 주기" 에 묶여 버립니다. 타이머로 분리하면 입력이 몇 Hz 든 우리가 정한
  publish_rate 로 발행할 수 있고, 파라미터로 주기를 바꾸는 것도 가능해집니다.
"""

import math

import rclpy
from rcl_interfaces.msg import ParameterDescriptor, SetParametersResult
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import (DurabilityPolicy, HistoryPolicy, QoSProfile,
                       ReliabilityPolicy, qos_profile_sensor_data)
from std_msgs.msg import Float32
from turtlesim.msg import Pose


class DistancePublisher(Node):

    def __init__(self):
        # 노드 이름. launch 의 params.yaml 은 이 이름으로 파라미터를 찾습니다.
        super().__init__('turtle_distance_publisher')

        # ---------- 파라미터 선언 ----------
        # declare 하지 않은 파라미터는 `ros2 param set` 으로 설정할 수 없습니다.
        # 기본값의 타입(10.0 → double) 이 곧 파라미터 타입이 됩니다.
        #  → `ros2 param set /turtle_distance_publisher publish_rate 5` (int) 는 거부되고
        #    `... publish_rate 5.0` 처럼 소수점을 붙여야 합니다.
        self.declare_parameter(
            'publish_rate', 10.0,
            ParameterDescriptor(description='/turtle_distance 발행 주기 [Hz], 0 보다 커야 함'))
        rate = self.get_parameter('publish_rate').value

        # ---------- 상태 ----------
        # 구독 콜백은 여기에 최신 자세를 저장만 합니다.
        self._latest_pose = None

        # ---------- 구독 ----------
        # turtlesim 은 /turtle1/pose 를 "기본 QoS(Reliable, Volatile, depth 10)" 로 발행합니다.
        # 센서성 데이터라 qos_profile_sensor_data(Best-Effort) 로 받아도 연결됩니다.
        # (발행자 Reliable + 구독자 Best-Effort 는 호환. 반대는 비호환 — 문제 7)
        # 여기서는 명시적으로 QoSProfile 을 조립해 각 항목이 무엇인지 보여 줍니다.
        pose_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
        )
        _ = qos_profile_sensor_data  # 대안: create_subscription(..., qos_profile_sensor_data)

        # 토픽 이름을 'turtle1/pose' 처럼 "상대 이름" 으로 적었습니다.
        #  - 네임스페이스 없이 실행하면 /turtle1/pose 로 풀립니다.
        #  - launch 에서 namespace='turtle2' 를 주면 /turtle2/turtle1/pose 로 풀리므로
        #    remappings=[('turtle1/pose', '/turtle2/pose')] 로 바꿔 줍니다. (문제 9 launch 주석 참고)
        # '/turtle1/pose' 처럼 절대 이름을 쓰면 네임스페이스가 전혀 적용되지 않습니다.
        self._pose_sub = self.create_subscription(
            Pose, 'turtle1/pose', self._on_pose, pose_qos)

        # ---------- 발행 ----------
        # 'turtle_distance' 도 상대 이름 → 기본 /turtle_distance, 네임스페이스 turtle2 면 /turtle2/turtle_distance.
        # 세 번째 인자 10 은 depth=10 인 기본 QoS(Reliable, Volatile, KEEP_LAST) 의 축약형입니다.
        self._dist_pub = self.create_publisher(Float32, 'turtle_distance', 10)

        # ---------- 타이머 ----------
        self._timer = self.create_timer(1.0 / rate, self._on_timer)

        # ---------- 파라미터 변경 콜백 ----------
        # `ros2 param set` 이 들어오면 값이 "적용되기 전에" 이 콜백이 먼저 불립니다.
        # 여기서 거부(successful=False) 하면 값이 바뀌지 않습니다.
        self.add_on_set_parameters_callback(self._on_set_parameters)

        self.get_logger().info(f'turtle_distance_publisher 시작: publish_rate={rate} Hz')

    # ------------------------------------------------------------------
    def _on_pose(self, msg: Pose):
        # 최신 자세만 보관. 계산·발행은 타이머에서.
        self._latest_pose = msg

    def _on_timer(self):
        if self._latest_pose is None:
            # turtlesim 이 아직 안 떴거나 토픽 이름이 틀린 경우. 1초에 한 번만 경고.
            self.get_logger().warn('아직 /turtle1/pose 를 받지 못했습니다',
                                   throttle_duration_sec=1.0)
            return
        p = self._latest_pose
        msg = Float32()
        msg.data = math.hypot(p.x, p.y)   # 원점(0,0)에서의 거리
        self._dist_pub.publish(msg)

    def _on_set_parameters(self, params):
        """파라미터 변경 검증 + 타이머 재생성.

        주의: 이 콜백 안에서 self.get_parameter('publish_rate') 를 읽으면 "옛 값" 이 나옵니다.
        새 값은 인자로 들어온 params[i].value 에서 읽어야 합니다.
        """
        for p in params:
            if p.name != 'publish_rate':
                continue
            if p.type_ != Parameter.Type.DOUBLE:
                return SetParametersResult(
                    successful=False, reason='publish_rate 는 double 이어야 합니다 (예: 5.0)')
            if p.value <= 0.0:
                return SetParametersResult(
                    successful=False, reason='publish_rate 는 0 보다 커야 합니다')
            # 타이머는 주기를 바꾸는 API 가 없으므로 "파괴 후 재생성" 합니다.
            self.destroy_timer(self._timer)
            self._timer = self.create_timer(1.0 / p.value, self._on_timer)
            self.get_logger().info(f'publish_rate 변경 → {p.value} Hz (타이머 재생성)')
        return SetParametersResult(successful=True)


def main(args=None):
    # ---------- 노드 생명주기 ----------
    # 1. rclpy.init      : rcl 컨텍스트 초기화 + 시그널 핸들러 설치
    # 2. Node 생성       : 이 시점에 그래프(DDS)에 참여
    # 3. spin            : 콜백(구독/타이머/서비스) 처리 루프. Ctrl+C 까지 여기서 블록
    # 4. destroy_node    : 퍼블리셔/구독/타이머를 명시적으로 해제
    # 5. rclpy.shutdown  : 컨텍스트 종료
    rclpy.init(args=args)
    node = DistancePublisher()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        # Ctrl+C : Humble 의 rclpy 는 SIGINT 를 받으면 컨텍스트를 먼저 내리고(shutdown)
        # 그 다음 KeyboardInterrupt 를 던집니다. 그래서 아래에서 rclpy.ok() 로 가드하지 않으면
        # "rcl_shutdown already called" 예외가 나면서 "정상 종료" 가 아니게 됩니다.
        node.get_logger().info('Ctrl+C — 정상 종료합니다')
    finally:
        node.destroy_node()
        if rclpy.ok():          # 이중 shutdown 방지
            rclpy.shutdown()


if __name__ == '__main__':
    main()
