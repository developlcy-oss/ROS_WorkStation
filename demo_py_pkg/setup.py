from setuptools import find_packages, setup

package_name = 'demo_py_pkg'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        # 이 두 줄이 있어야 ros2 run / ros2 launch 가 패키지를 찾는다.
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='pa',
    maintainer_email='roboticsmaster@naver.com',
    description='Python(rclpy) 노드 예제 - std_msgs/String 퍼블리셔',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        # 'ros2 run demo_py_pkg talker' 의 'talker' 가 여기서 만들어진다.
        'console_scripts': [
            'talker = demo_py_pkg.talker:main',
        ],
    },
)
