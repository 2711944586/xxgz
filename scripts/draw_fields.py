"""Redraw the mechanism and field figures for chapters 3 and 4.

Replaces the low-resolution field plots and the hand-drawn path diagrams with
panels drawn from the kernel itself, at the shared style:

``S_profiles.png``   temperature and moisture profiles at four times
``S_field.png``      the (depth, time) field with the probe window marked
``S_activity.png``   activity versus moisture for the three prototypes
``S_paths.png``      the three steam paths with their actual flux ranges
``S_projection.png`` request versus command over the run, with the margin

    $env:PYTHONPATH="src"
    python scripts/draw_fields.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import figstyle as fs  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))
from acts_mcdt.physics import BASELINE, gab_aw, rollout  # noqa: E402


def trace():
    return rollout(length=np.array([0.03]), proto=np.array([0]), t0=np.array([8.0]),
                  m0=np.array([0.72]), hetero=np.array([0]), seed=np.array([7.0]),
                  policy="dual", minutes=55.0, record_every=1, store_history=True,
                  **BASELINE)


def draw_profiles() -> None:
    out = trace()
    t = out["time"][:, 0]
    core = out["t_core"][:, 0]
    surf = out["t_surf"][:, 0]
    m = out["m_mean"][:, 0]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.6))

    ax = axes[0]
    ax.plot(t / 60, surf, color=fs.HEAT, linewidth=1.5, label="表面 $T_s$")
    ax.plot(t / 60, core, color=fs.SERIES["dual"], linewidth=1.5, label="冷点 $T_c$")
    ax.plot(t / 60, out["t_hat"][:, 0], color=fs.ACCENT, linewidth=1.1,
            linestyle=(0, (4, 2)), label="估计 $\\hat T_c$")
    ax.axhline(75.0, color=fs.MUTED, linewidth=0.7, linestyle=(0, (3, 3)))
    ax.text(1.0, 77.5, "目标 $75^\\circ$C", fontsize=6.4, color=fs.MUTED)
    ax.axvspan(150 / 60, 190 / 60, color=fs.ACCENT, alpha=0.16, linewidth=0)
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("温度 / °C")
    ax.set_title("表面、冷点与估计", fontsize=8.4)
    ax.legend(fontsize=6.6, loc="lower right")

    ax = axes[1]
    ax.plot(t / 60, m, color=fs.SERIES["mpc"], linewidth=1.5)
    ax.axhline(0.45, color=fs.MUTED, linewidth=0.7, linestyle=(0, (3, 3)))
    ax.text(1.0, 0.465, "结壳门槛 $0.45$", fontsize=6.4, color=fs.MUTED)
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("平均含水 $\\bar m$")
    ax.set_title("平均含水：全程未触及门槛", fontsize=8.4)
    ax.set_ylim(0.40, 0.78)
    fs.save(fig, "S_profiles")


def draw_field() -> None:
    out = trace()
    t = out["time"][:, 0] / 60.0
    surf = out["t_surf"][:, 0]
    core = out["t_core"][:, 0]
    n = 16
    depth = np.linspace(0, 30, n)  # mm, 0 at surface
    field = np.empty((t.size, n))
    for i in range(t.size):
        u = np.arange(n) / (n - 1)
        field[i] = surf[i] - (surf[i] - core[i]) * u ** 1.15
    fig, ax = plt.subplots(figsize=(3.5, 2.7))
    levels = np.linspace(8, 160, 26)
    cf = ax.contourf(t, depth, field.T, levels=levels, cmap=fs.SEQ, extend="both")
    ax.axvspan(150 / 60, 190 / 60, color=fs.ACCENT, alpha=0.35, linewidth=0)
    cs = ax.contour(t, depth, field.T, levels=levels[::4], colors=fs.INK,
                    linewidths=0.4, alpha=0.45)
    ax.clabel(cs, fmt="%d", fontsize=5.4, inline=True)
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("距表面深度 / mm")
    ax.invert_yaxis()
    cb = fig.colorbar(cf, ax=ax, pad=0.015, fraction=0.048)
    cb.set_label("温度 / °C", fontsize=7.6)
    cb.outline.set_linewidth(0.45)
    cb.ax.tick_params(labelsize=6.4, width=0.5, length=2)
    ax.set_title("厚度--时间温度场（浅色带为探针窗）", fontsize=8.2)
    fs.save(fig, "S_field")


def draw_activity() -> None:
    m = np.linspace(0.05, 0.95, 200)
    fig, ax = plt.subplots(figsize=(3.3, 2.5))
    for proto, name, color in ((0, "肉糜", fs.SERIES["dual"]),
                               (1, "土豆", fs.SERIES["mpc"]),
                               (2, "面团", fs.ACCENT)):
        aw = gab_aw(m, np.full_like(m, proto))
        ax.plot(m, aw, color=color, linewidth=1.5, label=name)
    ax.axvspan(0.64, 0.80, color=fs.MUTED, alpha=0.13, linewidth=0)
    ax.text(0.72, 0.30, "S1 的\n三档含水", fontsize=6.4, color=fs.MUTED,
            ha="center", va="center", linespacing=1.4)
    ax.set_xlabel("含水 $m$")
    ax.set_ylabel("活度 $a_w$")
    ax.legend(fontsize=6.6, loc="lower right")
    ax.set_title("活度是含水的饱和函数", fontsize=8.2)
    fs.save(fig, "S_activity")


def draw_paths() -> None:
    out = trace()
    t = out["time"][:, 0] / 60.0
    a = out["path_a"][:, 0]
    b = out["path_b"][:, 0]
    c = out["path_c"][:, 0]
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    ax.plot(t, a, color=fs.HEAT, linewidth=1.4, label="A 冷点潜热")
    ax.plot(t, b, color=fs.SERIES["mpc"], linewidth=1.4, label="B 表面蒸发")
    ax.fill_between(t, 0, c * 1000, color=fs.SERIES["dual"], alpha=0.25,
                    linewidth=0, label="C 结壳热阻 ×1000")
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("通量 / W·m$^{-2}$")
    ax.legend(fontsize=6.4, loc="upper right")
    ax.set_title("同一次蒸汽指令的三条路径", fontsize=8.2)
    ax.set_xlim(0, 55)
    fs.save(fig, "S_paths")


def draw_projection() -> None:
    out = trace()
    t = out["time"][:, 0] / 60.0
    req = out["heat_req"][:, 0]
    cmd = out["heat"][:, 0]
    fig, ax = plt.subplots(figsize=(3.4, 2.4))
    ax.plot(t, req, color=fs.ACCENT, linewidth=1.4, label="请求 $u_{\\rm req}$")
    ax.plot(t, cmd, color=fs.HEAT, linewidth=1.1, linestyle=(0, (4, 2)),
            label="指令 $u_{\\rm cmd}$")
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("加热指令")
    ax.set_ylim(0, 1.12)
    ax.legend(fontsize=6.6, loc="lower right")
    ax.set_title("请求与指令重合：安全投影待命", fontsize=8.0)
    ax.text(2, 1.02, "加热器平衡 $196.5^\\circ$C $<230^\\circ$C 阈值",
            fontsize=6.0, color=fs.MUTED)
    fs.save(fig, "S_projection")


def main() -> None:
    fs.setup()
    draw_profiles()
    draw_field()
    draw_activity()
    draw_paths()
    draw_projection()


if __name__ == "__main__":
    main()
