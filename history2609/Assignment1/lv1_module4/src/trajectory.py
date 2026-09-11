"""문제 4 — 궤적 보간. (학생 작성용 템플릿)

경유점(waypoint)을 지나는 궤적을 선형 보간 / 큐빅 스플라인으로 만들고,
시작·끝에서 속도와 가속도가 0 이 되는 5차 다항식 프로파일을 구현한다.

입력 규약
--------
- t_wp : (M,) 경유점 시각, 오름차순
- q_wp : (M,) 스칼라 궤적 또는 (M, D) 다차원 궤적 (예: 3차원 위치는 D = 3)
- t    : (N,) 평가할 시각 (t_wp[0] <= t <= t_wp[-1])
- 반환 : q_wp 가 (M,) 이면 (N,), (M, D) 이면 (N, D)

큐빅 스플라인은 `scipy.interpolate.CubicSpline` 을 써도 된다 (axis=0).
"""
from __future__ import annotations

import numpy as np

__all__ = ["linear_interp", "cubic_spline_interp", "quintic_profile", "finite_diff"]


def linear_interp(t_wp, q_wp, t) -> np.ndarray:
    """경유점 사이를 직선으로 잇는 보간. 각 차원마다 `np.interp` 를 쓰면 된다.

    위치는 이어지지만 경유점에서 속도가 불연속(꺾임)이다.
    """
    t_wp = np.asarray(t_wp, dtype=float)
    q_wp = np.asarray(q_wp, dtype=float)
    t = np.asarray(t, dtype=float)

    if t_wp.ndim != 1:
        raise ValueError("t_wp must be 1-dimensional")

    if q_wp.ndim not in (1, 2):
        raise ValueError("q_wp must be 1-dimensional or 2-dimensional")

    if t.ndim != 1:
        raise ValueError("t must be 1-dimensional")

    if len(t_wp) != len(q_wp):
        raise ValueError("t_wp and q_wp must have the same length")

    if len(t_wp) < 2:
        raise ValueError("at least two waypoints are required")

    if np.any(np.diff(t_wp) <= 0):
        raise ValueError("t_wp must be strictly increasing")

    if q_wp.ndim == 1:
        return np.interp(t, t_wp, q_wp)

    result = np.empty((len(t), q_wp.shape[1]), dtype=float)

    for d in range(q_wp.shape[1]):
        result[:, d] = np.interp(t, t_wp, q_wp[:, d])

    return result


def cubic_spline_interp(t_wp, q_wp, t, bc_type: str = "natural") -> np.ndarray:
    """경유점을 지나는 큐빅 스플라인 보간 (위치·속도·가속도가 모두 연속, C2).

    bc_type : 양끝 경계 조건. "natural" (양끝 가속도 0) 또는 "clamped" (양끝 속도 0).
    """
    from scipy.interpolate import CubicSpline

    t_wp = np.asarray(t_wp, dtype=float)
    q_wp = np.asarray(q_wp, dtype=float)
    t = np.asarray(t, dtype=float)

    if t_wp.ndim != 1:
        raise ValueError("t_wp must be 1-dimensional")

    if q_wp.ndim not in (1, 2):
        raise ValueError("q_wp must be 1-dimensional or 2-dimensional")

    if len(t_wp) != len(q_wp):
        raise ValueError("t_wp and q_wp must have the same length")

    if len(t_wp) < 2:
        raise ValueError("at least two waypoints are required")

    if np.any(np.diff(t_wp) <= 0):
        raise ValueError("t_wp must be strictly increasing")

    if bc_type not in ("natural", "clamped"):
        raise ValueError("bc_type must be 'natural' or 'clamped'")

    spline = CubicSpline(
        t_wp,
        q_wp,
        axis=0,
        bc_type=bc_type,
    )

    return spline(t)


def quintic_profile(t, t0: float, tf: float, q0, qf,
                    v0=0.0, vf=0.0, a0=0.0, af=0.0):
    """5차 다항식 궤적 q(t) 와 그 도함수 (q, qd, qdd) 를 돌려준다.

    경계 조건 6개 — q(t0)=q0, q(tf)=qf, qd(t0)=v0, qd(tf)=vf, qdd(t0)=a0, qdd(tf)=af —
    로 계수 6개 (c0 ~ c5) 를 정한다.
    """
    t = np.asarray(t, dtype=float)
    q0 = np.asarray(q0, dtype=float)
    qf = np.asarray(qf, dtype=float)
    v0 = np.asarray(v0, dtype=float)
    vf = np.asarray(vf, dtype=float)
    a0 = np.asarray(a0, dtype=float)
    af = np.asarray(af, dtype=float)

    if tf <= t0:
        raise ValueError("tf must be greater than t0")

    q0, qf = np.broadcast_arrays(q0, qf)
    v0 = np.broadcast_to(v0, q0.shape)
    vf = np.broadcast_to(vf, q0.shape)
    a0 = np.broadcast_to(a0, q0.shape)
    af = np.broadcast_to(af, q0.shape)

    T = tf - t0

    # q(tau) = c0 + c1*tau + c2*tau² + ... + c5*tau⁵
    #
    # tau = 0에서:
    # c0 = q0
    # c1 = v0*T
    # 2*c2 = a0*T²
    #
    # tau = 1에서 나머지 3개 계수를 결정한다.

    c0 = q0
    c1 = v0 * T
    c2 = 0.5 * a0 * T**2

    A = np.array([
        [1.0, 1.0, 1.0],
        [3.0, 4.0, 5.0],
        [6.0, 12.0, 20.0],
    ])

    rhs = np.stack([
        qf - (c0 + c1 + c2),
        vf * T - (c1 + 2.0 * c2),
        af * T**2 - (2.0 * c2),
    ], axis=0)

    c3, c4, c5 = np.linalg.solve(A, rhs)

    tau = (t - t0) / T

    q = (
        c0
        + c1 * tau[..., None] if q0.ndim > 0 else c0 + c1 * tau
    )

    if q0.ndim > 0:
        q = (
            c0
            + c1 * tau[..., None]
            + c2 * tau[..., None]**2
            + c3 * tau[..., None]**3
            + c4 * tau[..., None]**4
            + c5 * tau[..., None]**5
        )
        qd = (
            c1
            + 2.0 * c2 * tau[..., None]
            + 3.0 * c3 * tau[..., None]**2
            + 4.0 * c4 * tau[..., None]**3
            + 5.0 * c5 * tau[..., None]**4
        ) / T
        qdd = (
            2.0 * c2
            + 6.0 * c3 * tau[..., None]
            + 12.0 * c4 * tau[..., None]**2
            + 20.0 * c5 * tau[..., None]**3
        ) / T**2

    else:
        q = (
            c0
            + c1 * tau
            + c2 * tau**2
            + c3 * tau**3
            + c4 * tau**4
            + c5 * tau**5
        )
        qd = (
            c1
            + 2.0 * c2 * tau
            + 3.0 * c3 * tau**2
            + 4.0 * c4 * tau**3
            + 5.0 * c5 * tau**4
        ) / T
        qdd = (
            2.0 * c2
            + 6.0 * c3 * tau
            + 12.0 * c4 * tau**2
            + 20.0 * c5 * tau**3
        ) / T**2

    return q, qd, qdd


def finite_diff(y, t) -> np.ndarray:
    """시간축(axis 0)에 대한 수치 미분.

    y : (N,) 또는 (N, D), t : (N,)
    속도 = finite_diff(q, t), 가속도 = finite_diff(속도, t)
    """
    y = np.asarray(y, dtype=float)
    t = np.asarray(t, dtype=float)

    if t.ndim != 1:
        raise ValueError("t must be 1-dimensional")

    if y.shape[0] != len(t):
        raise ValueError("y and t must have the same length")

    return np.gradient(y, t, axis=0)