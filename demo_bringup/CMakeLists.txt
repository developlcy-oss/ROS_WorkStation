cmake_minimum_required(VERSION 3.8)
project(demo_bringup)

find_package(ament_cmake REQUIRED)

# launch/ 와 config/ 를 share/demo_bringup/ 아래로 설치해야
# 'ros2 launch demo_bringup demo.launch.py' 가 파일을 찾는다.
install(DIRECTORY
  launch
  config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
