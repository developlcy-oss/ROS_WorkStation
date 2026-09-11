cmake_minimum_required(VERSION 3.8)
project(turtle_interfaces)

# 문제 6 — 인터페이스 전용 패키지.
# 여기에는 add_executable 이 하나도 없습니다. 이 패키지가 하는 일은 오직
# ".msg/.srv/.action 텍스트 → C++ 헤더 + Python 모듈 자동 생성" 뿐입니다.

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
# rosidl_generate_interfaces 매크로를 제공하는 패키지
find_package(rosidl_default_generators REQUIRED)
# 우리 메시지가 "다른 패키지의 메시지" 를 필드로 포함하면 그 패키지를 find_package 해야 합니다.
#   WaypointList.msg → std_msgs/Header
#   DrawPolygon.action → (암묵적으로) action_msgs
find_package(std_msgs REQUIRED)
find_package(action_msgs REQUIRED)

# 인터페이스 목록. 파일 이름이 곧 타입 이름이 됩니다.
#   msg/Waypoint.msg        → turtle_interfaces/msg/Waypoint
#   msg/WaypointList.msg    → turtle_interfaces/msg/WaypointList
#   srv/SetGain.srv         → turtle_interfaces/srv/SetGain
#   action/DrawPolygon.action → turtle_interfaces/action/DrawPolygon
# 규칙: 타입 이름은 대문자로 시작하는 CamelCase, 필드 이름은 snake_case.
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Waypoint.msg"
  "msg/WaypointList.msg"
  "srv/SetGain.srv"
  "action/DrawPolygon.action"
  # DEPENDENCIES: 우리 정의가 필드로 "사용하는" 외부 인터페이스 패키지
  DEPENDENCIES std_msgs action_msgs
)

# 이 패키지를 쓰는 쪽(turtle_py, turtle_cpp)이 런타임 의존을 자동으로 물려받도록 export
ament_export_dependencies(rosidl_default_runtime)

ament_package()
