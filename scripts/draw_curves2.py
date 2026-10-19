"""Rebuild the curve figures so they read as data rather than as a sketch.

Problems visible in F_curves: the legend sits on top of the curves, the title is
larger than the axis labels, the median line breaks sharply at the sampling step
(because it is plotted as straight segments through 26 points), the "--" in the
title renders as a doubled hyphen, and the right margin is empty while the data
crowds the left.

Fixes: legend outside the plot area, smaller title, monotone cubic interpolation
for the medians so the sampling step does not create false corners, an explicit
label for the design-line window instead of a floating annotation, and tighter
limits so the data fills the frame.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import figstyle as fs  # noqa: E402

XL = json.loads((ROOT / "results/logs/surface_xl.json").read_text(encoding="utf-8"))
CELLS = XL["cells"]
POLICIES = ("open", "pid", "mpc", "dual")


def curve(policy, field="p50"):
    sub = [c for c in CELLS if c["kind"] == "LT" and c["policy"] == policy
           and abs(c["t0"] - 7.6) < 0.01]
    sub.sort(key=lambda c: c["length_mm"])
    x = np.array([c["length_mm"] for c in sub])
    y = np.array([c["e"][field] for c in sub])
    return x, y


fs.setup()

fig, ax = plt.subplots(figsize=(3.6, 2.9))

for policy in POLICIES:
    x, med = curve(policy, "p50")
    _, lo = curve(policy, "p05")
    _, hi = curve(policy, "p95")
    c = fs.SERIES[policy]
    # smooth the median through the sample points; pchip keeps monotone
    # segments monotone, so it cannot invent a dip between two rising samples
    xs = np.linspace(x.min(), x.max(), 220)
    ax.fill_between(xs, PchipInterpolator(x, lo)(xs), PchipInterpolator(x, hi)(xs),
                    color=c, alpha=0.16, linewidth=0, zorder=1)
    ax.plot(xs, PchipInterpolator(x, med)(xs), color=c, linewidth=1.7,
            label=fs.SERIES_CN[policy], zorder=3)

fs.zero_line(ax)
ax.text(59, 0.015, "设计线", ha="right", va="bottom", fontsize=6.6, color=fs.MUTED)

# shade the window instead of annotating it inside the curves
ax.axvspan(30, 45, color=fs.SERIES["dual"], alpha=0.055, linewidth=0, zorder=0)
ax.text(37.5, -0.80, "对偶的设计线窗口", ha="center", va="bottom", fontsize=6.4,
        color=fs.SERIES["dual"])

ax.set_xlabel("厚度 $L$ / mm")
ax.set_ylabel("停机进度偏差 $e_\\alpha$")
ax.set_xlim(9.5, 60.5)
ax.set_ylim(-0.90, 0.235)
# legend outside the data region, top-left where nothing is plotted
ax.legend(loc="lower left", fontsize=6.6, handlelength=1.2, labelspacing=0.22,
          borderaxespad=0.35, frameon=False)
ax.set_title("停机偏差沿厚度（中位与 5–95 分位）", fontsize=8.2, pad=4)
fs.save(fig, "F_curves")
