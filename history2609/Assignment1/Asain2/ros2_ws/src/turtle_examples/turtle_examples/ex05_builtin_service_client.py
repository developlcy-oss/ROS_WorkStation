#!/usr/bin/env python3
"""ex05_builtin_service_client — turtlesim 내장 서비스 4개를 순서대로 비동기 호출.

호출 순서 (문제 5 규격)
  1. /turtle1/teleport_absolute  turtlesim/srv/TeleportAbsolute  거북이를 (x, y, theta) 로 순간이동
  2. /turtle1/set_pen            turtlesim/srv/SetPen            펜 색(r,g,b)·굵기(width)·on/off
  3. /spawn                      turtlesim/srv/Spawn             거북이 추가 → 응답으로 이름 반환
  4. /clear                      std_srvs/srv/Empty              궤적 지우기 (요청·응답 필드 없음)

호출 전에 반드시 직접 확인해 report.md 에 기록하세요:
  ros2 service list
  ros2 service type /turtle1/teleport_absolute
  ros2 interface show turtlesim/srv/TeleportAbsolute

핵심 패턴: call_async() + rclpy.spin_until_future_complete()
  - call_async 는 "요청을 보내고 즉시 Future 를 돌려줍니다". 응답은 나중에 Future 에 담깁니다.
  - spin_until_future_complete 는 Future 가 완료될 때까지 executor 를 돌려 줍니다.
    (응답 메시지는 executor 가 돌아야 수신·처리되므로, 그냥 while 루프로 기다리면 영원히 안 옵니다)
  - 이 파일은 main() 에서 순차적으로 호출하므로 "콜백 안에서 spin" 하는 상황이 아니고, 데드락이 없습니다.
    콜백 안에서 같은 짓을 하면 왜 멈추는지는 ex05_toggle_servers.py 의 주석을 보세요.
"""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_srvs.srv import Empty
from turtlesim.srv import SetPen, Spawn, TeleportAbsolute


class BuiltinServiceClient(Node):

    def __init__(self):
        super().__init__('builtin_service_client')
        # 클라이언트 생성은 "이 타입으로 이 이름의 서비스를 부르겠다" 는 선언일 뿐,
        # 서버가 실제로 떠 있는지는 wait_for_service 로 확인해야 합니다.
        self.teleport_cli = self.create_client(TeleportAbsolute, '/turtle1/teleport_absolute')
        self.set_pen_cli = self.create_client(SetPen, '/turtle1/set_pen')
        self.spawn_cli = self.create_client(Spawn, '/spawn')
        self.clear_cli = self.create_client(Empty, '/clear')

    def call(self, client, request, timeout_sec=5.0):
        """서비스 하나를 비동기로 호출하고 응답이 올 때까지 기다린다. 실패하면 None."""
        name = client.srv_name
        # 1) 서버 대기. turtlesim_node 가 안 떠 있으면 여기서 timeout.
        if not client.wait_for_service(timeout_sec=timeout_sec):
            self.get_logger().error(f'{name}: 서버가 {timeout_sec}s 안에 뜨지 않았습니다 '
                                    '(turtlesim_node 가 실행 중인가요?)')
            return None
        # 2) 요청 전송 → Future 즉시 반환 (여기서 블록되지 않음)
        future = client.call_async(request)
        # 3) Future 완료까지 spin. 이 동안 다른 콜백도 함께 처리됩니다.
        rclpy.spin_until_future_complete(self, future, timeout_sec=timeout_sec)
        if not future.done():
            self.get_logger().error(f'{name}: {timeout_sec}s 안에 응답이 없습니다')
            return None
        if future.exception() is not None:
            self.get_logger().error(f'{name}: 예외 {future.exception()}')
            return None
        return future.result()

    def run_sequence(self):
        """네 서비스를 순서대로 호출하고 각 결과를 로그로 남긴다."""
        # ---- 1. teleport_absolute : 화면 중앙(5.5, 5.5), theta=0 ----
        req = TeleportAbsolute.Request()
        req.x, req.y, req.theta = 5.5, 5.5, 0.0
        res = self.call(self.teleport_cli, req)
        # TeleportAbsolute 의 응답은 필드가 없습니다. "None 이 아니다" = 성공.
        self.get_logger().info(f'[1/4] teleport_absolute({req.x}, {req.y}, {req.theta}) '
                               f'→ {"OK" if res is not None else "FAIL"}')

        # ---- 2. set_pen : 빨간색, 굵기 4, off=0(펜 내림) ----
        req = SetPen.Request()
        req.r, req.g, req.b, req.width, req.off = 255, 0, 0, 4, 0
        res = self.call(self.set_pen_cli, req)
        self.get_logger().info(f'[2/4] set_pen(r={req.r}, g={req.g}, b={req.b}, width={req.width}, off={req.off}) '
                               f'→ {"OK" if res is not None else "FAIL"}')

        # ---- 3. spawn : (2.0, 2.0) 에 turtle2 추가 ----
        req = Spawn.Request()
        req.x, req.y, req.theta, req.name = 2.0, 2.0, 0.0, 'turtle2'
        res = self.call(self.spawn_cli, req)
        if res is None:
            self.get_logger().info('[3/4] spawn → FAIL')
        elif res.name == '':
            # 같은 이름이 이미 있으면 turtlesim 은 빈 이름을 돌려줍니다 (turtlesim 쪽에 에러 로그).
            self.get_logger().warn('[3/4] spawn → 빈 이름 반환 (이미 turtle2 가 있나요?)')
        else:
            self.get_logger().info(f'[3/4] spawn → 새 거북이 이름 "{res.name}" '
                                   f'(ros2 topic list 에서 /{res.name}/pose 확인)')

        # ---- 4. clear : 궤적 지우기 (Empty 는 요청 필드가 없음) ----
        res = self.call(self.clear_cli, Empty.Request())
        self.get_logger().info(f'[4/4] clear → {"OK" if res is not None else "FAIL"}')


def main(args=None):
    rclpy.init(args=args)
    node = BuiltinServiceClient()
    try:
        # 이 노드는 spin() 으로 계속 도는 노드가 아니라 "한 번 일하고 끝나는" 노드입니다.
        # 그래서 spin 대신 run_sequence() 를 부르고, 각 호출 안에서 spin_until_future_complete 로
        # 필요한 만큼만 executor 를 돌립니다.
        node.run_sequence()
    except (KeyboardInterrupt, ExternalShutdownException):
        node.get_logger().info('Ctrl+C — 중단합니다')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
