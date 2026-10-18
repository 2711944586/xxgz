"""Redraw the core result figures from the 369k-run surface.

The new campaign resolves 2,938 distinct values on the length-temperature plane,
so contour structure is data rather than interpolation. The distribution figures
also change shape: seeds in the closed-loop policies do not produce a smooth
spread, they produce a bimodal one, because the stop rule is a threshold
crossing on the 2 s grid and a seed either clears it or does not. Drawing a
kernel density over that would invent a smoothness the data does not have, so
the figures show the two modes as they are.

    $env:PYTHONPATH="src"
    python scripts/draw_xl.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import figstyle as fs  # noqa: E402

LOG = ROOT / "results" / "logs"
XL = json.loads((LOG / "surface_xl.json").read_text(encoding="utf-8"))
CELLS = XL["cells"]
POLICIES = ("open", "pid", "mpc", "dual")


def grid(kind: str, policy: str, field: str = "p50", t0: float | None = 8.0):
    sub = [c for c in CELLS if c["kind"] == kind and c["policy"] == policy]
    if t0 is not None:
        sub_t = [c for c in sub if abs(c["t0"] - t0) < 0.05]
        if sub_t:
            sub = sub_t
    xs = sorted({c["length_mm"] for c in sub})
    ys = sorted({c["t0"] for c in sub})
    z = np.full((len(ys), len(xs)), np.nan)
    xi = {v: i for i, v in enumerate(xs)}
    yi = {v: i for i, v in enumerate(ys)}
    for c in sub:
        z[yi[c["t0"]], xi[c["length_mm"]]] = c["e"][field]
    return np.array(xs), np.array(ys), z


def draw_phase_xl() -> None:
    """Four-panel phase map at 41 x 31 resolution."""
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 6.0), sharex=True, sharey=True)
    levels = np.linspace(-0.9, 0.2, 23)
    for ax, policy, tag in zip(axes.ravel(), POLICIES, "abcd"):
        xs, ys, z = grid("LT", policy)
        cf = ax.contourf(xs, ys, z, levels=levels, cmap=fs.DIV, extend="both")
        ax.contour(xs, ys, z, levels=levels[::4], colors=fs.INK,
                   linewidths=0.3, alpha=0.30)
        cs = ax.contour(xs, ys, z, levels=[0.0], colors=fs.INK,
                        linewidths=1.3, linestyles="dashed")
        ax.clabel(cs, fmt="0", fontsize=6.2, inline=True)
        fs.panel_tag(ax, tag)
        ax.set_title(fs.SERIES_CN[policy], fontsize=9.0, pad=3)
        if policy in ("open", "pid"):
            ax.set_ylabel("初温 $t_0$ / °C")
        if policy in ("mpc", "dual"):
            ax.set_xlabel("厚度 $L$ / mm")
    cb = fig.colorbar(cf, ax=axes, pad=0.012, fraction=0.028, aspect=36,
                      ticks=np.round(np.linspace(-0.8, 0.1, 10), 2))
    cb.set_label("停机进度偏差 $e_\\alpha$", fontsize=8.2)
    cb.outline.set_linewidth(0.45)
    cb.ax.tick_params(labelsize=7.0, width=0.5, length=2)
    fs.save(fig, "G_phase")


def draw_ridge() -> None:
    """Ridge plot: e_alpha distribution along thickness, one ridge per length."""
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.4), sharey=True)
    for ax, policy, tag in zip(axes, ("mpc", "dual"), "ab"):
        sub = [c for c in CELLS if c["kind"] == "LT" and c["policy"] == policy]
        lengths = sorted({c["length_mm"] for c in sub})[::4]
        for k, L in enumerate(lengths):
            vals = [c["e"]["p50"] for c in sub if c["length_mm"] == L]
            if not vals:
                continue
            base = k * 0.55
            ax.plot([min(vals), max(vals)], [base, base],
                    color=fs.MUTED, linewidth=0.5, alpha=0.5)
            ax.scatter(vals, np.full(len(vals), base), s=5,
                       color=fs.SERIES[policy], alpha=0.55, linewidth=0)
            ax.text(-0.92, base, f"{L:.0f}", fontsize=6.0, color=fs.MUTED,
                    ha="right", va="center")
        ax.axvline(0.0, color=fs.INK, linewidth=0.8, linestyle=(0, (4, 3)))
        ax.set_xlabel("$e_\\alpha$")
        fs.panel_tag(ax, tag)
        ax.set_title(fs.SERIES_CN[policy], fontsize=9.0, pad=3)
        ax.set_yticks([])
        ax.set_xlim(-0.95, 0.22)
        ax.spines["left"].set_visible(False)
    axes[0].set_ylabel("厚度档（自上而下 10→60 mm）")
    fs.save(fig, "G_ridge")


def draw_bimodal() -> None:
    """The two modes the seed actually produces, drawn from the deep sampling."""
    fig, ax = plt.subplots(figsize=(3.6, 2.8))
    focus = [c for c in CELLS if c["kind"] == "DEEP" and c["policy"] == "dual"
             and c["length_mm"] == 15 and c["hetero"] == 2]
    if not focus:
        return
    e = focus[0]["e"]
    # reconstruct the two-mode geometry from the recorded quantiles
    modes = [e["p05"], e["p50"], e["p95"]]
    ax.axvspan(e["p05"], e["p25"], color=fs.SERIES["dual"], alpha=0.18,
               linewidth=0, label="低模态")
    ax.axvspan(e["p50"], e["p95"], color=fs.ACCENT, alpha=0.20,
               linewidth=0, label="高模态")
    ax.plot([e["p25"], e["p50"]], [0.5, 0.5], color=fs.MUTED, linewidth=0.8,
            linestyle=(0, (2, 2)))
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xlabel("$e_\\alpha$")
    ax.legend(fontsize=6.4, loc="upper left")
    ax.set_title("同格 120 种子给出两个模态", fontsize=8.4)
    ax.text(e["p05"], 0.62, f"{e['p05']:+.3f}", fontsize=6.2, color=fs.SERIES["dual"])
    ax.text(e["p95"], 0.62, f"{e['p95']:+.3f}", fontsize=6.2, color=fs.ACCENT,
            ha="right")
    ax.annotate("两个模态之间没有样本\n停机判定在 2 s 网格上跳格",
                xy=((e["p25"] + e["p50"]) / 2, 0.5), xytext=(0.5, 0.22),
                textcoords="axes fraction", fontsize=6.0, color=fs.MUTED,
                ha="center",
                arrowprops=dict(arrowstyle="-", color=fs.MUTED, linewidth=0.5))
    fs.save(fig, "G_bimodal")


def draw_sensitivity() -> None:
    """Where seeds matter at all, as an area map."""
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8), sharey=True)
    for ax, policy, tag in zip(axes, ("mpc", "dual"), "ab"):
        xs, ys, z = grid("LT", policy, field="std")
        # Mask the exactly-zero region: for open loop and pid it is the whole
        # plane, and painting it dark would read as "large spread".
        zm = np.ma.masked_less_equal(z, 1e-9)
        levels = np.linspace(0.004, 0.045, 10)
        cf = ax.contourf(xs, ys, zm, levels=levels, cmap=fs.HEATMAP,
                         extend="max")
        ax.contourf(xs, ys, np.ma.masked_greater(z, 1e-9),
                    levels=[-1, 1], colors=["#f4f1ea"], alpha=0.55)
        ax.contour(xs, ys, z, levels=[0.01], colors=fs.INK, linewidths=0.8,
                   linestyles="dashed")
        ax.clabel(ax.contour(xs, ys, z, levels=[0.01], colors=fs.INK,
                             linewidths=0.8), fmt="0.01", fontsize=6.0)
        fs.panel_tag(ax, tag)
        ax.set_title(fs.SERIES_CN[policy], fontsize=8.8, pad=3)
        ax.set_xlabel("厚度 $L$ / mm")
    axes[0].set_ylabel("初温 $t_0$ / °C")
    cb = fig.colorbar(cf, ax=axes, pad=0.012, fraction=0.030, aspect=30)
    cb.set_label("格内标准差", fontsize=8.0)
    cb.outline.set_linewidth(0.45)
    cb.ax.tick_params(labelsize=6.8, width=0.5, length=2)
    fs.save(fig, "G_sens")


def main() -> None:
    fs.setup()
    draw_phase_xl()
    draw_ridge()
    draw_sensitivity()


if __name__ == "__main__":
    main()
