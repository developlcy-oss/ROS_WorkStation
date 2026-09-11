"""turtle_system.launch.py — 문제 9: 다중 노드 기동 + 파라미터 주입 + 네임스페이스.

기동하는 노드 (ros2 node list 에 이 4개가 보여야 합니다)
  /turtlesim                    turtlesim_node
  /turtle_distance_publisher    상태(원점 거리) 발행자
  /turtle_distance_subscriber   경고 구독자
  /polygon_action_server        DrawPolygon 액션 서버

launch 인자
  use_examples:=true    학생의 turtle_py 대신 turtle_examples 의 ex03_/ex06_ 노드를 띄웁니다.
                        (turtle_py 를 아직 안 만들었어도 launch 실습이 가능하도록)
  spawn_second:=true    /spawn 으로 turtle2 를 만들고, 네임스페이스 turtle2 로 두 번째 발행자를 띄웁니다.
  params_file:=<경로>   기본은 share/turtle_examples/config/params.yaml
  student_package:=turtle_py            (기본) 학생 패키지 이름
  student_action_exec:=polygon_action_server  학생 액션 서버 실행파일 이름 (다르면 바꾸세요)

실행
  ros2 launch turtle_examples turtle_system.launch.py use_examples:=true
  ros2 launch turtle_examples turtle_system.launch.py use_examples:=true spawn_second:=true
  ros2 launch turtle_examples turtle_system.launch.py             # 학생의 turtle_py 사용

파라미터 주입 방법 두 가지
  (a) launch 안에서 직접:  parameters=[{'publish_rate': 10.0}]
  (b) YAML 파일로 분리:    parameters=[params_file]          ← 이 파일이 쓰는 방식
  둘을 함께 쓰면 리스트 뒤쪽이 앞쪽을 덮어씁니다: parameters=[params_file, {'warn_distance': 1.0}]
  YAML 은 share/ 에 "설치된" 파일을 읽습니다. colcon build --symlink-install 이면 src/ 의 YAML 이
  심볼릭 링크로 연결돼 있어 수정이 재빌드 없이 바로 반영됩니다. (일반 빌드면 재빌드 필요)

=====================================================================================
네임스페이스와 토픽 이름 — 왜 절대 이름('/turtle1/pose') 을 쓰면 네임스페이스가 안 먹는가
=====================================================================================
  ROS 2 는 코드에 적힌 이름을 다음 규칙으로 "완전한 이름(FQN)" 으로 바꿉니다.
    상대 이름 'pose'          → <namespace>/pose          예) ns=turtle2 → /turtle2/pose
    상대 이름 'turtle1/pose'  → <namespace>/turtle1/pose  예) ns=turtle2 → /turtle2/turtle1/pose
    절대 이름 '/turtle1/pose' → /turtle1/pose             (namespace 무시!)
  즉 '/' 로 시작하는 이름은 "이미 완전한 이름" 이므로 launch 의 namespace= 가 손댈 곳이 없습니다.
  절대 이름을 쓴 노드를 turtle2 용으로 돌리려면 remapping 으로 이름을 강제로 바꿔야 합니다.

  이 예제(ex03_distance_publisher) 는 상대 이름 'turtle1/pose' 와 'turtle_distance' 를 씁니다.
    namespace='turtle2' 를 주면
      구독 : /turtle2/turtle1/pose   ← 존재하지 않는 토픽. remap 으로 /turtle2/pose 로 바꿔 줌
      발행 : /turtle2/turtle_distance ← 네임스페이스가 적용된 결과. ros2 topic list 에서 확인하는 항목
  remappings 의 규칙: [(코드에 적힌 이름, 바꿀 이름)]
    ('turtle1/pose', '/turtle2/pose')   상대 이름 매치 → 네임스페이스를 붙여 /turtle2/turtle1/pose 와 비교
    ('/turtle1/pose', '/turtle2/pose')  절대 이름 매치 → 학생 코드가 절대 이름을 썼을 때를 위한 규칙
    ('/turtle_distance', 'turtle_distance') 절대 발행 이름을 상대 이름으로 되돌려 네임스페이스가 붙게 함
  매치되지 않는 규칙은 그냥 무시되므로, 두 코딩 스타일을 모두 대비해 세 규칙을 함께 넣었습니다.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, LogInfo, TimerAction
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def _system_nodes(package, pub_exec, sub_exec, action_exec, params_file, condition):
    """상태 발행자 + 경고 구독자 + 액션 서버 3개를 같은 조건으로 만든다.

    name= 을 명시하는 이유: params.yaml 의 최상위 키(turtle_distance_publisher 등)는
    "노드 이름" 과 일치해야 파라미터가 주입됩니다. 실행파일 이름이 아니라 노드 이름입니다.
    """
    return [
        Node(
            package=package,
            executable=pub_exec,
            name='turtle_distance_publisher',
            parameters=[params_file],
            output='screen',
            condition=condition,
        ),
        Node(
            package=package,
            executable=sub_exec,
            name='turtle_distance_subscriber',
            parameters=[params_file],
            output='screen',
            condition=condition,
        ),
        Node(
            package=package,
            executable=action_exec,
            name='polygon_action_server',
            parameters=[params_file],
            output='screen',
            condition=condition,
        ),
    ]


def _second_publisher(package, pub_exec, params_file, condition):
    """네임스페이스 turtle2 로 띄우는 두 번째 상태 발행자 (spawn_second:=true)."""
    return Node(
        package=package,
        executable=pub_exec,
        name='turtle_distance_publisher',   # 이름은 같아도 네임스페이스가 달라 /turtle2/turtle_distance_publisher 가 됨
        namespace='turtle2',
        remappings=[
            ('turtle1/pose', '/turtle2/pose'),          # 예제 노드(상대 이름) 용
            ('/turtle1/pose', '/turtle2/pose'),         # 절대 이름을 쓴 학생 노드 용
            ('/turtle_distance', 'turtle_distance'),    # 절대 발행 이름 → 네임스페이스 적용되게
        ],
        parameters=[params_file],
        output='screen',
        condition=condition,
    )


def generate_launch_description():
    pkg_share = get_package_share_directory('turtle_examples')
    default_params = os.path.join(pkg_share, 'config', 'params.yaml')

    # ---------- launch 인자 선언 ----------
    use_examples_arg = DeclareLaunchArgument(
        'use_examples', default_value='false',
        description='true 면 turtle_examples 의 예제 노드로 시스템을 구성')
    spawn_second_arg = DeclareLaunchArgument(
        'spawn_second', default_value='false',
        description='true 면 turtle2 를 spawn 하고 네임스페이스 turtle2 로 발행자를 하나 더 띄움')
    params_file_arg = DeclareLaunchArgument(
        'params_file', default_value=default_params,
        description='노드 파라미터 YAML 경로')
    student_pkg_arg = DeclareLaunchArgument(
        'student_package', default_value='turtle_py',
        description='학생 패키지 이름')
    student_action_arg = DeclareLaunchArgument(
        'student_action_exec', default_value='polygon_action_server',
        description='학생 패키지의 DrawPolygon 액션 서버 실행파일 이름')

    use_examples = LaunchConfiguration('use_examples')
    spawn_second = LaunchConfiguration('spawn_second')
    params_file = LaunchConfiguration('params_file')
    student_pkg = LaunchConfiguration('student_package')
    student_action = LaunchConfiguration('student_action_exec')

    # ---------- turtlesim 본체 ----------
    turtlesim = Node(
        package='turtlesim',
        executable='turtlesim_node',
        name='turtlesim',
        output='screen',
    )

    # ---------- 시스템 노드 3개 (두 가지 구성 중 조건으로 하나만 활성) ----------
    example_nodes = _system_nodes(
        package='turtle_examples',
        pub_exec='ex03_distance_publisher',
        sub_exec='ex03_distance_subscriber',
        action_exec='ex06_polygon_action_server',
        params_file=params_file,
        condition=IfCondition(use_examples),
    )
    student_nodes = _system_nodes(
        package=student_pkg,
        pub_exec='turtle_distance_publisher',      # 문제 3 규격의 실행파일 이름 (고정)
        sub_exec='turtle_distance_subscriber',
        action_exec=student_action,
        params_file=params_file,
        condition=UnlessCondition(use_examples),
    )

    # ---------- spawn_second ----------
    # turtlesim 이 뜨고 서비스가 준비될 시간을 주려고 2초 뒤에 /spawn 을 호출합니다.
    spawn_turtle2 = TimerAction(
        period=2.0,
        actions=[ExecuteProcess(
            cmd=['ros2', 'service', 'call', '/spawn', 'turtlesim/srv/Spawn',
                 "{x: 2.0, y: 2.0, theta: 0.0, name: 'turtle2'}"],
            output='screen',
        )],
        condition=IfCondition(spawn_second),
    )
    # 조건이 두 개(spawn_second AND use_examples)면 PythonExpression 으로 합칩니다.
    both_true_examples = PythonExpression([
        "'", spawn_second, "'.lower() in ('true', '1') and '", use_examples, "'.lower() in ('true', '1')"])
    both_true_student = PythonExpression([
        "'", spawn_second, "'.lower() in ('true', '1') and '", use_examples, "'.lower() not in ('true', '1')"])
    second_pub_example = _second_publisher(
        'turtle_examples', 'ex03_distance_publisher', params_file, IfCondition(both_true_examples))
    second_pub_student = _second_publisher(
        student_pkg, 'turtle_distance_publisher', params_file, IfCondition(both_true_student))

    return LaunchDescription([
        use_examples_arg,
        spawn_second_arg,
        params_file_arg,
        student_pkg_arg,
        student_action_arg,
        LogInfo(msg=['params_file = ', params_file]),
        turtlesim,
        *example_nodes,
        *student_nodes,
        spawn_turtle2,
        second_pub_example,
        second_pub_student,
    ])
