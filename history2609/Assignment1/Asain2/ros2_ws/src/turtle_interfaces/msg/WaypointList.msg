# 문제 6 — 경유점 목록. "중첩(다른 메시지를 필드로)" 과 "배열" 을 모두 사용합니다.
#
# 다른 패키지의 메시지를 쓸 때는 "패키지/타입" 으로 적습니다 (std_msgs/Header).
# 같은 패키지의 메시지는 패키지 이름 없이 타입 이름만 적어도 됩니다 (Waypoint).
# Waypoint[] 처럼 [] 를 붙이면 가변 길이 배열이 됩니다. (고정 길이는 Waypoint[4])

std_msgs/Header header   # stamp(발행 시각) + frame_id(좌표계 이름, 여기서는 "world")
Waypoint[] waypoints     # 경유점 배열 — 문제 6 에서는 4개 이상을 채워 발행합니다
