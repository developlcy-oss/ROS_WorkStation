"""문제 3 — 쿼터니언과 SLERP 검증 (pytest). [학생 작성용 템플릿]

지시문이 요구하는 두 가지:

  1. SLERP 결과가 항상 단위 쿼터니언인가                 -> test_slerp_is_unit_norm
  2. 보간 비율 0 과 1 에서 시작·목표 자세와 같은가       -> test_slerp_endpoints

작성 요령
--------
- 쿼터니언 순서는 (x, y, z, w). q 와 -q 는 같은 회전이므로 자세 비교는
  `quaternion_to_matrix` 로 회전행렬을 만들어 비교하거나 |q . q_ref| == 1 로 한다.
- `@pytest.mark.parametrize("t", [...])` 로 여러 비율을 한 번에 검사한다.
- 비교는 `np.allclose` / `np.isclose` (기본 허용오차).

실행: 프로젝트 루트에서  pytest tests/test_quaternion.py -v
"""

import numpy as np
import pytest

from src.quaternion import lerp_quat, matrix_to_quaternion, quaternion_to_matrix, slerp
from src.rotation import rodrigues, rot_x, rot_y, rot_z

TS = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]


@pytest.fixture
def rng():
    return np.random.default_rng(42)


@pytest.fixture
def q_pair():
    """시작·목표 자세 (노트북 3-2 와 같은 값)."""
    R_start = rot_z(np.deg2rad(-30.0)) @ rot_x(np.deg2rad(20.0))
    R_goal = rot_z(np.deg2rad(120.0)) @ rot_y(np.deg2rad(60.0)) @ rot_x(np.deg2rad(-40.0))
    return matrix_to_quaternion(R_start), matrix_to_quaternion(R_goal)


# --- 1. SLERP 결과는 항상 단위 쿼터니언 ---------------------------------------

@pytest.mark.parametrize("t", TS)
def test_slerp_is_unit_norm(q_pair, t):
    q0, q1 = q_pair

    q = slerp(q0, q1, t)

    assert np.isclose(np.linalg.norm(q), 1.0)


# --- 2. t = 0 / 1 에서 시작·목표 자세 -----------------------------------------

def test_slerp_endpoints(q_pair):
    q0, q1 = q_pair

    q_start = slerp(q0, q1, 0.0)
    q_end = slerp(q0, q1, 1.0)

    R_start = quaternion_to_matrix(q_start)
    R_end = quaternion_to_matrix(q_end)

    assert np.allclose(R_start, quaternion_to_matrix(q0))
    assert np.allclose(R_end, quaternion_to_matrix(q1))



# --- 여기부터는 추가 테스트 (권장) -------------------------------------------
#
# 예) def test_matrix_quaternion_roundtrip(rng):
#         """무작위 회전 50개: R -> q -> R 이 원래 행렬로 돌아오는가."""
#
# 예) def test_slerp_matches_scipy(q_pair):
#         """scipy.spatial.transform.Slerp 와 회전행렬 기준으로 일치하는가."""
#
# 예) def test_slerp_nearly_identical_poses(q_pair):
#         """거의 같은 두 자세에서 NaN 이 나오지 않는가."""
#
# 예) def test_lerp_norm_drops_below_one(q_pair):
#         """정규화하지 않은 선형 보간의 중간값은 크기가 1 보다 작다."""
