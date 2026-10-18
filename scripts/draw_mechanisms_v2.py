"""Redraw the mechanism and flow diagrams at journal quality.

The old diagrams were drawn with default matplotlib boxes and arrows: uneven
spacing, no visual hierarchy, labels colliding with frames. These replace them
with a consistent drafting grid, a three-level type hierarchy (section label,
box title, box body), and arrows that terminate on box centres.

    $env:PYTHONPATH="src"
    python scripts/draw_mechanisms_v2.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Circle

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import figstyle as fs  # noqa: E402


def stage(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_axis_off()
    return fig, ax


# ---------------------------------------------------------------------------
# 1. Five-layer architecture (replaces architecture.png)
# ---------------------------------------------------------------------------
def draw_architecture() -> None:
    fig, ax = stage(4.9, 4.6)
    ax.set_xlim(-1.2, 8.0)
    ax.set_ylim(0, 7.0)
    ax.set_aspect("equal")

    layers = [
        ("过程层", "腔体 + 食品边界\n四个执行量", fs.HEAT, 5.55),
        ("多尺度模型", "多孔介质 → 十六条控制体\n→ 两节点降阶", fs.SERIES["mpc"], 4.18),
        ("估计层", "探针窗 → 后验\n标量跟踪器 / EKF", "#4a6b4e", 2.81),
        ("对偶决策", "信息动作 ⊕ 品质动作\n150–190 s 分离", fs.ACCENT, 1.44),
        ("安全层", "水位 · 门 · 漏电 · 管温\n只读硬测量", "#8c2f1f", 0.07),
    ]
    box_h = 1.10
    x0, box_w = 0.85, 5.20
    for title, body, color, y in layers:
        fs.mechanism_box(ax, (x0, y), box_w, box_h, title, body, color,
                         title_size=8.2, body_size=6.6)
    for i in range(len(layers) - 1):
        y_from = layers[i][3]
        y_to = layers[i + 1][3] + box_h
        fs.arrow(ax, (x0 + box_w / 2, y_from - 0.02),
                 (x0 + box_w / 2, y_to + 0.02), color=fs.INK, lw=0.8, head=7)
    # feedback loops routed outside the stack, not across the boxes
    y_bot = layers[4][3] + box_h / 2
    y_top = layers[0][3] + box_h / 2
    xr = x0 + box_w + 0.55
    ax.plot([x0 + box_w, xr], [y_bot, y_bot], color=fs.SERIES["dual"],
            linewidth=0.9, linestyle=(0, (4, 2)))
    ax.plot([xr, xr], [y_bot, y_top], color=fs.SERIES["dual"],
            linewidth=0.9, linestyle=(0, (4, 2)))
    fs.arrow(ax, (xr, y_top), (x0 + box_w, y_top), color=fs.SERIES["dual"],
             lw=0.9, head=7, ls=(0, (4, 2)))
    ax.text(xr + 0.16, (y_bot + y_top) / 2, "指令写回", rotation=90,
            ha="center", va="center", fontsize=6.4, color=fs.SERIES["dual"])

    xl = x0 - 0.55
    y_est = layers[2][3] + box_h / 2
    ax.plot([x0, xl], [y_est, y_est], color=fs.MUTED,
            linewidth=0.9, linestyle=(0, (4, 2)))
    ax.plot([xl, xl], [y_est, y_top], color=fs.MUTED,
            linewidth=0.9, linestyle=(0, (4, 2)))
    fs.arrow(ax, (xl, y_top), (x0, y_top), color=fs.MUTED,
             lw=0.9, head=7, ls=(0, (4, 2)))
    ax.text(xl - 0.16, (y_est + y_top) / 2, "可安装观测", rotation=90,
            ha="center", va="center", fontsize=6.4, color=fs.MUTED)
    fs.save(fig, "M_architecture")


# ---------------------------------------------------------------------------
# 2. Decision chain (replaces M_chain.png)
# ---------------------------------------------------------------------------
def draw_chain() -> None:
    fig, ax = stage(7.2, 2.4)
    ax.set_xlim(0, 10.2)
    ax.set_ylim(0, 3.4)

    steps = [
        ("边界激励", "执行量离开\n名义轨迹", fs.SERIES["mpc"]),
        ("多尺度状态", "冷点 · 表面\n进度 · 热阻", fs.SERIES["dual"]),
        ("后验", "均值与\n协方差", "#4a6b4e"),
        ("价值分解", "$G(a)$ 与 $Q(z)$\n分开计算", fs.ACCENT),
        ("安全投影", "只读硬测量\n改写指令", fs.HEAT),
        ("新边界", "写回\n积分器", fs.MUTED),
    ]
    w, h, y = 1.42, 1.30, 1.02
    for i, (title, body, color) in enumerate(steps):
        x = 0.18 + i * 1.66
        fs.mechanism_box(ax, (x, y), w, h, title, body, color,
                         title_size=8.0, body_size=6.4)
        if i < len(steps) - 1:
            fs.arrow(ax, (x + w + 0.01, y + h / 2), (x + 1.66 - 0.01, y + h / 2),
                     color=fs.INK, lw=0.8, head=7)
    # loop back
    fs.arrow(ax, (0.18 + 5 * 1.66 + w / 2, y + h + 0.04),
             (0.18 + w / 2, y + h + 0.04),
             color=fs.SERIES["dual"], lw=1.0, rad=0.30, head=9, ls=(0, (4, 2)))
    ax.text(5.1, 3.16, "写回积分器，进入下一次观测", ha="center", va="center",
            fontsize=7.4, color=fs.SERIES["dual"])
    ax.text(0.18, 0.40, "可分离 → 第 4 环    可拦截 → 第 5 环    可重构 → 第 2–3 环    可迁移 → 第 2 环",
            ha="left", va="center", fontsize=6.8, color=fs.MUTED)
    fs.save(fig, "M_chain")


# ---------------------------------------------------------------------------
# 3. Probe timing (new: the separability claim as a timeline)
# ---------------------------------------------------------------------------
def draw_probe_timeline() -> None:
    """Real logged commands, with the 40 s probe window shown as an inset.

    The probe is 40 s inside a 3400 s horizon, so at full scale it is a single
    pixel wide. A synthetic trace would also misrepresent the commands; this
    reads the exported seed-7 trace instead.
    """
    import csv

    path = ROOT / "results" / "logs" / "demo_seed7_dual.csv"
    with path.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    t = np.array([float(r["time"]) for r in rows])
    heat = np.array([float(r["heat_req"]) for r in rows])
    steam = np.array([float(r["steam"]) for r in rows])
    fan = np.array([float(r["fan"]) for r in rows])
    mode = np.array([float(r["mode"]) for r in rows])
    stop_t = 1866.0

    fig, ax = stage(6.6, 2.6)
    ax.set_axis_on()
    for sp in ("left", "top", "right"):
        ax.spines[sp].set_visible(False)
    ax.set_yticks([])
    ax.set_xlabel("时间 / s")
    ax.set_xlim(-300, 3450)

    ax.axvspan(150, 190, color=fs.ACCENT, alpha=0.65, linewidth=0, zorder=3)
    ax.axvline(stop_t, color=fs.INK, linewidth=0.8, linestyle=(0, (3, 2)))

    cfg = [("加热请求 $u$", heat, 3.30, fs.HEAT, 1.00),
           ("蒸汽 $s$", steam, 2.35, fs.SERIES["mpc"], 1.00),
           ("风机 $f$", fan, 1.40, fs.SERIES["dual"], 1.35),
           ("模式", mode / 2.0, 0.45, fs.ACCENT, 1.00)]
    for name, vals, ybase, color, scale in cfg:
        ax.plot(t, ybase + 0.48 * np.clip(vals, 0, None) / scale, color=color,
                linewidth=1.0, solid_capstyle="round")
        ax.text(-50, ybase + 0.22, name, ha="right", va="center", fontsize=6.8,
                color=color)
    ax.annotate("探针窗 150–190 s", xy=(175, 4.02), xytext=(430, 4.10),
                fontsize=6.4, color=fs.ACCENT, ha="left", va="center",
                arrowprops=dict(arrowstyle="-", color=fs.ACCENT, linewidth=0.6))
    ax.text(stop_t + 35, 4.10, "停机 1866 s", fontsize=6.4, color=fs.INK,
            va="center")
    ax.set_ylim(0.20, 4.50)

    axin = fig.add_axes([0.335, 0.58, 0.19, 0.30])
    win = (t >= 140) & (t <= 200)
    axin.plot(t[win], steam[win], color=fs.SERIES["mpc"], linewidth=1.0,
              label="蒸汽 $s$")
    axin.plot(t[win], fan[win], color=fs.SERIES["dual"], linewidth=1.0,
              label="风机 $f$")
    axin.set_xlim(140, 200)
    axin.set_ylim(0, 1.55)
    axin.set_yticks([0, 1])
    axin.tick_params(labelsize=5.4, width=0.5, length=1.5, pad=1)
    axin.set_title("放大：先蒸汽、后风机", fontsize=5.6, pad=2)
    axin.legend(fontsize=5.0, handlelength=0.8, labelspacing=0.10,
                loc="upper center", ncol=2, borderaxespad=0.05)
    for sp in ("top", "right"):
        axin.spines[sp].set_visible(False)
    axin.spines["left"].set_linewidth(0.5)
    axin.spines["bottom"].set_linewidth(0.5)
    fs.save(fig, "M_probe_timeline")


def main() -> None:
    fs.setup()
    draw_architecture()
    draw_chain()
    draw_probe_timeline()


if __name__ == "__main__":
    main()
