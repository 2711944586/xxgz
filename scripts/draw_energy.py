"""Energy versus stopping accuracy: the joint view the text argues from.

The old chapter had three overlapping figures (D11 bar pair, P_energy box,
P_stop histogram) saying the same thing badly. This is one panel that carries
the argument: energy on the horizontal axis, stopping error on the vertical,
one point per policy per thickness, with the open-loop policy visibly cheap
and wrong.

    $env:PYTHONPATH="src"
    python scripts/draw_energy.py
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
POLICIES = ("open", "pid", "mpc", "dual")


def main() -> None:
    fs.setup()
    s1 = json.loads((LOG / "s1_summary.json").read_text(encoding="utf-8"))

    fig, ax = plt.subplots(figsize=(3.6, 3.0))
    marks = {"open": "s", "pid": "^", "mpc": "D", "dual": "o"}
    # hand-placed label offsets so nothing collides with a marker
    offsets = {"open": (10, -2), "pid": (-14, -14), "mpc": (8, -12),
               "dual": (8, 4)}
    for policy in POLICIES:
        rows = [r for r in s1 if r["policy"] == policy]
        e = float(np.median([r["e_alpha"] for r in rows]))
        en = float(np.median([r["energy"] for r in rows]))
        ax.scatter(en, e, s=42, marker=marks[policy], color=fs.SERIES[policy],
                   edgecolor="white", linewidth=0.6, zorder=4,
                   label=fs.SERIES_CN[policy])
        ax.annotate(fs.SERIES_CN[policy], xy=(en, e), xytext=offsets[policy],
                    textcoords="offset points", fontsize=6.6,
                    color=fs.SERIES[policy])

    fs.zero_line(ax)
    ax.set_xlabel("累计加热中位 $E_{50}$")
    ax.set_ylabel("停机进度偏差中位 $e_{\\alpha,50}$")
    ax.set_title("能量与精度的联合", fontsize=8.4)
    ax.text(0.97, 0.06, "越靠右下越好", transform=ax.transAxes, fontsize=6.4,
            color=fs.MUTED, ha="right")
    ax.set_xlim(700, 3600)
    fs.save(fig, "R_energy")

    # Distribution of stopping times as a strip, one row per policy.
    fig, ax = plt.subplots(figsize=(3.6, 2.4))
    for i, policy in enumerate(POLICIES):
        rows = [r for r in s1 if r["policy"] == policy]
        stop = np.array([r["stop_s"] for r in rows])
        # jitter for visibility
        y = i + (np.random.default_rng(0).random(stop.size) - 0.5) * 0.34
        ax.scatter(stop, y, s=1.6, color=fs.SERIES[policy], alpha=0.35,
                   linewidth=0, rasterized=True)
        ax.plot([np.median(stop)], [i], "|", color=fs.INK, markersize=11,
                markeredgewidth=1.4, zorder=5)
    ax.set_yticks(range(len(POLICIES)))
    ax.set_yticklabels([fs.SERIES_CN[p] for p in POLICIES], fontsize=7.4)
    ax.set_xlabel("停机时刻 / s")
    ax.axvline(3300, color=fs.MUTED, linewidth=0.7, linestyle=(0, (3, 3)))
    ax.text(3230, 3.38, "时域终点 3300 s", fontsize=6.2, color=fs.MUTED,
            ha="right", va="center")
    ax.set_ylim(-0.6, 3.6)
    ax.set_title("四条策略的停机时刻分布（竖线为中位）", fontsize=8.0)
    fs.save(fig, "R_stop")


if __name__ == "__main__":
    main()
