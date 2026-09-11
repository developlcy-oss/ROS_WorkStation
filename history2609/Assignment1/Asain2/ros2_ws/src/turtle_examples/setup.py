import os
from glob import glob

from setuptools import setup

package_name = 'turtle_examples'

setup(
    name=package_name,
    version='0.1.0',
    # 파이썬 모듈 디렉터리 (turtle_examples/__init__.py 가 있는 폴더)
    packages=[package_name],
    # ------------------------------------------------------------------
    # data_files : 파이썬 코드가 "아닌" 파일을 install/ 아래 어디에 복사할지 지정.
    #  - resource/turtle_examples : ament 인덱스 마커. 이 파일이 있어야
    #    `ros2 pkg list` 와 `ros2 run` 이 이 패키지를 찾습니다.
    #  - package.xml            : share/turtle_examples/ 에 복사 (의존성 정보)
    #  - launch/*.launch.py     : share/turtle_examples/launch/  ← 문제 9
    #  - config/*.yaml          : share/turtle_examples/config/  ← 문제 9
    #    launch 파일은 get_package_share_directory('turtle_examples') 로
    #    share 경로를 얻어 config/params.yaml 을 읽습니다. 여기서 설치하지 않으면
    #    "file not found" 로 launch 가 실패합니다.
    # ------------------------------------------------------------------
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='student',
    maintainer_email='student@example.com',
    description='Physical AI Lv.1 module 2 (turtlesim) example nodes for problems 5-9',
    license='Apache-2.0',
    tests_require=['pytest'],
    # ------------------------------------------------------------------
    # [문제 8] entry_points / console_scripts
    #
    #   '실행파일이름 = 파이썬패키지.모듈:함수'
    #
    #  - 왼쪽 "실행파일이름" 이 `ros2 run turtle_examples <실행파일이름>` 에 쓰이는 이름입니다.
    #  - 오른쪽은 "어떤 모듈의 어떤 함수를 호출할지" 입니다. 모든 예제는 main() 을 진입점으로 둡니다.
    #  - colcon build 가 끝나면 install/turtle_examples/lib/turtle_examples/ 아래에
    #    같은 이름의 작은 래퍼 스크립트가 생성됩니다. (setup.cfg 의 install_scripts 가 그 위치를 지정)
    #  - 여기 등록하지 않은 노드는 파일이 있어도 `ros2 run` 으로 실행할 수 없습니다.
    #    노드를 새로 만들면 (1) 파일 추가 (2) 여기 한 줄 추가 (3) colcon build 재실행, 세 단계입니다.
    #    --symlink-install 로 빌드했더라도 setup.py 를 바꾼 뒤에는 재빌드가 필요합니다.
    # ------------------------------------------------------------------
    entry_points={
        'console_scripts': [
            # 문제 3 (launch 데모용 최소 구현)
            'ex03_distance_publisher = turtle_examples.ex03_distance_publisher:main',
            'ex03_distance_subscriber = turtle_examples.ex03_distance_subscriber:main',
            # 문제 5
            'ex05_builtin_service_client = turtle_examples.ex05_builtin_service_client:main',
            'ex05_toggle_servers = turtle_examples.ex05_toggle_servers:main',
            'ex05_rotate_absolute_client = turtle_examples.ex05_rotate_absolute_client:main',
            # 문제 6
            'ex06_polygon_action_server = turtle_examples.ex06_polygon_action_server:main',
            'ex06_waypoint_publisher = turtle_examples.ex06_waypoint_publisher:main',
            # 문제 7
            'ex07_qos_sensor_publisher = turtle_examples.ex07_qos_sensor_publisher:main',
            'ex07_qos_subscriber = turtle_examples.ex07_qos_subscriber:main',
        ],
    },
)
