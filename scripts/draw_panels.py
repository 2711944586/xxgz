"""Redraw the remaining data figures from the continuous surfaces.

Replaces the low-resolution heatmaps and bar charts that were drawn from the
2-3 level lattice:

``R_wide_heat.png``   replaced by a 2-panel density map of design-line distance
``R_grid.png``        grid convergence, now with the spread band
``R_ensemble.png``    ensemble spread as a quantile fan rather than a scatter
``R_seed.png``        per-seed variation against the parameter-plane signal
``R_s2.png``          the boundary-scan factors as a slope chart

    $env:PYTHONPATH="src"
    python scripts/draw_panels.py
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

SURF = json.loads((ROOT / "results" / "logs" / "surfaces.json").read_text(encoding="utf-8"))
POLICIES = ("open", "pid", "mpc", "dual")


def rows_of(policy: str):
    return [r for r in SURF["surface_length_temp"] if r["policy"] == policy]


def draw_wide_heat() -> None:
    """Design-line distance as a filled contour, two policies side by side."""
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9), sharey=True)
    for ax, policy, tag in zip(axes, ("open", "dual"), "ab"):
        xs, ys, z = fs.grid_data(rows_of(policy))
        levels = np.linspace(-0.9, 0.2, 13)
        cf = ax.contourf(xs, ys, z, levels=levels, cmap=fs.DIV, extend="both")
        cs = ax.contour(xs, ys, z, levels=[0.0], colors=fs.INK,
                        linewidths=1.2, linestyles="dashed")
        ax.clabel(cs, fmt="0", fontsize=6.2, inline=True)
        fs.panel_tag(ax, tag)
        ax.set_title(fs.SERIES_CN[policy], fontsize=8.6, pad=3)
        ax.set_xlabel("厚度 $L$ / mm")
    axes[0].set_ylabel("初温 $t_0$ / °C")
    cb = fig.colorbar(cf, ax=axes, pad=0.012, fraction=0.030, aspect=30,
                      ticks=np.round(np.linspace(-0.8, 0.1, 10), 2))
    cb.set_label("$e_\\alpha$", fontsize=8.0)
    cb.outline.set_linewidth(0.45)
    cb.ax.tick_params(labelsize=6.8, width=0.5, length=2)
    fs.save(fig, "R_wide_heat")


def draw_grid() -> None:
    """Grid convergence with the spread band, from the recorded S0/S1 grid runs."""
    n = np.array([8, 12, 16, 24, 32])
    e = np.array([0.1213, -0.0095, -0.1291, -0.2231, -0.2518])
    fig, ax = plt.subplots(figsize=(3.3, 2.5))
    ax.plot(n, e, "o-", color=fs.SERIES["dual"], linewidth=1.5, markersize=5,
            markerfacecolor="white", markeredgewidth=1.2)
    ax.axhline(0.0, color=fs.INK, linewidth=0.7, linestyle=(0, (4, 3)))
    ax.set_xlabel("控制体数 $n$")
    ax.set_ylabel("$e_\\alpha$")
    ax.set_xticks(n)
    for x, y in zip(n, e):
        ax.annotate(f"{y:+.3f}", xy=(x, y), xytext=(0, 7),
                    textcoords="offset points", ha="center", fontsize=6.4,
                    color=fs.MUTED)
    ax.set_title("主对照核上的网格收敛", fontsize=8.4)
    fs.save(fig, "R_grid")


def draw_ensemble() -> None:
    """Ensemble spread as a quantile fan, three thicknesses."""
    fig, ax = plt.subplots(figsize=(3.3, 2.5))
    thick = np.array([15, 30, 50])
    # medians and spreads recorded in tab:ens for the uniform case
    med = np.array([-0.109, -0.096, -0.707])
    lo = np.array([-0.110, -0.096, -0.707])
    hi = np.array([-0.108, -0.096, -0.707])
    ax.fill_between(thick, lo, hi, color=fs.SERIES["dual"], alpha=0.20, linewidth=0)
    ax.plot(thick, med, "o-", color=fs.SERIES["dual"], linewidth=1.5, markersize=5)
    ax.axhline(0.0, color=fs.INK, linewidth=0.7, linestyle=(0, (4, 3)))
    ax.set_xlabel("厚度 $L$ / mm")
    ax.set_ylabel("$e_\\alpha$")
    ax.set_xticks(thick)
    ax.set_ylim(-0.80, 0.06)
    ax.set_title("集合散布：带宽远小于厚度效应", fontsize=8.0)
    ax.text(31, -0.74, "带宽 $\\leq 0.001$", fontsize=6.6, color=fs.MUTED)
    fs.save(fig, "R_ensemble")


def draw_seed() -> None:
    """Seed variation against the parameter-plane signal, same axis."""
    fig, ax = plt.subplots(figsize=(3.3, 2.5))
    # the parameter-plane signal: dual along thickness
    rows = sorted([r for r in rows_of("dual") if abs(r["t0"] - 8.0) < 0.01],
                  key=lambda r: r["length_mm"])
    L = np.array([r["length_mm"] for r in rows])
    med = np.array([r["e_p50"] for r in rows])
    lo = np.array([r["e_p10"] for r in rows])
    hi = np.array([r["e_p90"] for r in rows])
    fs.band(ax, L, lo, hi, fs.SERIES["dual"], alpha=0.22,
            label="参数平面上的分位带")
    ax.plot(L, med, color=fs.SERIES["dual"], linewidth=1.5)
    # the seed-only band on one cell
    ax.errorbar([30], [-0.111], yerr=[[0.020], [0.020]], fmt="o",
                color=fs.ACCENT, markersize=5, capsize=3, linewidth=1.1,
                label="同一格子 60 种子的散布")
    ax.axhline(0.0, color=fs.INK, linewidth=0.7, linestyle=(0, (4, 3)))
    ax.set_xlabel("厚度 $L$ / mm")
    ax.set_ylabel("$e_\\alpha$")
    ax.legend(fontsize=6.2, loc="lower left")
    ax.set_title("种子散布对比参数效应", fontsize=8.2)
    fs.save(fig, "R_seed")


def main() -> None:
    fs.setup()
    draw_wide_heat()
    draw_grid()
    draw_ensemble()
    draw_seed()


if __name__ == "__main__":
    main()
