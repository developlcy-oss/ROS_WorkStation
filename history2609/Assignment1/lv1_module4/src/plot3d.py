"""모듈 ④ — Matplotlib 3D 그림 헬퍼. (제공 코드 — 수정하지 않아도 됩니다)

좌표계(4x4 동차변환)를 x·y·z 축 화살표로 그리고, 점군을 찍고,
자세 궤적을 따라 좌표계가 움직이는 애니메이션을 만든다.
노트북 첫 셀의 `draw_frame` / `setup_axes` 와 같은 함수이며,
문제 6 의 애니메이션은 `animate_frames` 를 그대로 쓰면 된다.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

__all__ = ["draw_frame", "setup_axes", "plot_point_cloud", "animate_frames"]

_AXIS_COLORS = ("r", "g", "b")


def draw_frame(ax, T, scale: float = 0.15, name: str = "", alpha: float = 1.0):
    """동차변환 T(4x4) 가 나타내는 좌표계를 x(빨강)·y(초록)·z(파랑) 화살표로 그린다."""
    T = np.asarray(T, dtype=float)
    o = T[:3, 3]
    for i, c in enumerate(_AXIS_COLORS):
        ax.quiver(*o, *(T[:3, i] * scale), color=c, alpha=alpha, arrow_length_ratio=0.2)
    if name:
        ax.text(*(o + 0.03), name, fontsize=10, weight="bold", alpha=max(alpha, 0.6))


def setup_axes(ax, title: str = "", lim: float = 1.0, center=(0.0, 0.0, 0.0)):
    """축 범위를 center 를 중심으로 +-lim 으로 맞추고 라벨·제목을 붙인다 (등축)."""
    cx, cy, cz = center
    ax.set_xlim(cx - lim, cx + lim)
    ax.set_ylim(cy - lim, cy + lim)
    ax.set_zlim(cz - lim, cz + lim)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    if title:
        ax.set_title(title, fontsize=10)
    ax.set_box_aspect([1, 1, 1])


def plot_point_cloud(ax, P, color="tab:blue", s: float = 6, alpha: float = 0.6, label: str = ""):
    """(N,3) 점군을 산점도로 찍는다."""
    P = np.asarray(P, dtype=float)
    ax.scatter(P[:, 0], P[:, 1], P[:, 2], s=s, c=color, alpha=alpha, label=label, depthshade=False)


def animate_frames(frames, static=None, trail=None, lim: float = 0.8, center=None,
                   scale: float = 0.12, interval: int = 100, title: str = "",
                   moving_name: str = "object", figsize=(6, 6)) -> FuncAnimation:
    """자세 궤적 frames(4x4 리스트)를 따라 좌표계가 움직이는 애니메이션을 만든다.

    Parameters
    ----------
    frames : 움직이는 좌표계의 4x4 동차변환 리스트 (프레임마다 하나)
    static : {이름: 4x4} — 배경에 고정으로 그릴 좌표계 (예: base, camera)
    trail  : (N,3) 위치 궤적 — 지나온 경로를 선으로 남긴다 (None 이면 frames 의 병진 사용)
    lim, center : 축 범위 (center 가 None 이면 궤적 중심)
    interval : 프레임 간격 [ms]

    Returns
    -------
    matplotlib.animation.FuncAnimation
        노트북 재생: `HTML(anim.to_jshtml())`
        GIF 저장  : `anim.save("demo.gif", writer="pillow", fps=10)`
    """
    frames = [np.asarray(T, dtype=float) for T in frames]
    static = static or {}
    path = np.asarray(trail if trail is not None else [T[:3, 3] for T in frames], dtype=float)
    if center is None:
        pts = [path] + [np.asarray(T)[:3, 3][None, :] for T in static.values()]
        center = np.vstack(pts).mean(axis=0)

    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection="3d")

    def update(i):
        ax.cla()
        setup_axes(ax, title or "frame {}/{}".format(i + 1, len(frames)), lim=lim, center=center)
        for name, T in static.items():
            draw_frame(ax, T, scale=scale * 1.3, name=name, alpha=0.5)
        ax.plot(path[:, 0], path[:, 1], path[:, 2], color="gray", lw=0.8, alpha=0.5)
        ax.plot(path[: i + 1, 0], path[: i + 1, 1], path[: i + 1, 2], color="k", lw=1.5)
        draw_frame(ax, frames[i], scale=scale, name=moving_name)
        if title:
            ax.set_title("{}  ({}/{})".format(title, i + 1, len(frames)), fontsize=10)
        return ()

    anim = FuncAnimation(fig, update, frames=len(frames), interval=interval, blit=False)
    plt.close(fig)          # 노트북에 정지 그림이 한 장 더 뜨지 않도록 닫는다
    return anim
