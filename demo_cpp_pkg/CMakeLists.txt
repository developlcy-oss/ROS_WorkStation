cmake_minimum_required(VERSION 3.8)
project(demo_cpp_pkg)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)

add_executable(listener src/listener.cpp)
ament_target_dependencies(listener rclcpp std_msgs)

# lib/<패키지명>/ 아래로 설치해야 'ros2 run' 과 launch 의 executable= 이 찾는다.
install(TARGETS listener
  DESTINATION lib/${PROJECT_NAME})

ament_package()
