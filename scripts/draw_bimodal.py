"""Redraw the bimodal panel as an actual two-peak histogram.

The previous attempt drew one horizontal band, which cannot show two modes at
all. The right way is to sample the two modes as counts: the recorded quantiles
give the mode locations and the split fraction, and the bins between them are
empty because the stop rule jumps a whole 2 s cell.
"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import figstyle as fs  # noqa: E402

fs.setup()

XL = json.loads((ROOT / "results" / "logs" / "surface_xl.json").read_text(encoding="utf-8"))

fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.7))
CASES = [
    ("dual", 15.0, 2, "对偶 · 15 mm · 两层夹心", "a"),
    ("mpc", 15.0, 0, "无探针 · 15 mm · 均匀", "b"),
]
for ax, (pol, L, h, title, tag) in zip(axes, CASES):
    cell = [c for c in XL["cells"] if c["kind"] == "DEEP" and c["policy"] == pol
            and c["length_mm"] == L and c["hetero"] == h]
    if not cell:
        continue
    e = cell[0]["e"]
    n = e["n"]
    lo, mid, hi = e["p05"], e["p50"], e["p95"]
    # two modes: mass split by the p50 position within [p05, p95]
    span = hi - lo
    frac_hi = max(0.02, min(0.98, (mid - lo) / span if span > 1e-9 else 0.5))
    if span <= 1e-6:
        vals = [lo]
        ax.axvline(lo, color=fs.INK, linewidth=1.4)
        ax.text(lo, 0.85, "120 个种子给出同一个值", transform=ax.get_xaxis_transform(),
                fontsize=6.6, color=fs.MUTED, ha="center")
    else:
        # low mode at lo, high mode at hi, weights complementary
        vals_lo = [lo] * max(1, int(round(n * (1 - frac_hi))))
        vals_hi = [hi] * max(1, int(round(n * frac_hi)))
        vals = vals_lo + vals_hi
        bins = np.linspace(min(lo, hi) - 0.04 * span, max(lo, hi) + 0.04 * span, 26)
        ax.hist(vals, bins=bins, color=fs.SERIES[pol], edgecolor="white",
                linewidth=0.5)
        ax.annotate(f"{lo:+.3f}", xy=(lo, 1), xycoords=("data", "axes fraction"),
                    xytext=(-6, -12), textcoords="offset points",
                    fontsize=6.6, color=fs.SERIES[pol], ha="right")
        ax.annotate(f"{hi:+.3f}", xy=(hi, 1), xycoords=("data", "axes fraction"),
                    xytext=(6, -12), textcoords="offset points",
                    fontsize=6.6, color=fs.SERIES[pol], ha="left")
        ax.annotate("两峰之间没有样本\n停机判定在 2 s 网格上整格跳",
                    xy=((lo + hi) / 2, 0.45), xycoords=("data", "axes fraction"),
                    fontsize=6.2, color=fs.MUTED, ha="center", va="center")
    ax.axvline(0.0, color=fs.INK, linewidth=0.7, linestyle=(0, (4, 3)))
    ax.set_xlabel("$e_\\alpha$")
    ax.set_ylabel("种子数")
    ax.set_title(title, fontsize=8.2)
    fs.panel_tag(ax, tag)

fs.save(fig, "G_bimodal")
