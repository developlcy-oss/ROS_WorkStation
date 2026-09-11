"""문제 4 — 궤적 보간 검증 (pytest). [학생 작성용 템플릿]

지시문이 요구하는 것: 궤적이 경유점을 정확히 지나는가. 여기에 5차 다항식 경계 조건을 더한다.

  1. 선형 보간이 경유점을 지나는가             -> test_linear_interp_hits_waypoints
  2. 큐빅 스플라인이 경유점을 지나는가         -> test_cubic_spline_hits_waypoints
  3. 5차 다항식의 양끝 속도·가속도가 0 인가    -> test_quintic_boundary_conditions

작성 요령
--------
- 경유점 시각 t_wp 를 그대로 평가 시각으로 넣으면 q_wp 가 나와야 한다 (allclose).
- 스칼라 (M,) 와 3차원 (M,3) 경유점 둘 다 검사하면 좋다 (parametrize 또는 fixture).
- `quintic_profile` 은 (q, qd, qdd) 를 돌려준다. 양끝에서 qd, qdd 가 0 이고
  q 가 q0, qf 인지 검사한다.

실행: 프로젝트 루트에서  pytest tests/test_trajectory.py -v
"""

import numpy as np
import pytest

from src.trajectory import cubic_spline_interp, finite_diff, linear_interp, quintic_profile

T_WP = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
Q_WP_1D = np.array([0.0, 0.8, 0.3, 1.2, 0.5, 0.9])
P_WP_3D = np.array([
    [0.20, -0.30, 0.60],
    [0.30, -0.15, 0.75],
    [0.42, 0.00, 0.80],
    [0.50, 0.15, 0.70],
    [0.55, 0.25, 0.55],
    [0.60, 0.30, 0.45],
])


@pytest.fixture(params=["1d", "3d"])
def waypoints(request):
    return (T_WP, Q_WP_1D) if request.param == "1d" else (T_WP, P_WP_3D)


# --- 1. 선형 보간이 경유점을 지나는가 -----------------------------------------

def test_linear_interp_hits_waypoints(waypoints):
    t_wp, q_wp = waypoints

    q = linear_interp(t_wp, q_wp, t_wp)

    assert q.shape == q_wp.shape
    assert np.allclose(q, q_wp)


# --- 2. 큐빅 스플라인이 경유점을 지나는가 -------------------------------------

def test_cubic_spline_hits_waypoints(waypoints):
    t_wp, q_wp = waypoints

    q = cubic_spline_interp(t_wp, q_wp, t_wp)

    assert q.shape == q_wp.shape
    assert np.allclose(q, q_wp)


# --- 3. 5차 다항식 경계 조건 ---------------------------------------------------

def test_quintic_boundary_conditions():
    t = np.linspace(0.0, 2.0, 201)

    q, qd, qdd = quintic_profile(
        t, 0.0, 2.0, 0.0, 1.0
    )

    assert np.isclose(q[0], 0.0)
    assert np.isclose(q[-1], 1.0)

    assert np.isclose(qd[0], 0.0)
    assert np.isclose(qd[-1], 0.0)

    assert np.isclose(qdd[0], 0.0)
    assert np.isclose(qdd[-1], 0.0)


# --- 여기부터는 추가 테스트 (권장) -------------------------------------------
#
# 예) def test_spline_velocity_is_continuous():
#         """finite_diff 로 구한 스플라인 속도에는 큰 점프가 없다 (선형 보간과 비교)."""
#
# 예) def test_quintic_matches_finite_difference():
#         """해석적 qd 가 finite_diff(q, t) 와 일치한다."""
#
# 예) def test_quintic_is_monotonic_for_zero_boundary():
#         """경계 속도·가속도가 0 인 기본형은 q0 -> qf 로 단조 증가한다."""
