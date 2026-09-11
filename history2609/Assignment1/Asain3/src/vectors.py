"""문제 1 — 벡터 연산 모듈. (학생 작성용 템플릿)

내적 · 사이각 · 정규화 · 정사영 · 반대칭행렬(외적) · 평면 법선과
가우스 소거 기반의 rank / 행렬식 / 역행렬을 **직접** 구현한다.

규칙
----
- `np.linalg` 는 노트북에서 **검산용으로만** 쓰고, 이 모듈 안에서는 쓰지 않는다.
  (`inverse_gauss_jordan` 이 던지는 `np.linalg.LinAlgError` 예외 타입만 예외)
- 각 함수의 docstring 에 적힌 계약(입력/출력/예외)을 그대로 지킨다.
  노트북의 검증 셀과 `tests/` 가 이 계약을 기준으로 채점된다.
- 구현을 마치면 `raise NotImplementedError(...)` 줄을 지운다.
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "as_vector",
    "dot",
    "norm",
    "angle_between",
    "normalize",
    "project",
    "reject",
    "skew",
    "cross",
    "plane_normal",
    "row_echelon",
    "rank",
    "det",
    "gauss_eliminate",
    "inverse_gauss_jordan",
]


# ---------------------------------------------------------------- 기본 연산

def as_vector(v) -> np.ndarray:
    """입력(리스트/튜플/배열)을 1차원 float 배열로 변환한다.

    1차원이 아니면 ValueError 를 던진다.

    [구현 예시] 아래 세 줄이 이 파일에서 기대하는 코드 스타일이다.
    나머지 함수도 이런 식으로 채워 넣으면 된다.
    """
    arr = np.asarray(v, dtype=float)
    if arr.ndim != 1:
        raise ValueError(f"1차원 벡터가 필요합니다. 받은 shape={arr.shape}")
    return arr


def dot(a, b) -> float:
    """내적. sum(a_i * b_i) 를 직접 계산한다 (`np.dot` 사용 금지).

    두 벡터의 차원이 다르면 ValueError.
    """
    a = as_vector(a)
    b = as_vector(b)

    if a.shape != b.shape:
        raise ValueError("두 벡터의 차원이 같아야 합니다.")

    return float(np.sum(a * b))


def norm(v) -> float:
    """유클리드 노름. sqrt(v·v) — 위에서 만든 dot 을 재사용한다."""
    v = as_vector(v)

    return float(np.sqrt(dot(v, v)))


def angle_between(a, b, degrees: bool = True) -> float:
    """두 벡터 사이각. degrees=True 면 도(°), False 면 라디안.

    cos(theta) = (a·b) / (|a||b|)

    주의 1. 영벡터가 들어오면 사이각이 정의되지 않는다 -> ValueError.
    주의 2. 부동소수점 오차로 |cos| 가 1 을 아주 조금 넘으면 arccos 가 nan 을 낸다.
            [-1, 1] 로 clip 해야 무작위 입력에서도 안전하다.
    """
    a = as_vector(a)
    b = as_vector(b)

    if a.shape != b.shape:
        raise ValueError("두 벡터의 차원이 같아야 합니다.")

    a_norm = norm(a)
    b_norm = norm(b)

    if a_norm == 0 or b_norm == 0:
        raise ValueError("영벡터의 사이각은 정의되지 않습니다.")

    cos_theta = dot(a, b) / (a_norm * b_norm)

    cos_theta = np.clip(cos_theta, -1.0, 1.0)

    theta = np.arccos(cos_theta)

    if degrees:
        theta = np.degrees(theta)

    return float(theta)


def normalize(v, eps: float = 1e-12) -> np.ndarray:
    """단위벡터로 정규화한다. v / |v|"""

    v = as_vector(v)
    length = norm(v)

    if length < eps:
        raise ValueError("영벡터는 정규화할 수 없습니다.")

    return v / length


def project(a, b) -> np.ndarray:
    """a를 b 방향으로 정사영한 성분."""

    a = as_vector(a)
    b = as_vector(b)

    denominator = dot(b, b)

    if denominator == 0:
        raise ValueError("영벡터에는 정사영할 수 없습니다.")

    coefficient = dot(a, b) / denominator

    return coefficient * b


def reject(a, b) -> np.ndarray:
    """a에서 b 방향 성분을 뺀 나머지."""

    a = as_vector(a)

    return a - project(a, b)


def skew(a) -> np.ndarray:
    """3차원 벡터에 대응하는 반대칭행렬을 만든다."""

    a = as_vector(a)

    if a.shape != (3,):
        raise ValueError("3차원 벡터가 필요합니다.")

    x, y, z = a

    return np.array([
        [0.0, -z,  y],
        [z,   0.0, -x],
        [-y,  x,   0.0]
    ])


def cross(a, b) -> np.ndarray:
    """외적을 반대칭행렬 곱으로 계산한다 (`np.cross` 사용 금지)."""

    a = as_vector(a)
    b = as_vector(b)

    if a.shape != (3,) or b.shape != (3,):
        raise ValueError("외적은 3차원 벡터만 사용할 수 있습니다.")

    return skew(a) @ b


def plane_normal(P1, P2, P3) -> np.ndarray:
    """세 점이 이루는 평면의 단위 법선 벡터."""
    P1 = as_vector(P1)
    P2 = as_vector(P2)
    P3 = as_vector(P3)

    if P1.shape != (3,) or P2.shape != (3,) or P3.shape != (3,):
        raise ValueError("세 점 모두 3차원 벡터여야 합니다.")

    v1 = P2 - P1
    v2 = P3 - P1

    normal = cross(v1, v2)

    if norm(normal) < 1e-12:
        raise ValueError("세 점이 일직선이므로 평면의 법선을 정의할 수 없습니다.")

    return normalize(normal)

# ------------------------------------------------- 가우스 소거 기반 선형대수

def row_echelon(A, pivoting: bool = True):
    """행 사다리꼴(row echelon form) 로 만든다."""
    U = np.asarray(A, dtype=float).copy()

    if U.ndim != 2:
        raise ValueError("2차원 행렬이 필요합니다.")

    m, n = U.shape
    pivot_cols = []
    n_swaps = 0

    row = 0

    for col in range(n):
        if row >= m:
            break

        # 현재 열에서 피벗 선택
        if pivoting:
            pivot_row = row + np.argmax(np.abs(U[row:, col]))
        else:
            pivot_row = row

        # 허용오차
        tol = max(m, n) * np.finfo(float).eps * max(
            1.0, np.max(np.abs(U))
        )

        # 피벗이 사실상 0이면 다음 열
        if abs(U[pivot_row, col]) <= tol:
            continue

        # 행 교환
        if pivot_row != row:
            U[[row, pivot_row]] = U[[pivot_row, row]]
            n_swaps += 1

        # 아래 행들을 소거
        for r in range(row + 1, m):
            if abs(U[r, col]) <= tol:
                continue

            factor = U[r, col] / U[row, col]
            U[r, col:] -= factor * U[row, col:]

        pivot_cols.append(col)
        row += 1

    return U, pivot_cols, n_swaps


def rank(A) -> int:
    """행 사다리꼴의 피벗 개수 = rank."""
    _, pivot_cols, _ = row_echelon(A)
    return len(pivot_cols)


def det(A) -> float:
    """행렬식 = 행 사다리꼴 대각성분의 곱 x (-1)^(행 교환 횟수)."""
    A = np.asarray(A, dtype=float)

    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise ValueError("정사각 행렬이 필요합니다.")

    U, pivot_cols, n_swaps = row_echelon(A)

    n = A.shape[0]

    # 피벗이 n개보다 적으면 특이행렬
    if len(pivot_cols) < n:
        return 0.0

    diagonal_product = np.prod(np.diag(U))

    return float(((-1) ** n_swaps) * diagonal_product)


def gauss_eliminate(A, b, pivoting: bool = True, verbose: bool = False):
    """가우스 소거법 + 후진대입으로 Ax = b 를 푼다.

    Parameters
    ----------
    pivoting : True 면 부분 피벗팅을 적용한다. False 면 피벗을 그대로 쓴다
               (문제 4-4 에서 두 경우의 오차를 비교하므로 **둘 다 동작해야 한다**).
    verbose  : True 면 각 소거 단계의 첨가행렬 [A|b] 를 출력한다
               (문제 4-1 이 요구하는 '단계별 출력').

    Returns
    -------
    x : 해 벡터
    steps : 단계별 첨가행렬 [A|b] 스냅샷 리스트 (초기 상태 포함)

    피벗이 0 이면 해가 유일하지 않다 -> ZeroDivisionError.
    """
    # TODO: 문제 4-1
    A = np.asarray(A, dtype=float)
    b = np.asarray(b, dtype=float)

    if A.ndim != 2:
        raise ValueError("2차원 계수행렬이 필요합니다.")

    if b.ndim != 1:
        raise ValueError("1차원 우변 벡터가 필요합니다.")

    m, n = A.shape

    if m != n:
        raise ValueError("정사각 계수행렬이 필요합니다.")

    if b.shape[0] != m:
        raise ValueError("A와 b의 행 수가 같아야 합니다.")

    # 첨가행렬 [A | b]
    M = np.hstack([A.copy(), b.reshape(-1, 1)])

    # 초기 상태 기록
    steps = [M.copy()]

    for col in range(n):

        # 피벗 행 선택
        if pivoting:
            pivot_row = col + np.argmax(np.abs(M[col:, col]))
        else:
            pivot_row = col

        # 실제로 0일 때만 실패
        if M[pivot_row, col] == 0.0:
            raise ZeroDivisionError("0인 피벗이 발생했습니다.")

        # 행 교환
        if pivot_row != col:
            M[[col, pivot_row]] = M[[pivot_row, col]]
            steps.append(M.copy())

        # 아래 행 소거
        for row in range(col + 1, n):

            if M[row, col] == 0.0:
                continue

            factor = M[row, col] / M[col, col]

            M[row, col:] -= factor * M[col, col:]

        # 소거 결과 기록
        steps.append(M.copy())

        if verbose:
            print(f"\n--- {col + 1}단계 소거 후 ---")
            print(M)

    # 후진 대입
    x = np.zeros(n)

    for i in range(n - 1, -1, -1):

        if M[i, i] == 0.0:
            raise ZeroDivisionError("0인 피벗이 발생했습니다.")

        x[i] = (
            M[i, -1]
            - np.sum(M[i, i + 1:n] * x[i + 1:n])
        ) / M[i, i]

    return x, steps

def inverse_gauss_jordan(A) -> np.ndarray:
    """가우스-조던 소거로 역행렬을 구한다. [A|I] -> [I|A^-1].

    정사각이 아니면 ValueError, 특이행렬이면 np.linalg.LinAlgError.
    (`np.linalg.inv` 를 부르지 말고 소거로 직접 구한다)
    """
    # TODO: 문제 4-3
    A = np.asarray(A, dtype=float)

    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise ValueError("정사각 행렬이 필요합니다.")

    n = A.shape[0]

    M = np.hstack([A.copy(), np.eye(n)])

    for col in range(n):
        # 부분 피벗팅
        pivot_row = col + np.argmax(np.abs(M[col:, col]))

        if np.isclose(M[pivot_row, col], 0.0):
            raise np.linalg.LinAlgError("특이행렬은 역행렬을 가질 수 없습니다.")

        # 행 교환
        if pivot_row != col:
            M[[col, pivot_row]] = M[[pivot_row, col]]

        # 피벗 행을 1로 정규화
        M[col] /= M[col, col]

        # 현재 열의 다른 행을 모두 0으로 만들기
        for row in range(n):
            if row == col:
                continue

            factor = M[row, col]

            if np.isclose(factor, 0.0):
                continue

            M[row] -= factor * M[col]

    return M[:, n:]
