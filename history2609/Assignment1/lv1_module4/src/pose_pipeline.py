"""문제 2 — camera 에서 base 로의 변환 파이프라인. (학생 작성용 템플릿)

모듈 ③ 의 회전·동차변환·좌표 체인 모듈을 한데 묶어 쓰는 `PosePipeline` 을 작성한다.

    base --T_base_link--> link --T_link_camera--> camera --(관측)--> 물체 점군

    T_base_camera = T_base_link @ T_link_camera
    P_base        = transform_points(T_base_camera, P_cam)      # (N,3) 한 번에

관절이 움직이면 link 변환이 바뀐다. 이 템플릿은 "link 가 자기 z축 둘레로 theta 만큼
돈다" 로 단순화한다 (`set_joint_angle`). 실제 로봇이라면 관절마다 축과 오프셋이 다르다.
"""

from __future__ import annotations

import numpy as np

from .rotation import rot_x, rot_y, rot_z
from .transform import inv_T, make_T, transform_points

__all__ = ["PosePipeline"]


_ROT = {"x": rot_x, "y": rot_y, "z": rot_z}


class PosePipeline:
    """base -> link -> camera 변환을 보관하고 카메라 점군을 base 좌표로 바꾼다."""

    def __init__(self, T_base_link, T_link_camera, joint_axis: str = "z"):
        # 입력을 float ndarray로 변환
        T_base_link = np.asarray(T_base_link, dtype=float)
        T_link_camera = np.asarray(T_link_camera, dtype=float)

        # 변환행렬 크기 확인
        if T_base_link.shape != (4, 4):
            raise ValueError("T_base_link must have shape (4, 4)")

        if T_link_camera.shape != (4, 4):
            raise ValueError("T_link_camera must have shape (4, 4)")

        # 회전축 확인
        if joint_axis not in _ROT:
            raise ValueError("joint_axis must be one of 'x', 'y', or 'z'")

        # 관절 0도에서의 기준 변환
        self._T_base_link0 = T_base_link

        # link -> camera는 고정
        self._T_link_camera = T_link_camera

        # 관절 설정
        self.joint_axis = joint_axis
        self.joint_angle = 0.0

    # -------------------------------------------------------------
    # 변환 행렬

    @property
    def T_base_link(self) -> np.ndarray:
        """현재 관절 각도가 반영된 T(base <- link)."""

        R_axis = _ROT[self.joint_axis](self.joint_angle)

        T_joint = make_T(
            R_axis,
            [0.0, 0.0, 0.0]
        )

        return self._T_base_link0 @ T_joint

    @property
    def T_link_camera(self) -> np.ndarray:
        """T(link <- camera) — 카메라는 link에 고정되어 있다."""

        return self._T_link_camera

    @property
    def T_base_camera(self) -> np.ndarray:
        """합성 변환 T(base <- camera)."""

        return self.T_base_link @ self.T_link_camera

    @property
    def T_camera_base(self) -> np.ndarray:
        """역변환 T(camera <- base)."""

        return inv_T(self.T_base_camera)

    # -------------------------------------------------------------
    # 관절

    def set_joint_angle(self, theta: float) -> "PosePipeline":
        """관절 각도 [rad]를 변경하고 self를 반환한다."""

        self.joint_angle = float(theta)

        return self

    # -------------------------------------------------------------
    # 점군 변환

    def camera_to_base(self, P_cam) -> np.ndarray:
        """카메라 기준 점군 또는 점을 base 기준으로 변환한다."""

        return transform_points(
            self.T_base_camera,
            P_cam
        )

    def base_to_camera(self, P_base) -> np.ndarray:
        """base 기준 점군 또는 점을 camera 기준으로 되돌린다."""

        return transform_points(
            self.T_camera_base,
            P_base
        )

    def object_pose_in_base(self, T_camera_object) -> np.ndarray:
        """카메라 기준 물체 자세를 base 기준 물체 자세로 변환한다."""

        T_camera_object = np.asarray(T_camera_object, dtype=float)

        if T_camera_object.shape != (4, 4):
            raise ValueError("T_camera_object must have shape (4, 4)")

        return self.T_base_camera @ T_camera_object

    def __repr__(self) -> str:
        return "PosePipeline(joint_axis={!r}, joint_angle={:.4f} rad)".format(
            getattr(self, "joint_axis", "?"),
            getattr(self, "joint_angle", float("nan"))
        )