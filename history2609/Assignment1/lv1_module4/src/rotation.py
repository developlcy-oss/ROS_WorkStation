"""문제 2·3 — 회전 행렬 모듈. (학생 작성용 템플릿)

축별 회전 행렬, 로드리게스 공식(임의 축 회전), Gram-Schmidt 재직교화,
회전행렬 판정과 고유값 분해 기반 축·각 복원을 직접 구현한다.

문제 1 에서 만든 `src/vectors.py` 를 그대로 재사용한다.
"""

from __future__ import annotations

import numpy as np
import matplotlib.font_manager as fm

[f.name for f in fm.fontManager.ttflist if "Nanum" in f.name]

from .vectors import det, normalize, skew

__all__ = [
    "rot_x",
    "rot_y",
    "rot_z",
    "rodrigues",
    "gram_schmidt",
    "orthogonality_error",
    "is_rotation",
    "axis_angle_from_matrix",
    "quaternion_from_axis_angle",
]


# ------------------------------------------------------------ 축별 회전 행렬
def rot_x(theta: float) -> np.ndarray:
    c = np.cos(theta)
    s = np.sin(theta)

    return np.array([
        [1, 0, 0],
        [0, c, -s],
        [0, s,  c],
    ])


def rot_y(theta: float) -> np.ndarray:
    c = np.cos(theta)
    s = np.sin(theta)

    return np.array([
        [ c, 0, s],
        [ 0, 1, 0],
        [-s, 0, c],
    ])


def rot_z(theta: float) -> np.ndarray:
    c = np.cos(theta)
    s = np.sin(theta)

    return np.array([
        [c, -s, 0],
        [s,  c, 0],
        [0,  0, 1],
    ])

def rodrigues(axis, theta: float) -> np.ndarray:
    """로드리게스 공식으로 임의 축 회전 행렬을 만든다.

        R = I + sin(theta) * K + (1 - cos(theta)) * K @ K,   K = [k]_x

    - 축은 함수 안에서 단위벡터로 정규화한다
      (정규화되지 않은 축을 넣어도 같은 결과가 나와야 한다).
    - 문제 1 의 `skew` 를 반드시 사용한다.
    """
    # TODO: 문제 2-5
    axis = normalize(axis)
    K = skew(axis)

    I = np.eye(3)

    return I + np.sin(theta) * K + (1 - np.cos(theta)) * (K @ K)

# ------------------------------------------------------------- 재직교화 관련

def gram_schmidt(A) -> np.ndarray:
    """**열벡터**에 대해 Gram-Schmidt 직교정규화를 수행한다.

        q1 = a1 / |a1|
        vj = aj - sum_{i<j} (qi · aj) qi
        qj = vj / |vj|

    각 열에서 앞선 열 방향 성분(정사영)을 빼고 정규화하는 것이며,
    문제 1 의 project / reject 와 같은 연산의 반복이다.

    수치적으로는 성분을 빼자마자 갱신하는 modified Gram-Schmidt 가 더 안정적이다.
    앞선 열들에 종속인 열이 있으면 ValueError.
    """
    # TODO: 문제 3-2
    A = np.asarray(A, dtype=float)

    Q = np.zeros_like(A)

    for i in range(A.shape[1]):
        v = A[:, i].copy()

        for j in range(i):
            v = v - np.dot(Q[:, j], v) * Q[:, j]

        norm = np.linalg.norm(v)

        if norm < np.finfo(float).eps:
            raise ValueError("선형 종속인 열벡터가 있습니다.")

        Q[:, i] = v / norm

    if np.linalg.det(Q) < 0:
        Q[:, -1] *= -1

    return Q

def orthogonality_error(R) -> float:
    """직교성 이탈 지표: || R^T R - I ||_F  (프로베니우스 노름).

    완전한 직교행렬이면 0 이고, 클수록 직교성이 무너진 것이다.
    """
    I = np.eye(3)
    return np.linalg.norm(R.T @ R - I)


def is_rotation(R, atol: float = 1e-8) -> bool:
    """회전행렬 판정: 직교(R^T R = I) **그리고** det(R) = +1 이면 True.

    det = -1 이면 직교이긴 하지만 반사가 섞여 있어 회전이 아니다.
    3x3 이 아니면 False.
    """
    # TODO: 문제 3-2
    R = np.asarray(R, dtype=float)

    # 3x3 행렬인지 확인
    if R.shape != (3, 3):
        return False

    # 직교행렬인지 확인
    if not np.allclose(R.T @ R, np.eye(3), atol=atol):
        return False

    # 행렬식이 +1인지 확인
    if not np.isclose(np.linalg.det(R), 1.0, atol=atol):
        return False

    return True

# --------------------------------------------------- 회전축·회전각·쿼터니언

def axis_angle_from_matrix(R, atol: float = 1e-8):
    """고유값 분해로 회전축을, 대각합으로 회전각을 복원한다.

    - 회전축은 고유값 1 에 대응하는 실수 고유벡터다 (R k = k).
      -> 여기서는 `np.linalg.eig` 를 써도 된다 (검산이 아니라 축 복원이 목적).
    - 회전각은 trace(R) = 1 + 2 cos(theta) 에서 구한다.
    - arccos 의 치역이 [0, pi] 라 '어느 쪽으로 도는지'는 알 수 없고,
      고유벡터도 부호가 정해지지 않는다. 반대칭 성분
      R - R^T = 2 sin(theta) [k]_x 를 이용해 부호를 맞춘다.
    - theta = 0 (회전 없음) 과 theta = pi (sin = 0) 는 따로 처리해야 한다.
      두 경우에 어떤 규약을 쓸지 정하고 주석으로 남긴다.

    Returns
    -------
    axis : 단위 회전축 (3,)
    angle : 회전각 [rad], 0 <= angle <= pi
    """
    R = np.asarray(R, dtype=float)

    if R.shape != (3, 3):
        raise ValueError(f"3x3 회전행렬이 필요합니다. 받은 shape={R.shape}")

    cos_theta = (np.trace(R) - 1.0) / 2.0
    cos_theta = np.clip(cos_theta, -1.0, 1.0)

    angle = np.arccos(cos_theta)

    if np.isclose(angle, 0.0, atol=atol):
        return np.array([1.0, 0.0, 0.0]), 0.0

    if np.isclose(angle, np.pi, atol=atol):
        eigvals, eigvecs = np.linalg.eig(R)

        idx = np.argmin(np.abs(eigvals - 1.0))
        axis = np.real(eigvecs[:, idx])

        axis = axis / np.linalg.norm(axis)

        # 고유벡터의 부호는 임의이므로 규약을 정한다.
        # 가장 절댓값이 큰 성분을 양수로 만든다.
        max_idx = np.argmax(np.abs(axis))

        if axis[max_idx] < 0:
            axis = -axis

        return axis, np.pi

    sin_theta = np.sin(angle)

    K = (R - R.T) / (2.0 * sin_theta)

    axis = np.array([
        K[2, 1],
        K[0, 2],
        K[1, 0]
    ])

    axis = axis / np.linalg.norm(axis)

    return axis, angle


def quaternion_from_axis_angle(axis, angle: float) -> np.ndarray:
    """축-각에서 단위 쿼터니언을 만든다.

        q = (k * sin(theta/2), cos(theta/2))

    반환 순서는 SciPy `Rotation.as_quat()` 와 같은 **(x, y, z, w)** 로 맞춘다
    (그래야 문제 6-5 에서 바로 비교할 수 있다).
    """
    axis = np.asarray(axis, dtype=float)

    if axis.shape != (3,):
        raise ValueError(f"회전축은 (3,) 벡터여야 합니다. 받은 shape={axis.shape}")

    norm = np.linalg.norm(axis)

    if norm < 1e-12:
        raise ValueError("회전축의 크기가 0입니다.")

    # 회전축 정규화
    axis = axis / norm

    half_angle = angle / 2.0

    s = np.sin(half_angle)
    w = np.cos(half_angle)

    q = np.array([
        axis[0] * s,
        axis[1] * s,
        axis[2] * s,
        w
    ])

    # 부동소수점 오차를 고려하여 다시 정규화
    q = q / np.linalg.norm(q)

    return q
