"""Python 노드(talker)와 C++ 노드(listener)를 한 번에 띄우는 launch 예제.

    ros2 launch demo_bringup demo.launch.py
    ros2 launch demo_bringup demo.launch.py --show-args
    ros2 launch demo_bringup demo.launch.py publish_period:=0.2 namespace:=robot1
    ros2 launch demo_bringup demo.launch.py use_listener:=false log_level:=debug

담고 있는 것
    - DeclareLaunchArgument : 커맨드라인에서 바꿀 수 있는 인자
    - yaml 파라미터 파일 로드 + launch 인자로 개별 덮어쓰기
    - PushRosNamespace : 여러 노드를 한 네임스페이스로 묶기
    - remappings : 토픽 이름 갈아끼우기
    - IfCondition : 노드를 조건부로 띄우기
    - 로그 레벨을 --ros-args 로 넘기기
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, LogInfo
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # ------------------------------------------------------------------
    # 1) launch 인자 선언
    #    'ros2 launch demo_bringup demo.launch.py --show-args' 로 목록 확인
    # ------------------------------------------------------------------
    declared_args = [
        DeclareLaunchArgument(
            'namespace',
            default_value='demo',
            description='두 노드를 함께 넣을 ROS 네임스페이스',
        ),
        DeclareLaunchArgument(
            'topic',
            default_value='chatter',
            description='실제로 사용할 토픽 이름 (코드의 chatter 를 이걸로 remap)',
        ),
        DeclareLaunchArgument(
            'publish_period',
            default_value='1.0',
            description='talker 발행 주기 [s]. params.yaml 값을 덮어쓴다.',
        ),
        DeclareLaunchArgument(
            'use_listener',
            default_value='true',
            choices=['true', 'false'],
            description='C++ listener 노드를 띄울지 여부',
        ),
        DeclareLaunchArgument(
            'log_level',
            default_value='info',
            choices=['debug', 'info', 'warn', 'error'],
            description='두 노드에 적용할 로그 레벨',
        ),
    ]

    # 선언한 인자를 값으로 꺼내 쓰기 위한 substitution 객체.
    # 여기서는 아직 문자열이 아니고, launch 실행 시점에 평가된다.
    namespace = LaunchConfiguration('namespace')
    topic = LaunchConfiguration('topic')
    publish_period = LaunchConfiguration('publish_period')
    use_listener = LaunchConfiguration('use_listener')
    log_level = LaunchConfiguration('log_level')

    # ------------------------------------------------------------------
    # 2) 설치된 share/demo_bringup/config/params.yaml 경로 만들기
    #    소스 경로를 직접 쓰면 안 된다. colcon build 로 설치된 쪽을 가리켜야 한다.
    # ------------------------------------------------------------------
    params_file = PathJoinSubstitution(
        [FindPackageShare('demo_bringup'), 'config', 'params.yaml']
    )

    # ------------------------------------------------------------------
    # 3) 노드 정의
    # ------------------------------------------------------------------
    talker_node = Node(
        package='demo_py_pkg',          # package.xml 의 <name>
        executable='talker',            # setup.py 의 console_scripts 이름
        name='talker',                  # 실행될 노드 이름 (params.yaml 키와 매칭)
        output='screen',
        emulate_tty=True,               # 없으면 파이썬 로그가 버퍼링돼 늦게 뜬다
        parameters=[
            params_file,
            # 뒤에 오는 dict 가 yaml 값을 덮어쓴다.
            # LaunchConfiguration 은 문자열이라 그냥 넘기면 타입 에러가 난다.
            # ParameterValue 로 노드가 선언한 타입(double)을 명시해 줘야 한다.
            {'publish_period': ParameterValue(publish_period, value_type=float)},
        ],
        # 코드 안의 'chatter' 를 launch 인자 topic 으로 갈아끼운다.
        remappings=[('chatter', topic)],
        arguments=['--ros-args', '--log-level', log_level],
    )

    listener_node = Node(
        package='demo_cpp_pkg',
        executable='listener',          # CMakeLists 의 add_executable 이름
        name='listener',
        output='screen',
        emulate_tty=True,
        parameters=[params_file],
        remappings=[('chatter', topic)],
        arguments=['--ros-args', '--log-level', log_level],
        # use_listener:=false 면 이 노드는 아예 실행되지 않는다.
        condition=IfCondition(use_listener),
    )

    # ------------------------------------------------------------------
    # 4) 두 노드를 하나의 네임스페이스로 묶기
    #    PushRosNamespace 는 같은 GroupAction 안의 노드에만 적용된다.
    # ------------------------------------------------------------------
    demo_group = GroupAction([
        PushRosNamespace(namespace),
        talker_node,
        listener_node,
    ])

    return LaunchDescription([
        *declared_args,
        LogInfo(msg=['[demo_bringup] namespace=', namespace, ' topic=', topic]),
        demo_group,
    ])
