"""Draw the information-stop map that ch2 argues from but never showed.

ch2 lists six product paths and six shelf designs in two long tables and then
concludes that all of them stop at boundary quantities or a single puncture point.
That conclusion is structural -- what each path closes versus what stays hidden --
and a table makes the reader assemble it row by row.

The figure puts the layers on one axis: actuators at the left, the observable
boundary in the middle, the internal state at the right. Each product path is a
horizontal bar showing how far it reaches; the empty right-hand region is the
gap the paper fills. Numbers are the ones the chapter already states (seven
product paths, six shelf designs, two sensor channels actually used here).
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import figstyle as fs  # noqa: E402

fs.setup()

fig, ax = plt.subplots(figsize=(7.1, 3.4))
ax.set_xlim(0, 10)
ax.set_ylim(0, 6.3)
ax.set_axis_off()

# column bands
BANDS = [
    (0.10, 2.55, "执行量\n（机器可动）", "#eef2f3"),
    (2.75, 5.35, "边界观测\n（装得上）", "#e8eef1"),
    (5.55, 7.55, "内部状态\n（真正决定熟度）", "#f3ece1"),
    (7.75, 9.90, "这一次过程的\n后验", "#f6e9e4"),
]
for x0, x1, label, color in BANDS:
    ax.add_patch(Rectangle((x0, 0.45), x1 - x0, 5.55, facecolor=color,
                           edgecolor="none", zorder=0))
    ax.text((x0 + x1) / 2, 6.10, label, ha="center", va="center",
            fontsize=7.0, color=fs.MUTED, linespacing=1.4)

ROWS = [
    ("机械定时", 5.05, 0.0, 0.0, fs.SERIES["open"]),
    ("腔温闭环", 4.48, 2.1, 0.0, fs.SERIES["pid"]),
    ("按重量调用曲线", 3.91, 1.5, 0.0, fs.SERIES["open"]),
    ("穿刺探针", 3.34, 1.15, 0.35, fs.SERIES["mpc"]),
    ("表面红外", 2.77, 1.0, 0.0, fs.SERIES["mpc"]),
    ("边界湿度闭环", 2.20, 1.55, 0.0, fs.SERIES["pid"]),
    ("图像分类 + 曲线", 1.63, 1.35, 0.0, fs.SERIES["open"]),
]
BAR_H = 0.38
for name, y, reach, internal, color in ROWS:
    ax.add_patch(FancyBboxPatch((0.55, y - BAR_H / 2), reach, BAR_H,
                                boxstyle="round,pad=0.01,rounding_size=0.05",
                                facecolor=color, edgecolor="none", alpha=0.55,
                                zorder=3))
    ax.text(0.45, y, name, ha="right", va="center", fontsize=6.8, color=fs.INK)
    if internal > 0:
        ax.add_patch(FancyBboxPatch((5.75, y - BAR_H / 2), internal, BAR_H,
                                    boxstyle="round,pad=0.01,rounding_size=0.05",
                                    facecolor=color, edgecolor="none",
                                    alpha=0.30, linestyle="--", zorder=3))

# the paper's own row
Y_SELF = 0.95
ax.add_patch(FancyBboxPatch((0.55, Y_SELF - BAR_H / 2), 2.05, BAR_H,
                            boxstyle="round,pad=0.01,rounding_size=0.05",
                            facecolor=fs.SERIES["dual"], edgecolor="none",
                            alpha=0.75, zorder=3))
ax.add_patch(FancyBboxPatch((2.75, Y_SELF - BAR_H / 2), 2.45, BAR_H,
                            boxstyle="round,pad=0.01,rounding_size=0.05",
                            facecolor=fs.SERIES["dual"], edgecolor="none",
                            alpha=0.45, zorder=3))
ax.add_patch(FancyBboxPatch((5.70, Y_SELF - BAR_H / 2), 1.75, BAR_H,
                            boxstyle="round,pad=0.01,rounding_size=0.05",
                            facecolor=fs.SERIES["dual"], edgecolor="none",
                            alpha=0.30, linestyle="--", zorder=3))
ax.add_patch(FancyBboxPatch((7.70, Y_SELF - BAR_H / 2), 2.0, BAR_H,
                            boxstyle="round,pad=0.01,rounding_size=0.05",
                            facecolor=fs.SERIES["dual"], edgecolor="none",
                            alpha=0.85, zorder=3))
ax.text(0.45, Y_SELF, "本文（对偶）", ha="right", va="center", fontsize=7.2,
        color=fs.SERIES["dual"], fontweight="bold")
ax.text(5.72, Y_SELF + 0.30, "150–190 s 探针", fontsize=6.4,
        color=fs.SERIES["dual"])

# the gap arrow
ax.annotate("", xy=(7.62, 5.45), xytext=(5.62, 5.45),
            arrowprops=dict(arrowstyle="-|>", color=fs.ACCENT, linewidth=1.1))
ax.text(6.62, 5.66, "本文补上的那一段", ha="center", fontsize=6.6, color=fs.ACCENT)

ax.text(0.45, 0.14,
        "实色条＝该路径已经闭合的量；虚线框＝仍隐藏、只在本文被纳入后验的内部状态",
        fontsize=6.2, color=fs.MUTED)

fs.save(fig, "P_stopmap")
