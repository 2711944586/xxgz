"""Redraw the core result figures from the continuous surfaces.

Replaces the old block heatmaps and thread-like violins with:

``F_phase.png``     four-panel phase map e_alpha(L, t0) per policy, plus the
                    zero contour that marks the design line
``F_curves.png``    dense 1D length curves with p10-p90 bands per policy
``F_design.png``    the design-line crossing locus in the (L, t0) plane, which
                    is the figure the policy comparison is really about
``F_moist.png``     the moisture axis, drawn honestly as a collapsed axis

    $env:PYTHONPATH="src"
    python scripts/draw_results.py
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

DATA = json.loads((ROOT / "results" / "logs" / "surfaces.json").read_text(encoding="utf-8"))
POLICIES = ("open", "pid", "mpc", "dual")


def surface(policy: str):
    rows = [r for r in DATA["surface_length_temp"] if r["policy"] == policy]
    return fs.grid_data(rows)


def draw_phase() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(7.1, 5.9), sharex=True, sharey=True)
    levels = np.linspace(-0.9, 0.2, 12)
    for ax, policy, tag in zip(axes.ravel(), POLICIES, "abcd"):
        xs, ys, z = surface(policy)
        cf = ax.contourf(xs, ys, z, levels=levels, cmap=fs.DIV, extend="both")
        cs = ax.contour(xs, ys, z, levels=[0.0], colors=fs.INK,
                        linewidths=1.1, linestyles="dashed")
        ax.contour(xs, ys, z, levels=levels[::3], colors=fs.INK,
                   linewidths=0.35, alpha=0.32)
        ax.clabel(cs, fmt="0", fontsize=6.4, inline=True)
        fs.panel_tag(ax, tag)
        ax.set_title(fs.SERIES_CN[policy], fontsize=8.8, pad=3)
        if policy == POLICIES[0]:
            ax.set_ylabel("初温 $t_0$ / °C")
        if policy in ("mpc", "dual"):
            ax.set_xlabel("厚度 $L$ / mm")
    cb = fig.colorbar(cf, ax=axes, pad=0.012, fraction=0.028, aspect=34,
                      ticks=np.round(np.linspace(-0.8, 0.1, 10), 2))
    cb.set_label("停机进度偏差 $e_\\alpha$", fontsize=8.0)
    cb.outline.set_linewidth(0.45)
    cb.ax.tick_params(labelsize=7.0, width=0.5, length=2)
    fig.suptitle("四条策略在同一参数平面上的停机偏差（虚线为设计线 $e_\\alpha=0$）",
                 fontsize=9.0, y=1.015)
    fs.save(fig, "F_phase")


def draw_curves() -> None:
    fig, ax = plt.subplots(figsize=(3.5, 2.9))
    for policy in POLICIES:
        rows = sorted([r for r in DATA["curves_length"] if r["policy"] == policy],
                      key=lambda r: r["length_mm"])
        L = np.array([r["length_mm"] for r in rows])
        med = np.array([r["e_p50"] for r in rows])
        lo = np.array([r["e_p10"] for r in rows])
        hi = np.array([r["e_p90"] for r in rows])
        c = fs.SERIES[policy]
        ax.fill_between(L, lo, hi, color=c, alpha=0.20, linewidth=0, zorder=1)
        ax.plot(L, med, color=c, linewidth=1.5, label=fs.SERIES_CN[policy], zorder=3)
    fs.zero_line(ax)
    ax.text(59, 0.012, "设计线", ha="right", va="bottom", fontsize=6.8,
            color=fs.MUTED)
    # Shade the window where the dual policy crosses the design line.
    ax.axvspan(30, 45, color=fs.SERIES["dual"], alpha=0.055, linewidth=0, zorder=0)
    ax.annotate("对偶的设计线窗口", xy=(37.5, 0.10), xytext=(24, 0.155),
                fontsize=6.6, color=fs.SERIES["dual"],
                arrowprops=dict(arrowstyle="-", color=fs.SERIES["dual"], linewidth=0.6))
    ax.set_xlabel("厚度 $L$ / mm")
    ax.set_ylabel("停机进度偏差 $e_\\alpha$")
    ax.set_xlim(9, 61)
    ax.set_ylim(-0.90, 0.22)
    ax.legend(loc="lower right", fontsize=6.6, handlelength=1.2,
              borderaxespad=0.3, labelspacing=0.2, framealpha=0.0,
              bbox_to_anchor=(1.0, 0.02))
    ax.set_title("中位线与十分位--九十分位带", fontsize=8.6)
    fs.save(fig, "F_curves")


def draw_design_locus() -> None:
    """Where each policy puts the design line in the (L, t0) plane."""
    fig, ax = plt.subplots(figsize=(3.6, 3.0))
    for policy in POLICIES:
        xs, ys, z = surface(policy)
        if policy in ("pid",):
            # monotone in t0 only; draw the boundary where it crosses
            pass
        X, Y = np.meshgrid(xs, ys)
        try:
            ax.contour(xs, ys, z, levels=[0.0], colors=[fs.SERIES[policy]],
                       linewidths=1.5, linestyles="solid")
        except ValueError:
            continue
    ax.set_xlabel("厚度 $L$ / mm")
    ax.set_ylabel("初温 $t_0$ / °C")
    ax.set_xlim(8, 62)
    handles = [plt.Line2D([], [], color=fs.SERIES[p], linewidth=1.5,
                          label=fs.SERIES_CN[p]) for p in POLICIES]
    ax.legend(handles=handles, loc="upper right", fontsize=7.2)
    ax.set_title("设计线在参数平面上的位置", fontsize=8.8)
    ax.text(10.5, 3.0, "线右上 = 达到设计线\n线左下 = 停在下限", fontsize=6.8,
            color=fs.MUTED, va="bottom", linespacing=1.5)
    fs.save(fig, "F_design")


def draw_moisture() -> None:
    """The moisture axis, shown as what it is: a collapsed axis."""
    fig, ax = plt.subplots(figsize=(3.4, 2.7))
    for policy in ("open", "dual"):
        rows = sorted([r for r in DATA["surface_length_moisture"]
                       if r["policy"] == policy], key=lambda r: (r["length_mm"], r["m0"]))
        for L in sorted({r["length_mm"] for r in rows})[:2]:
            sub = [r for r in rows if r["length_mm"] == L]
            m = np.array([r["m0"] for r in sub])
            e = np.array([r["e_p50"] for r in sub])
            ax.plot(m, e, marker="o", markersize=2.6, linewidth=1.0,
                    color=fs.SERIES[policy],
                    alpha=0.9 if L < 20 else 0.5,
                    label=f"{fs.SERIES_CN[policy]} · {L:.0f} mm")
    ax.set_xlabel("初始含水 $m_0$")
    ax.set_ylabel("$e_\\alpha$")
    ax.legend(fontsize=6.4, ncol=1, loc="best")
    ax.set_title("含水轴是一条平线（活度已饱和）", fontsize=8.4)
    fs.save(fig, "F_moist")


def main() -> None:
    fs.setup()
    draw_phase()
    draw_curves()
    draw_design_locus()
    draw_moisture()


if __name__ == "__main__":
    main()
