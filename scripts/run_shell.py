"""Shell-conductivity factor on the 30 mm combi dual cell."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from acts_mcdt.physics import rollout

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "results" / "figures" / "study"
rows = []
for factor in (0.0, 0.25, 0.55, 0.8):
    for seed in range(12):
        for length in (0.015, 0.03, 0.05):
            out = rollout(
                length=np.array([length]), proto=np.array([0]), t0=np.array([8.0]),
                m0=np.array([0.72]), hetero=np.array([0]), seed=np.array([seed]),
                policy="dual", cook="combi", minutes=55.0, store_history=False,
                shell_k=factor,
            )
            rows.append({
                "factor": factor, "seed": seed, "length_mm": int(length * 1000),
                "e_alpha": round(float(out["e_alpha"][0]), 4),
                "stop_s": round(float(out["stop"][0]), 1),
            })
(ROOT / "results" / "logs" / "shell_scan.json").write_text(json.dumps(rows), encoding="utf-8")
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
fig, ax = plt.subplots(figsize=(6.4, 4.0))
for length, color in zip((15, 30, 50), ("#8a6a3d", "#3d6b8a", "#c46b3a")):
    xs, ys = [], []
    for factor in (0.0, 0.25, 0.55, 0.8):
        vals = [r["e_alpha"] for r in rows if r["factor"] == factor and r["length_mm"] == length]
        xs.append(factor)
        ys.append(float(np.median(vals)))
    ax.plot(xs, ys, marker="o", color=color, label=f"{length} mm")
ax.set_xlabel("结壳导热削减系数")
ax.set_ylabel("进度偏差中位数")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(FIG / "F16_shell.png", dpi=150)
print(len(rows))
