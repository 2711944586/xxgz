"""Draw the ill-posedness figure that ch2 argues about but never showed.

ch2 states that the amplification e^{kL} at 30 mm with a 40 s harmonic is about
1.46e8, and that at menu timescales it drops to tens. Those numbers are the reason
the whole probe design exists, yet the chapter had one figure and none of them
showed this.

Plotted from the analytic relation: for angular frequency omega, the decay
constant is k = sqrt(omega / (2 alpha)), so the amplification needed to recover a
depth-L component is exp(k L). Three curves at the two probe timescales and the
menu timescale, on a log axis, with the 30 mm operating point marked.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import figstyle as fs  # noqa: E402

fs.setup()

ALPHA = 2.0e-7  # m^2/s, the value stated in the paper
depth = np.linspace(0.001, 0.060, 300)  # m

fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.9))

# --- panel a: amplification vs depth for several timescales -------------
ax = axes[0]
cases = [
    ("40 s（探针窗）", 40.0, fs.SERIES["dual"]),
    ("200 s（探针后半）", 200.0, fs.SERIES["mpc"]),
    ("1170 s（菜单时间）", 1170.0, fs.ACCENT),
]
for label, T, color in cases:
    omega = 2 * np.pi / T
    k = np.sqrt(omega / (2 * ALPHA))
    amp = np.exp(k * depth)
    ax.semilogy(depth * 1000, amp, color=color, linewidth=1.5, label=label)

# the 30 mm operating point for the 20 s case
k20 = np.sqrt((2 * np.pi / 40.0) / (2 * ALPHA))
ax.plot([30], [np.exp(k20 * 0.030)], "o", color=fs.SERIES["dual"],
        markersize=6, markeredgecolor="white", markeredgewidth=0.8, zorder=5)
ax.annotate(f"$1.5\\times10^{{8}}$", xy=(30, np.exp(k20 * 0.030)),
            xytext=(-34, -4), textcoords="offset points", fontsize=7.0,
            color=fs.SERIES["dual"])
ax.axvline(30, color=fs.MUTED, linewidth=0.6, linestyle=(0, (3, 3)))
ax.set_xlabel("深度 $L$ / mm")
ax.set_ylabel("恢复该深度所需的噪声放大 $e^{kL}$")
ax.set_title("高频分量的指数放大", fontsize=8.4)
ax.legend(fontsize=6.6, loc="lower right")
ax.set_xlim(0, 60)
fs.panel_tag(ax, "a")

# --- panel b: amplification at 30 mm vs timescale ----------------------
ax = axes[1]
T = np.logspace(np.log10(5), np.log10(3000), 200)
k = np.sqrt((2 * np.pi / T) / (2 * ALPHA))
amp30 = np.exp(k * 0.030)
ax.loglog(T, amp30, color=fs.SERIES["dual"], linewidth=1.7)
for sec, lab in ((40, "探针窗"), (1170, "菜单")):
    kk = np.sqrt((2 * np.pi / sec) / (2 * ALPHA))
    val = np.exp(kk * 0.030)
    ax.plot([sec], [val], "o", color=fs.HEAT, markersize=5.5,
            markeredgecolor="white", markeredgewidth=0.8, zorder=5)
    ax.annotate(lab, xy=(sec, val), xytext=(6, 8), textcoords="offset points",
                fontsize=6.6, color=fs.HEAT)
ax.set_xlabel("激励时间尺度 $T$ / s")
ax.set_ylabel("$30\\,\\mathrm{mm}$ 处放大")
ax.set_title("越短的激励，需要的放大越大", fontsize=8.4)
fs.panel_tag(ax, "b")

fs.save(fig, "P_illposed")
