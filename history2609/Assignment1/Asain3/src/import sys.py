from __future__ import annotations
import numpy as np

_all_ = [
    "angle_between", 
    "cross", 
    "det", 
    "dot", 
    "norm", 
    "normalize",]



    # 1-1. 내적
def dot(a, b):
        """
        두 벡터의 내적을 계산한다.
        """
        a = np.asarray(a, dtype=float)
        b = np.asarray(b, dtype=float)

        if a.shape != b.shape:
            raise ValueError("두 벡터의 크기가 같아야 합니다.")

        return np.sum(a * b)

    # 1-1. 놈(norm)
def norm(a):
        """
        벡터의 L2 norm(길이)을 계산한다.
        """
        a = np.asarray(a, dtype=float)

        return np.sqrt(np.sum(a ** 2))

    # 1-1. 사이각
def angle_between(a, b):
        """
        두 벡터 사이의 각도를 라디안으로 반환한다.
        """
        a = np.asarray(a, dtype=float)
        b = np.asarray(b, dtype=float)

        norm_a = VectorMath.norm(a)
        norm_b = VectorMath.norm(b)

        if norm_a == 0 or norm_b == 0:
            raise ValueError("영벡터와는 사이각을 구할 수 없습니다.")

        cos_theta = VectorMath.dot(a, b) / (norm_a * norm_b)

        # 부동소수점 오차로 인해 1보다 조금 커지는 것을 방지
        cos_theta = np.clip(cos_theta, -1.0, 1.0)

        return np.arccos(cos_theta)

    # 1-2. 정규화
def normalize(a):
        """
        벡터의 길이를 1로 정규화한다.
        """
        a = np.asarray(a, dtype=float)

        norm_a = VectorMath.norm(a)

        if norm_a == 0:
            raise ValueError("영벡터는 정규화할 수 없습니다.")

        return a / norm_a

    # 1-3. 정사영
def project(a, b):
        """
        벡터 a를 벡터 b에 정사영한다.

        proj_b(a) = (a·b / b·b) b
        """
        a = np.asarray(a, dtype=float)
        b = np.asarray(b, dtype=float)

        denominator = VectorMath.dot(b, b)

        if denominator == 0:
            raise ValueError("영벡터에는 정사영할 수 없습니다.")

        coefficient = VectorMath.dot(a, b) / denominator

        return coefficient * b

    # 1-3. 정사영 후 남는 성분
def reject(a, b):
        """
        벡터 a에서 b 방향의 성분을 제거한 나머지 성분을 반환한다.

        reject_b(a) = a - project_b(a)
        """
        a = np.asarray(a, dtype=float)

        return a - VectorMath.project(a, b)

    # 1-4. 반대칭행렬
def skew(v):
        """
        벡터 v = (x, y, z)에 대응하는 반대칭행렬을 만든다.

        [  0  -z   y]
        [  z   0  -x]
        [ -y   x   0]
        """
        v = np.asarray(v, dtype=float)

        if v.shape != (3,):
            raise ValueError("3차원 벡터만 사용할 수 있습니다.")

        x, y, z = v

        return np.array([
            [0, -z,  y],
            [z,  0, -x],
            [-y, x,  0]
        ])

    # 1-4. 외적
def cross(a, b):
        """
        두 3차원 벡터의 외적을 계산한다.
        반대칭행렬을 이용한다.

        a × b = skew(a) @ b
        """
        a = np.asarray(a, dtype=float)
        b = np.asarray(b, dtype=float)

        if a.shape != (3,) or b.shape != (3,):
            raise ValueError("3차원 벡터만 사용할 수 있습니다.")

        return VectorMath.skew(a) @ b

    # 1-5. 세 점이 만드는 평면의 단위 법선
def plane_normal(p1, p2, p3):
        """
        세 점 p1, p2, p3가 만드는 평면의 단위 법선 벡터를 반환한다.
        """
        p1 = np.asarray(p1, dtype=float)
        p2 = np.asarray(p2, dtype=float)
        p3 = np.asarray(p3, dtype=float)

        v1 = p2 - p1
        v2 = p3 - p1

        normal = VectorMath.cross(v1, v2)

        return VectorMath.normalize(normal)

    # 1-6. 행 사다리꼴 형태(row echelon form)
def row_echelon(A):
        """
        행렬을 행 사다리꼴 형태로 변환한다.
        """
        A = np.asarray(A, dtype=float).copy()

        rows, cols = A.shape
        pivot_row = 0

        for col in range(cols):

            if pivot_row >= rows:
                break

            # 현재 열에서 절댓값이 가장 큰 값을 pivot으로 선택
            max_row = pivot_row + np.argmax(
                np.abs(A[pivot_row:, col])
            )

            # 사실상 0인 열이면 다음 열로
            if np.isclose(A[max_row, col], 0):
                continue

            # pivot 행을 위로 이동
            A[[pivot_row, max_row]] = A[[max_row, pivot_row]]

            # pivot 값을 1로 만듦
            A[pivot_row] /= A[pivot_row, col]

            # pivot 아래를 0으로 만듦
            for row in range(pivot_row + 1, rows):
                factor = A[row, col]

                if not np.isclose(factor, 0):
                    A[row] -= factor * A[pivot_row]

            pivot_row += 1

        # 부동소수점 오차로 생긴 아주 작은 값 제거
        A[np.isclose(A, 0)] = 0

        return A

    # 1-6. Rank
def rank(A):
        """
        행렬의 rank를 행 사다리꼴 형태를 이용해 계산한다.
        """
        echelon = VectorMath.row_echelon(A)

        rank = 0

        for row in echelon:
            if not np.allclose(row, 0):
                rank += 1

        return rank

    # 1-6. 행렬식
def det(A):
        """
        행렬식을 재귀적으로 계산한다.
        """
        A = np.asarray(A, dtype=float)

        if A.ndim != 2 or A.shape[0] != A.shape[1]:
            raise ValueError("정사각행렬만 사용할 수 있습니다.")

        n = A.shape[0]

        # 1 x 1
        if n == 1:
            return A[0, 0]

        # 2 x 2
        if n == 2:
            return A[0, 0] * A[1, 1] - A[0, 1] * A[1, 0]

        # Laplace 전개
        result = 0

        for col in range(n):

            minor = np.delete(
                np.delete(A, 0, axis=0),
                col,
                axis=1
            )

            sign = (-1) ** col

            result += (
                sign
                * A[0, col]
                * VectorMath.det(minor)
            )

        return result