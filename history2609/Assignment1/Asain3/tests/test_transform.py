"""문제 5 — 동차변환 inv_T 검증 (pytest). [학생 작성용 템플릿]

지시문이 요구하는 것은 `inv_T` 검증이지만,
점/방향 구분과 벡터화, 최소자승까지 함께 검증해 두면 이후 문제에서 안전하다.

실행: 프로젝트 루트에서  pytest -v
"""

import numpy as np
import pytest

from src.rotation import rot_x, rot_y, rot_z
from src.transform import (
    inv_T,
    least_squares_normal_equation,
    make_T,
    transform_direction,
    transform_point,
    transform_points,
)


@pytest.fixture
def T():
    """테스트에 쓸 대표 동차변환 하나."""
    R = rot_z(0.9) @ rot_y(-0.35) @ rot_x(1.3)
    return make_T(R, [0.35, -0.15, 0.55])

def test_inv_T_gives_identity(T):
    # inv_T(T) @ T 와 T @ inv_T(T) 가 모두 4x4 단위행렬인지 검사
    Ti = inv_T(T)
    I = np.eye(4)

    assert np.allclose(
        Ti @ T,
        I
    ), "inv_T(T) @ T가 단위행렬이 아닙니다."

    assert np.allclose(
        T @ Ti,
        I
    ), "T @ inv_T(T)가 단위행렬이 아닙니다."


def test_inv_T_matches_generic_inverse(T):
    # inv_T(T) 가 np.linalg.inv(T) 와 일치하는지 검사
    Ti = inv_T(T)

    assert np.allclose(
        Ti,
        np.linalg.inv(T)
    ), "inv_T(T)가 np.linalg.inv(T)와 다릅니다."


def test_point_and_direction_differ(T):
    # 같은 벡터를 점(w=1)/방향(w=0)으로 변환
    v = np.array([0.4, -0.2, 0.7])

    p_out = transform_point(T, v)
    d_out = transform_direction(T, v)

    # 점과 방향은 병진 때문에 달라야 한다.
    assert not np.allclose(
        p_out,
        d_out
    ), "점과 방향 변환 결과가 같습니다."

    # 두 결과의 차이는 정확히 병진 벡터
    translation = T[:3, 3]

    assert np.allclose(
        p_out - d_out,
        translation
    ), "점과 방향 변환 결과의 차이가 병진 벡터가 아닙니다."

    # 회전은 벡터의 길이를 보존한다.
    assert np.allclose(
        np.linalg.norm(d_out),
        np.linalg.norm(v)
    ), "방향 변환에서 벡터의 길이가 보존되지 않았습니다."


def test_transform_points_is_vectorized(T):
    # (N,3) 점군
    P = np.array([
        [0.1, 0.2, 0.3],
        [-0.4, 0.5, 0.6],
        [0.7, -0.8, 0.9],
        [1.0, 0.0, -0.2],
        [-0.3, -0.6, 0.4],
    ])

    # 벡터화된 변환
    P_vec = transform_points(T, P)

    # transform_point를 반복문으로 적용
    P_loop = np.array([
        transform_point(T, p)
        for p in P
    ])

    assert np.allclose(
        P_vec,
        P_loop
    ), "벡터화 결과와 반복문 결과가 다릅니다."


def test_roundtrip_through_inverse(T):
    # 점군 생성
    P = np.array([
        [0.1, 0.2, 0.3],
        [-0.4, 0.5, 0.6],
        [0.7, -0.8, 0.9],
        [1.0, 0.0, -0.2],
        [-0.3, -0.6, 0.4],
    ])

    # T로 변환
    P_out = transform_points(T, P)

    # 역변환으로 복원
    P_back = transform_points(inv_T(T), P_out)

    assert np.allclose(
        P_back,
        P
    ), "변환 후 역변환했을 때 원래 점군으로 복원되지 않습니다."


def test_least_squares_matches_lstsq():
    # 과결정 문제 생성
    rng = np.random.default_rng(42)

    A = rng.normal(size=(20, 4))
    x_true = np.array([0.8, -0.5, 0.3, 1.2])

    noise = rng.normal(scale=0.002, size=20)
    b = A @ x_true + noise

    # 우리가 구현한 정규방정식 해
    x_hat, residual = least_squares_normal_equation(A, b)

    # NumPy 기준 해
    x_lstsq, *_ = np.linalg.lstsq(A, b, rcond=None)

    # 두 해가 일치하는지 검사
    assert np.allclose(
        x_hat,
        x_lstsq
    ), "정규방정식 해와 np.linalg.lstsq 해가 다릅니다."

    # 잔차가 A의 열공간에 수직인지 검사
    assert np.allclose(
        A.T @ residual,
        np.zeros(A.shape[1]),
        atol=1e-10
    ), "잔차가 A의 열공간에 수직하지 않습니다."
    
# def test_inv_T_gives_identity(T):
#     # TODO: inv_T(T) @ T 와 T @ inv_T(T) 가 모두 4x4 단위행렬인지 검사
#     raise NotImplementedError("test_inv_T_gives_identity 를 작성하세요")


# def test_inv_T_matches_generic_inverse(T):
#     # TODO: inv_T(T) 가 np.linalg.inv(T) 와 일치하는지 검사 (np.linalg 는 검산용)
#     raise NotImplementedError("test_inv_T_matches_generic_inverse 를 작성하세요")


# def test_point_and_direction_differ(T):
#     # TODO: 같은 벡터를 점(w=1)/방향(w=0)으로 변환하면 결과가 다르고,
#     #       그 차이가 정확히 병진 벡터 T[:3, 3] 이며,
#     #       방향 변환은 길이를 보존하는지 검사
#     raise NotImplementedError("test_point_and_direction_differ 를 작성하세요")


# def test_transform_points_is_vectorized(T):
#     # TODO: (N,3) 점군을 한 번에 변환한 결과가
#     #       transform_point 를 반복문으로 돌린 결과와 같은지 검사
#     raise NotImplementedError("test_transform_points_is_vectorized 를 작성하세요")


# def test_roundtrip_through_inverse(T):
#     # TODO: T 로 보냈다가 inv_T(T) 로 되돌리면 원래 점군이 나오는지 검사
#     raise NotImplementedError("test_roundtrip_through_inverse 를 작성하세요")


# def test_least_squares_matches_lstsq():
#     # TODO: 노이즈를 섞은 과결정 문제를 만들어
#     #       least_squares_normal_equation 의 해가 np.linalg.lstsq 와 일치하고
#     #       잔차가 A 의 열공간에 수직(A^T r = 0)인지 검사
#     raise NotImplementedError("test_least_squares_matches_lstsq 를 작성하세요")
