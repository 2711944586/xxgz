"""Redraw the Fo/Bi figure: the two lines currently coincide and say nothing.

X_fo_band.png plots Fo(t) and Bi(u_fan) on twin axes. Because both are nearly
linear over the horizon they overlap almost exactly, so the figure carries no
information -- a reader cannot tell whether that overlap is meaningful.

What the section actually argues is a scale separation: at the probe window
Fo << 1 while Bi > 1, which is why the surface responds and the interior does
not. That is better shown as two panels on their own axes with the probe window
marked, plus a third panel giving the concrete numbers at the three thicknesses.
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

ALPHA = 2.0e-7
RHO_C = 3.4e6
K = 0.68
T_HORIZON = 3300.0

fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.5))

# --- panel a: Fo vs time, three thicknesses ----------------------------
ax = axes[0]
t = np.linspace(0, T_HORIZON, 200) / 60.0
for L, color in ((0.015, fs.SERIES["mpc"]), (0.030, fs.SERIES["dual"]),
                 (0.050, fs.ACCENT)):
    ax.plot(t, ALPHA * (t * 60) / L ** 2, color=color, linewidth=1.5,
            label=f"{int(L*1000)} mm")
ax.axhline(1.0, color=fs.INK, linewidth=0.7, linestyle=(0, (4, 3)))
ax.text(1.0, 1.06, "$\\mathrm{Fo}=1$", fontsize=6.4, color=fs.MUTED)
ax.axvspan(2.5, 3.17, color=fs.ACCENT, alpha=0.18, linewidth=0)
ax.set_xlabel("时间 / min")
ax.set_ylabel("$\\mathrm{Fo}=\\alpha t/L^2$")
ax.set_ylim(0, 3.1)
ax.legend(fontsize=6.2, loc="upper left", frameon=False, handlelength=1.2)
ax.set_title("Fourier 数：薄件先走完", fontsize=8.0)
fs.panel_tag(ax, "a")

# --- panel b: Bi vs fan command ---------------------------------------
ax = axes[1]
u = np.linspace(0, 1.3, 120)
for L, color in ((0.015, fs.SERIES["mpc"]), (0.030, fs.SERIES["dual"]),
                 (0.050, fs.ACCENT)):
    ax.plot(u, (12 + 55 * u) * L / K, color=color, linewidth=1.5)
ax.axhline(1.0, color=fs.INK, linewidth=0.7, linestyle=(0, (4, 3)))
ax.axvline(0.4, color=fs.MUTED, linewidth=0.6, linestyle=(0, (3, 3)))
ax.axvline(1.3, color=fs.MUTED, linewidth=0.6, linestyle=(0, (3, 3)))
ax.text(0.45, 3.4, "品质段", fontsize=6.2, color=fs.MUTED)
ax.text(1.16, 0.35, "探针段", fontsize=6.2, color=fs.MUTED, ha="right")
ax.set_xlabel("风机指令 $u_{\\mathrm{fan}}$")
ax.set_ylabel("$\\mathrm{Bi}=hL/k$")
ax.set_title("Biot 数：表面阻力远小于内部", fontsize=8.0)
fs.panel_tag(ax, "b")

# --- panel c: the two numbers at the probe window ----------------------
ax = axes[2]
labels = ["15 mm", "30 mm", "50 mm"]
fo_probe = [ALPHA * 170 / L ** 2 for L in (0.015, 0.030, 0.050)]
bi_probe = [(12 + 55 * 1.3) * L / K for L in (0.015, 0.030, 0.050)]
x = np.arange(3)
ax.bar(x - 0.19, fo_probe, width=0.36, color=fs.SERIES["dual"],
       label="$\\mathrm{Fo}$（探针窗）")
ax.bar(x + 0.19, bi_probe, width=0.36, color=fs.SERIES["mpc"],
       label="$\\mathrm{Bi}$（探针段）")
ax.set_yscale("log")
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_ylabel("数值（对数轴）")
ax.legend(fontsize=5.8, loc="upper center", bbox_to_anchor=(0.5, -0.22),
          ncol=2, frameon=False, handlelength=1.0)
ax.set_title("探针窗内 Fo$\\ll$1 而 Bi$>$1", fontsize=8.0)
fs.panel_tag(ax, "c")
for i, (f, b) in enumerate(zip(fo_probe, bi_probe)):
    ax.text(i - 0.19, f * 1.35, f"{f:.4f}", ha="center", fontsize=5.4,
            color=fs.SERIES["dual"])
    ax.text(i + 0.19, b * 1.35, f"{b:.2f}", ha="center", fontsize=5.4,
            color=fs.SERIES["mpc"])

fs.save(fig, "X_fo_band")
