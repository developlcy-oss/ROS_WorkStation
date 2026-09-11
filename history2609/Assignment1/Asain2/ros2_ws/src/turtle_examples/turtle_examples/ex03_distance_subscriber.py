#!/usr/bin/env python3
"""ex03_distance_subscriber — /turtle_distance 경고 구독자 (launch 데모용 최소 구현).

[주의] 문제 3 의 정답이 아니라, 문제 9 launch 예제가 돌기 위한 최소 구현입니다.

규격 (고정)
  - 구독 : /turtle_distance (std_msgs/msg/Float32)
  - 파라미터 : warn_distance (double, 기본 2.5) — 이 값을 넘으면 WARN 로그
  - 실행 중 `ros2 param set /turtle_distance_subscriber warn_distance 0.8` 로 바꿀 수 있어야 합니다.

문제 9 실험: config/params.yaml 의 warn_distance 를 2.5 → 0.8 로 낮추면 재빌드 없이
경고가 훨씬 자주 찍히는 것을 확인합니다. (launch 는 share/ 에 설치된 YAML 을 읽으므로
--symlink-install 로 빌드했다면 src/ 의 YAML 수정이 바로 반영됩니다.)
"""

import rclpy
from rcl_interfaces.msg import ParameterDescriptor, SetParametersResult
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import (DurabilityPolicy, HistoryPolicy, QoSProfile,
                       ReliabilityPolicy)
from std_msgs.msg import Float32


class DistanceSubscriber(Node):

    def __init__(self):
        super().__init__('turtle_distance_subscriber')

        self.declare_parameter(
            'warn_distance', 2.5,
            ParameterDescriptor(description='이 거리[m]를 넘으면 경고 로그'))
        self._warn_distance = self.get_parameter('warn_distance').value

        # 발행자(문제 3 / ex03_distance_publisher)가 기본 QoS(Reliable, Volatile) 이므로
        # 구독자도 Reliable 로 두면 확실히 연결됩니다.
        # (문제 7 에서 발행자를 Best-Effort 로 바꾸면 이 구독자는 연결이 안 됩니다 — 의도된 실험)
        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
        )
        self._sub = self.create_subscription(Float32, 'turtle_distance', self._on_distance, qos)
        self.add_on_set_parameters_callback(self._on_set_parameters)

        self.get_logger().info(f'turtle_distance_subscriber 시작: warn_distance={self._warn_distance}')

    def _on_distance(self, msg: Float32):
        d = msg.data
        if d > self._warn_distance:
            # 10 Hz 로 들어오므로 경고도 초당 10줄 찍힙니다. 너무 시끄러우면
            # self.get_logger().warn(..., throttle_duration_sec=1.0) 처럼 스로틀을 거세요.
            self.get_logger().warn(f'경고: 원점 거리 {d:.2f} m > 임계 {self._warn_distance:.2f} m')
        else:
            self.get_logger().debug(f'거리 {d:.2f} m')   # 기본 로그 레벨(INFO)에서는 안 보임

    def _on_set_parameters(self, params):
        for p in params:
            if p.name == 'warn_distance':
                if p.type_ != Parameter.Type.DOUBLE:
                    return SetParametersResult(successful=False,
                                               reason='warn_distance 는 double 이어야 합니다 (예: 0.8)')
                if p.value < 0.0:
                    return SetParametersResult(successful=False,
                                               reason='warn_distance 는 음수일 수 없습니다')
                self._warn_distance = p.value
                self.get_logger().info(f'warn_distance 변경 → {p.value}')
        return SetParametersResult(successful=True)


def main(args=None):
    rclpy.init(args=args)
    node = DistanceSubscriber()
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
