#!/usr/bin/env python3
"""ex06_waypoint_publisher — WaypointList(경유점 4개) 를 /waypoints 로 발행 (문제 6·7).

QoS 선택 이유 (문제 7 의 "왜 이 설정이 맞는가")
  경유점 목록은 "한 번 발행되면 계속 유효한" 데이터입니다. 센서값처럼 매 주기 새로 오는 것이 아니라
  설정값에 가깝습니다. 그래서
    - Durability = TRANSIENT_LOCAL : 발행자가 마지막 메시지를 보관해 두었다가 "나중에 뜬 구독자" 에게도 줍니다.
                                     (VOLATILE 이면 발행 순간에 없던 구독자는 영원히 못 받습니다)
    - Reliability = RELIABLE       : 경유점 하나라도 빠지면 경로가 틀어지므로 재전송이 필요합니다.
    - History depth = 1            : 보관할 가치가 있는 건 "가장 최근 목록" 하나뿐입니다.
  이 조합은 ROS 2 의 "latched topic" 관용구이며, /tf_static 이나 /map 이 같은 방식을 씁니다.

실험 (문제 7)
  1) 이 노드를 먼저 띄우고 → 몇 초 뒤 `ros2 topic echo /waypoints` : TRANSIENT_LOCAL 이면 과거 메시지가 옵니다.
  2) `--ros-args -p durability:=volatile` 로 다시 띄우고 같은 실험 : 아무것도 안 옵니다.
     (Humble 의 ros2 topic echo 는 발행자 QoS 에 맞춰 자동 조정합니다. 안 되면
      `ros2 topic echo /waypoints --qos-durability transient_local --qos-reliability reliable`)
  3) ex07_qos_subscriber 로 durability 를 바꿔 가며 받아 보세요.

주의: 발행 후 노드가 살아 있어야 합니다. TRANSIENT_LOCAL 은 "발행자가 보관" 하는 것이지
      네트워크 어딘가에 남는 것이 아닙니다. 노드를 끄면 늦게 뜬 구독자는 받을 수 없습니다.
"""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import (DurabilityPolicy, HistoryPolicy, QoSProfile,
                       ReliabilityPolicy)
from turtle_interfaces.msg import Waypoint, WaypointList


class WaypointPublisher(Node):

    def __init__(self):
        super().__init__('waypoint_publisher')

        # 문제 7 실험용: transient_local | volatile
        self.declare_parameter('durability', 'transient_local')
        self.declare_parameter('frame_id', 'world')
        durability_str = self.get_parameter('durability').value
        if durability_str == 'transient_local':
            durability = DurabilityPolicy.TRANSIENT_LOCAL
        elif durability_str == 'volatile':
            durability = DurabilityPolicy.VOLATILE
        else:
            raise ValueError(f'durability 파라미터는 transient_local 또는 volatile 이어야 합니다: {durability_str}')

        # 이 예제는 "일부러" depth=1 입니다 (최근 목록 하나만 보관). 다른 예제들은 depth=10 을 씁니다.
        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=durability,
        )
        self._pub = self.create_publisher(WaypointList, 'waypoints', qos)

        # 생성 직후 바로 발행하지 않고 1초 뒤 발행합니다.
        # 이미 떠 있는 VOLATILE 구독자와의 디스커버리(서로를 찾는 과정)에 수백 ms 가 걸리는데,
        # 그 전에 발행하면 VOLATILE 실험에서 "구독자가 먼저 떠 있었는데도 못 받는" 혼란이 생깁니다.
        self._timer = self.create_timer(1.0, self._publish_once)
        self.get_logger().info(f'waypoint_publisher 시작: durability={durability_str}, '
                               'reliability=reliable, depth=1 — 1초 뒤 1회 발행')

    def _make_waypoint(self, x, y, tolerance, label) -> Waypoint:
        wp = Waypoint()
        wp.x = float(x)              # float64
        wp.y = float(y)
        wp.tolerance = float(tolerance)   # float32 (파이썬 float 를 넣으면 자동 변환)
        wp.label = label
        return wp

    def _publish_once(self):
        self._timer.cancel()   # 한 번만

        msg = WaypointList()
        # ---- Header 채우기 ----
        # stamp : 노드 시계의 현재 시각 (use_sim_time 이면 시뮬레이션 시각)
        # frame_id : 이 좌표들이 어느 좌표계 기준인지. 문제 10 의 RViz2 Fixed Frame 과 맞춥니다.
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.get_parameter('frame_id').value

        # ---- 경유점 4개 (turtlesim 화면 11x11 안의 정사각형 꼭짓점) ----
        # 배열 필드는 파이썬 list 처럼 append 하면 됩니다.
        msg.waypoints.append(self._make_waypoint(2.0, 2.0, 0.3, 'corner_A'))
        msg.waypoints.append(self._make_waypoint(9.0, 2.0, 0.3, 'corner_B'))
        msg.waypoints.append(self._make_waypoint(9.0, 9.0, 0.3, 'corner_C'))
        msg.waypoints.append(self._make_waypoint(2.0, 9.0, 0.3, 'corner_D'))

        self._pub.publish(msg)
        labels = [wp.label for wp in msg.waypoints]
        self.get_logger().info(f'/waypoints 발행: {len(msg.waypoints)}개 {labels} '
                               f'(frame_id={msg.header.frame_id}). '
                               '`ros2 topic echo /waypoints` 로 중첩 필드를 확인하세요')


def main(args=None):
    rclpy.init(args=args)
    node = WaypointPublisher()
    try:
        rclpy.spin(node)   # 발행 후에도 계속 살아 있어야 늦게 뜬 구독자가 받을 수 있음
    except (KeyboardInterrupt, ExternalShutdownException):
        node.get_logger().info('Ctrl+C — 정상 종료합니다')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
