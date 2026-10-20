"""Redraw the stop map with honest encoding: ticks, not arbitrary bar lengths.

The previous version used bar length to suggest "how far each path reaches", but
the lengths were invented -- the tables in ch2 say which quantities each path
closes, not by how much. Encoding an unmeasured quantity as length would invite
the reader to compare bar lengths that mean nothing.

Replaced with a matrix: rows are the seven product paths plus this paper, columns
are the four layers (actuators / boundary observation / internal state /
posterior). A filled dot means the path closes that layer, a hollow dot means it
does not. That is exactly what the two tables state, and nothing more.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import figstyle as fs  # noqa: E402

fs.setup()

fig, ax = plt.subplots(figsize=(7.1, 3.3))
ax.set_xlim(0, 10)
ax.set_ylim(0, 8.6)
ax.set_axis_off()

COLS = ["执行量", "边界观测", "内部状态", "后验"]
XS = [3.5, 5.3, 7.1, 8.9]

for x, label in zip(XS, COLS):
    ax.text(x, 8.15, label, ha="center", va="center", fontsize=7.2, color=fs.INK)

# vertical guides separate the layers
for x in (4.4, 6.2, 8.0):
    ax.plot([x, x], [0.85, 7.72], color=fs.GRID, linewidth=0.6, zorder=0)

ROWS = [
    ("机械定时",            [0, 0, 0, 0]),
    ("腔温闭环",            [1, 1, 0, 0]),
    ("按重量调用曲线",      [1, 1, 0, 0]),
    ("穿刺探针",            [1, 1, 0, 0]),
    ("表面红外",            [1, 1, 0, 0]),
    ("边界湿度闭环",        [1, 1, 0, 0]),
    ("图像分类 + 曲线",     [1, 1, 0, 0]),
]

y = 7.30
for name, marks in ROWS:
    ax.text(3.15, y, name, ha="right", va="center", fontsize=7.0, color=fs.INK)
    for x, m in zip(XS, marks):
        if m:
            ax.add_patch(Circle((x, y), 0.105, facecolor=fs.SERIES["open"],
                                edgecolor="none", zorder=3))
        else:
            ax.add_patch(Circle((x, y), 0.10, facecolor="none",
                                edgecolor=fs.FAINT, linewidth=0.9, zorder=3))
    y -= 0.78

# separator then this paper
ax.plot([0.55, 9.55], [y + 0.38, y + 0.38], color=fs.MUTED, linewidth=0.7)

ax.text(3.15, y, "本文（对偶）", ha="right", va="center", fontsize=7.4,
        color=fs.SERIES["dual"], fontweight="bold")
for x, m in zip(XS, [1, 1, 1, 1]):
    ax.add_patch(Circle((x, y), 0.115, facecolor=fs.SERIES["dual"],
                        edgecolor="none", zorder=3))

ax.text(0.55, 0.30,
        "实心＝该路径闭合了这一层；空心＝没有。前七行据表 2.2 与表 2.3 逐条核对；"
        "本文新增的是内部状态与后验两列。",
        fontsize=6.2, color=fs.MUTED)
ax.text(7.1, y - 0.52, "150–190 s 探针", ha="center", fontsize=6.4,
        color=fs.SERIES["dual"])
ax.annotate("", xy=(8.9, y - 0.30), xytext=(7.1, y - 0.30),
            arrowprops=dict(arrowstyle="-|>", color=fs.SERIES["dual"], linewidth=0.9))

fs.save(fig, "P_stopmap")
