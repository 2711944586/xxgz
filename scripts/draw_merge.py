"""Merge the four small grid/ablation panels into two readable ones.

The four figures on one page (S0 pair scatter, S0 delta box, grid convergence,
heterogeneity quantiles) were each squeezed to ~80 mm and became unreadable.
Two combined panels carry the same content at a legible size:

``R_grid_merge.png``  left: S0 16-vs-8 pairing; right: grid convergence
``R_factors.png``     factor marginal effects with confidence bands

    $env:PYTHONPATH="src"
    python scripts/draw_merge.py
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

LOG = ROOT / "results" / "logs"


def draw_grid_merge() -> None:
    s0 = json.loads((LOG / "s0_summary.json").read_text(encoding="utf-8"))
    e16 = np.array([r["e16"] for r in s0])
    e8 = np.array([r["e8"] for r in s0])

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8))
    ax = axes[0]
    # S0 has only four distinct pairings, so a scatter is the wrong chart:
    # plot each policy-free pairing as a horizontal pair of markers instead.
    from collections import Counter
    counts = Counter((round(a, 3), round(b, 3)) for a, b in zip(e16, e8))
    pairs = sorted(counts.items(), key=lambda kv: -kv[0][0])
    for i, ((a, b), c) in enumerate(pairs):
        ax.plot([a, b], [i, i], color=fs.MUTED, linewidth=0.7, zorder=1)
        ax.scatter([a], [i], s=34, color=fs.SERIES["mpc"], zorder=3,
                   label="十六格" if i == 0 else None)
        ax.scatter([b], [i], s=34, color=fs.SERIES["dual"], zorder=3,
                   label="八格" if i == 0 else None)
        ax.text(0.235, i + 0.30, f"$n={c}$", va="bottom", ha="right",
                fontsize=6.4, color=fs.MUTED)
    ax.axvline(0.0, color=fs.INK, linewidth=0.7, linestyle=(0, (4, 3)))
    ax.set_yticks([])
    ax.set_xlim(-0.95, 0.26)
    ax.set_ylim(-0.7, len(pairs) - 0.2)
    ax.set_xlabel("停机进度偏差 $e_\\alpha$")
    ax.set_title("S0 配对：八格一律更正（右移）", fontsize=8.4)
    ax.legend(fontsize=6.4, loc="lower left", handletextpad=0.3,
              borderaxespad=0.2)
    fs.panel_tag(ax, "a")
    ax.text(-0.93, len(pairs) - 0.55, "$\\Delta e$ 中位 $0.227$", fontsize=6.6,
            color=fs.MUTED)

    ax = axes[1]
    n = np.array([8, 12, 16, 24, 32])
    e = np.array([0.1213, -0.0095, -0.1291, -0.2231, -0.2518])
    ax.plot(n, e, "o-", color=fs.SERIES["dual"], linewidth=1.5, markersize=5,
            markerfacecolor="white", markeredgewidth=1.2)
    ax.axhline(0.0, color=fs.INK, linewidth=0.7, linestyle=(0, (4, 3)))
    ax.set_xlabel("控制体数 $n$")
    ax.set_ylabel("$e_\\alpha$")
    ax.set_xticks(n)
    ax.set_title("主对照核的网格收敛", fontsize=8.4)
    fs.panel_tag(ax, "b")
    for x, y in zip(n, e):
        ax.annotate(f"{y:+.3f}", xy=(x, y), xytext=(0, 7),
                    textcoords="offset points", ha="center", fontsize=6.2,
                    color=fs.MUTED)
    fs.save(fig, "R_grid_merge")


def draw_factors() -> None:
    """Factor marginals from the S1 dual rows, with bootstrap intervals."""
    s1 = json.loads((LOG / "s1_summary.json").read_text(encoding="utf-8"))
    dual = [r for r in s1 if r["policy"] == "dual"]
    rng = np.random.default_rng(7)

    def q(values):
        v = np.array(values)
        med = float(np.median(v))
        idx = rng.integers(0, v.size, size=(800, v.size))
        boots = np.median(v[idx], axis=1)
        return med, float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))

    fig, ax = plt.subplots(figsize=(3.4, 2.7))
    groups = [
        ("厚度", [("15", [r["e_alpha"] for r in dual if r["length_mm"] == 15.0]),
                  ("30", [r["e_alpha"] for r in dual if r["length_mm"] == 30.0]),
                  ("50", [r["e_alpha"] for r in dual if r["length_mm"] == 50.0])]),
        ("初温", [("5", [r["e_alpha"] for r in dual if r["t0"] == 5.0]),
                  ("20", [r["e_alpha"] for r in dual if r["t0"] == 20.0])]),
        ("非均质", [("0", [r["e_alpha"] for r in dual if r["hetero"] == 0]),
                    ("1", [r["e_alpha"] for r in dual if r["hetero"] == 1]),
                    ("2", [r["e_alpha"] for r in dual if r["hetero"] == 2])]),
    ]
    x = 0.0
    ticks, labels = [], []
    for name, levels in groups:
        for lv, vals in levels:
            med, lo, hi = q(vals)
            ax.errorbar([x], [med], yerr=[[med - lo], [hi - med]], fmt="o",
                        color=fs.SERIES["dual"], markersize=4.5, capsize=2.4,
                        linewidth=1.0)
            ticks.append(x)
            labels.append(lv)
            x += 1.0
        x += 0.5
        ax.text(x - 0.5 - len(levels) / 2, -0.95, name, ha="center",
                fontsize=6.8, color=fs.MUTED)
    ax.axhline(0.0, color=fs.INK, linewidth=0.7, linestyle=(0, (4, 3)))
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels, fontsize=6.2)
    ax.set_ylabel("$e_\\alpha$ 中位与 95\\% 区间")
    ax.set_ylim(-1.0, 0.25)
    ax.set_title("对偶策略的因子边际", fontsize=8.2)
    fs.save(fig, "R_factors")


def main() -> None:
    fs.setup()
    draw_grid_merge()
    draw_factors()


if __name__ == "__main__":
    main()
