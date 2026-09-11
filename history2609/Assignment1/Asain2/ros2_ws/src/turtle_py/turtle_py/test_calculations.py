import math

import pytest

from turtle_py.distance_publisher import DistancePublisher
from turtle_py.square_controller import SquareController
from turtle_py.waypoint_marker import WaypointMarker


class TestCalculateDistance:

    def test_normal(self):
        # 정상: 3-4-5 삼각형
        result = DistancePublisher.calculate_distance(3.0, 4.0)

        assert result == pytest.approx(5.0)

    def test_boundary(self):
        # 경계: 원점에서의 거리
        result = DistancePublisher.calculate_distance(0.0, 0.0)

        assert result == pytest.approx(0.0)

    def test_exception(self):
        # 예외: 숫자가 아닌 입력
        with pytest.raises(TypeError):
            DistancePublisher.calculate_distance("3", 4.0)


class TestAngleToGoal:

    def test_normal(self):
        # 정상: 현재 위치 (0,0) → 목표 (1,1)
        result = SquareController.angle_to_goal(
            0.0, 0.0,
            1.0, 1.0
        )

        assert result == pytest.approx(math.pi / 4)

    def test_boundary(self):
        # 경계: 목표가 정확히 왼쪽에 있을 때
        result = SquareController.angle_to_goal(
            0.0, 0.0,
            -1.0, 0.0
        )

        assert -math.pi <= result <= math.pi
        assert result == pytest.approx(-math.pi)

    def test_exception(self):
        # 예외: 숫자가 아닌 입력
        with pytest.raises(TypeError):
            SquareController.angle_to_goal(
                "0", 0.0,
                1.0, 1.0
            )


class TestWaypointReached:

    def test_normal(self):
        # 정상: waypoint에 충분히 가까움
        result = WaypointMarker.is_waypoint_reached(
            2.0, 2.0,
            2.3, 2.4,
            0.5
        )

        assert result is True

    def test_boundary(self):
        # 경계: 거리가 tolerance와 정확히 같음
        result = WaypointMarker.is_waypoint_reached(
            0.0, 0.0,
            3.0, 4.0,
            5.0
        )

        assert result is True

    def test_exception(self):
        # 예외: 음수 tolerance
        with pytest.raises(ValueError):
            WaypointMarker.is_waypoint_reached(
                0.0, 0.0,
                1.0, 1.0,
                -0.1
            )
