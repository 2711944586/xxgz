"""Draw the two ch5 distribution figures: C_under and C_cook.

This is the canonical producer for both files:

* ``C_under`` — 未达设计线比例。95% bootstrap 区间在这个尺寸上原本看不见，
  画成点＋区间而不是柱状图，区间才读得出来。
* ``C_cook`` — 档位与策略的交叉。图例原本压在曲线上，这里让出空间。

Historical note: the file was originally named ``fix_figs.py`` when it was a
one-off legibility patch; the two figures still ship in the paper, so it stays
as their only producer.
"""
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import figstyle as fs  # noqa: E402
import json  # noqa: E402

LOG = ROOT / "results" / "logs"
POLICIES = ("open", "pid", "mpc", "dual")
fs.setup()

# ---- C_under: dot with interval, readable -------------------------------
s1 = json.loads((LOG / "s1_summary.json").read_text(encoding="utf-8"))
rng = np.random.default_rng(11)
fig, ax = plt.subplots(figsize=(3.5, 2.8))
thick = [15.0, 30.0, 50.0]
for k, policy in enumerate(POLICIES):
    xs, ys, lo_e, hi_e = [], [], [], []
    for j, L in enumerate(thick):
        v = np.array([r["e_alpha"] for r in s1
                      if r["policy"] == policy and r["length_mm"] == L])
        if v.size == 0:
            continue
        share = float(np.mean(v < 0))
        idx = rng.integers(0, v.size, size=(800, v.size))
        boots = np.mean(v[idx] < 0, axis=1)
        lo, hi = np.percentile(boots, [2.5, 97.5])
        xs.append(j + (k - 1.5) * 0.16)
        ys.append(share)
        lo_e.append(share - lo)
        hi_e.append(hi - share)
    ax.plot(xs, ys, "-", color=fs.SERIES[policy], linewidth=0.9, alpha=0.45)
    ax.errorbar(xs, ys, yerr=[lo_e, hi_e], fmt="o", color=fs.SERIES[policy],
                markersize=5.5, capsize=0, elinewidth=2.4, label=fs.SERIES_CN[policy])
ax.set_xticks(range(len(thick)))
ax.set_xticklabels([f"{int(t)} mm" for t in thick])
ax.set_ylabel("$P(e_\\alpha<0)$")
ax.set_ylim(0, 1.12)
ax.legend(fontsize=6.2, ncol=2, loc="center left", bbox_to_anchor=(0.02, 0.42), framealpha=0.9)
ax.set_title("未达设计线的比例（竖线为 95% 区间）", fontsize=8.0)
fs.save(fig, "C_under")

# ---- C_cook: legend out of the plotting area ---------------------------
study = json.loads((LOG / "study.json").read_text(encoding="utf-8"))
cn = {"steam": "蒸", "bake": "烤", "combi": "组合"}
fig, ax = plt.subplots(figsize=(3.5, 2.8))
for policy in POLICIES:
    ys = [float(np.median([r["e_alpha"] for r in study
                           if r["policy"] == policy and r["cook"] == c]))
          for c in ("steam", "bake", "combi")]
    ax.plot(range(3), ys, "o-", color=fs.SERIES[policy], linewidth=1.5,
            markersize=5, markerfacecolor="white", markeredgewidth=1.3,
            label=fs.SERIES_CN[policy])
ax.axhline(0.0, color=fs.INK, linewidth=0.7, linestyle=(0, (4, 3)))
ax.set_xticks(range(3))
ax.set_xticklabels([cn[c] for c in ("steam", "bake", "combi")])
ax.set_ylabel("$e_\\alpha$ 中位")
ax.set_ylim(-1.02, 0.34)
ax.legend(fontsize=6.2, loc="upper left", bbox_to_anchor=(0.0, 1.0),
          handlelength=1.2, labelspacing=0.18)
ax.set_title("档位 × 策略的停机偏差中位", fontsize=8.2)
fs.save(fig, "C_cook")

print("C_under and C_cook redrawn")
