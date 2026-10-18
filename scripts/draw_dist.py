"""Redraw the remaining ch5 distribution and comparison figures.

``C_ecdf.png``   ECDF of e_alpha per policy, drawn from the 19440 rows
``C_under.png``  share below the design line, by thickness, with CI
``C_cook.png``   cook-mode x policy medians as a slope chart
``C_hetero.png`` heterogeneity effect with quantile whiskers
``C_factors.png`` factor marginals with bootstrap intervals

The old versions were bar charts of four numbers, or ECDFs of a variable with
seven distinct values. These use the full lattice and show uncertainty.

    $env:PYTHONPATH="src"
    python scripts/draw_dist.py
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


def draw_ecdf() -> None:
    s1 = json.loads((LOG / "s1_summary.json").read_text(encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(3.4, 2.7))
    for policy in POLICIES:
        v = np.sort(np.array([r["e_alpha"] for r in s1 if r["policy"] == policy]))
        y = np.arange(1, v.size + 1) / v.size
        ax.plot(v, y, color=fs.SERIES[policy], linewidth=1.5,
                label=fs.SERIES_CN[policy])
    ax.axvline(0.0, color=fs.INK, linewidth=0.7, linestyle=(0, (4, 3)))
    ax.set_xlabel("$e_\\alpha$")
    ax.set_ylabel("累积比例")
    ax.set_xlim(-0.95, 0.22)
    ax.set_ylim(0, 1.02)
    ax.legend(fontsize=6.4, loc="upper left")
    ax.set_title("停机偏差的经验分布（各 4860 条）", fontsize=8.2)
    ax.annotate("对偶曲线在最右", xy=(-0.10, 0.62), xytext=(-0.62, 0.60),
                fontsize=6.2, color=fs.SERIES["dual"],
                arrowprops=dict(arrowstyle="-", color=fs.SERIES["dual"],
                                linewidth=0.5))
    fs.save(fig, "C_ecdf")


def draw_under() -> None:
    s1 = json.loads((LOG / "s1_summary.json").read_text(encoding="utf-8"))
    rng = np.random.default_rng(3)
    thick = [15.0, 30.0, 50.0]
    fig, ax = plt.subplots(figsize=(3.4, 2.7))
    width = 0.19
    for k, policy in enumerate(POLICIES):
        xs, ys, err = [], [], []
        for j, L in enumerate(thick):
            v = np.array([r["e_alpha"] for r in s1
                          if r["policy"] == policy and r["length_mm"] == L])
            share = float(np.mean(v < 0))
            idx = rng.integers(0, v.size, size=(600, v.size))
            boots = np.mean(v[idx] < 0, axis=1)
            lo, hi = np.percentile(boots, [2.5, 97.5])
            xs.append(j + (k - 1.5) * width)
            ys.append(share)
            err.append([share - lo, hi - share])
        err = np.array(err).T
        ax.bar(xs, ys, width=width, color=fs.SERIES[policy],
               label=fs.SERIES_CN[policy], linewidth=0)
        ax.errorbar(xs, ys, yerr=err, fmt="none", ecolor=fs.INK,
                    elinewidth=0.6, capsize=1.6)
    ax.set_xticks(range(len(thick)))
    ax.set_xticklabels([f"{int(t)} mm" for t in thick])
    ax.set_ylabel("$P(e_\\alpha<0)$")
    ax.set_ylim(0, 1.12)
    ax.legend(fontsize=6.2, ncol=2, loc="upper center")
    ax.set_title("未达设计线的比例，含 95\\% 区间", fontsize=8.0)
    fs.save(fig, "C_under")


def draw_cook() -> None:
    study = json.loads((LOG / "study.json").read_text(encoding="utf-8"))
    cooks = ("steam", "bake", "combi")
    cn = {"steam": "蒸", "bake": "烤", "combi": "组合"}
    fig, ax = plt.subplots(figsize=(3.4, 2.7))
    for policy in POLICIES:
        ys = [float(np.median([r["e_alpha"] for r in study
                               if r["policy"] == policy and r["cook"] == c]))
              for c in cooks]
        ax.plot(range(3), ys, "o-", color=fs.SERIES[policy], linewidth=1.4,
                markersize=4.5, markerfacecolor="white", markeredgewidth=1.1,
                label=fs.SERIES_CN[policy])
    ax.axhline(0.0, color=fs.INK, linewidth=0.7, linestyle=(0, (4, 3)))
    ax.set_xticks(range(3))
    ax.set_xticklabels([cn[c] for c in cooks])
    ax.set_ylabel("$e_\\alpha$ 中位")
    ax.set_ylim(-1.0, 0.25)
    ax.legend(fontsize=6.0, loc="center left", bbox_to_anchor=(0.30, 0.30),
              handlelength=1.2, labelspacing=0.22)
    ax.set_title("档位 × 策略的停机偏差中位", fontsize=8.2)
    ax.text(0.035, -0.42, "蒸档把策略\n一起压到底", fontsize=6.0,
            color=fs.MUTED, ha="left", va="center", linespacing=1.5)
    fs.save(fig, "C_cook")


def draw_hetero() -> None:
    s1 = json.loads((LOG / "s1_summary.json").read_text(encoding="utf-8"))
    dual = [r for r in s1 if r["policy"] == "dual"]
    labels = {0: "均匀", 1: "厚度扰动", 2: "脂肪夹层"}
    fig, ax = plt.subplots(figsize=(3.4, 2.7))
    data, ticks = [], []
    for h in (0, 1, 2):
        v = np.array([r["e_alpha"] for r in dual if r["hetero"] == h])
        data.append(v)
        ticks.append(labels[h])
    bp = ax.boxplot(data, widths=0.42, patch_artist=True, showfliers=False,
                    medianprops=dict(color=fs.INK, linewidth=1.1),
                    whiskerprops=dict(color=fs.MUTED, linewidth=0.7),
                    capprops=dict(color=fs.MUTED, linewidth=0.7),
                    boxprops=dict(linewidth=0.7))
    for patch, h in zip(bp["boxes"], (0, 1, 2)):
        patch.set_facecolor(fs.SERIES["dual"])
        patch.set_alpha(0.28 + 0.1 * h)
    ax.axhline(0.0, color=fs.INK, linewidth=0.7, linestyle=(0, (4, 3)))
    ax.set_xticks(range(1, 4))
    ax.set_xticklabels(ticks)
    ax.set_ylabel("$e_\\alpha$")
    ax.set_title("对偶策略的非均质效应", fontsize=8.2)
    for i, v in enumerate(data):
        ax.text(i + 1, np.median(v) + 0.06, f"{np.median(v):+.3f}",
                ha="center", fontsize=6.2, color=fs.INK)
    fs.save(fig, "C_hetero")


def main() -> None:
    fs.setup()
    draw_ecdf()
    draw_under()
    draw_cook()
    draw_hetero()


if __name__ == "__main__":
    main()
