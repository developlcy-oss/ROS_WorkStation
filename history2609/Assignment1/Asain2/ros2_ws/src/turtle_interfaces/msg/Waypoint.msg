# 문제 6 — 경유점 하나를 표현하는 메시지.
# 좌표는 정밀도를 위해 float64, 허용 오차는 float32 로 두어
# "같은 메시지 안에서 서로 다른 실수 타입을 쓸 수 있다" 는 점을 보여 줍니다.
# (turtlesim 의 Pose 는 float32 지만, 경유점 좌표는 double 로 두는 편이 일반적입니다.)

float64 x            # 경유점 x 좌표 [m] (turtlesim 좌표계, 0 ~ 11)
float64 y            # 경유점 y 좌표 [m]
float32 tolerance    # 도달 판정 허용 오차 [m] — 이 거리 이내면 "도달" 로 봅니다
string  label        # 사람이 읽는 이름 (예: "corner_A")
