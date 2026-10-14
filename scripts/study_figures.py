"""Extra figures from study.json. Run after run_study.py."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
rows = json.loads((ROOT / "results" / "logs" / "study.json").read_text(encoding="utf-8"))
FIG = ROOT / "results" / "figures" / "study"
FIG.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
cooks = ("steam", "bake", "combi")
cook_name = {"steam": "蒸", "bake": "烤", "combi": "组合"}
policies = ("open", "pid", "mpc", "dual")
policy_name = {"open": "开环", "pid": "腔温", "mpc": "无探针", "dual": "对偶"}
colors = ("#8a6a3d", "#c46b3a", "#3d6b8a", "#6b7a45")


def med(pred, key):
    vals = [r[key] for r in rows if pred(r)]
    return float(np.median(vals)) if vals else np.nan


# F7 heatmap policy x cook
grid = np.zeros((4, 3))
for i, policy in enumerate(policies):
    for j, cook in enumerate(cooks):
        grid[i, j] = med(lambda r, policy=policy, cook=cook: r["policy"] == policy and r["cook"] == cook, "e_alpha")
fig, ax = plt.subplots(figsize=(6.2, 4.4))
im = ax.imshow(grid, cmap="cividis", vmin=-0.9, vmax=0.15)
ax.set_xticks(range(3), [cook_name[c] for c in cooks])
ax.set_yticks(range(4), [policy_name[p] for p in policies])
for i in range(4):
    for j in range(3):
        ax.text(j, i, f"{grid[i, j]:+.2f}", ha="center", va="center", color="white")
fig.colorbar(im, ax=ax, label="进度偏差中位数")
fig.tight_layout()
fig.savefig(FIG / "F7_policy_cook.png", dpi=150)
plt.close(fig)

# F8 initial temperature
fig, ax = plt.subplots(figsize=(6.4, 4.0))
for t0, color in zip((4.0, 8.0, 20.0), colors[:3]):
    ys = [med(lambda r, t0=t0, L=L: r["t0"] == t0 and r["length_mm"] == L and r["policy"] == "dual" and r["cook"] == "combi", "e_alpha") for L in (15, 30, 50)]
    ax.plot([15, 30, 50], ys, marker="o", color=color, label=f"初温 {t0:.0f} °C")
ax.axhline(0, color="#888", lw=0.8)
ax.set_xlabel("厚度 / mm")
ax.set_ylabel("进度偏差中位数")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(FIG / "F8_t0.png", dpi=150)
plt.close(fig)

# F9 food small multiples of stop time
fig, axes = plt.subplots(1, 3, figsize=(9.2, 3.3), sharey=True)
for ax, food, title in zip(axes, ("mince", "potato", "dough"), ("肉糜", "土豆", "面团")):
    for policy, color in zip(policies, colors):
        ys = [med(lambda r, food=food, policy=policy, L=L: r["food"] == food and r["policy"] == policy and r["length_mm"] == L and r["cook"] == "combi", "stop_s") / 60 for L in (15, 30, 50)]
        ax.plot([15, 30, 50], ys, marker="o", color=color, label=policy_name[policy])
    ax.set_title(title)
    ax.set_xlabel("厚度 / mm")
axes[0].set_ylabel("停止 / min")
axes[2].legend(frameon=False, fontsize=8)
fig.tight_layout()
fig.savefig(FIG / "F9_food_stop.png", dpi=150)
plt.close(fig)

# F10 variance vs error
fig, ax = plt.subplots(figsize=(6.2, 4.2))
for cook, color in zip(cooks, ("#3d6b8a", "#c46b3a", "#6b7a45")):
    sub = [r for r in rows if r["cook"] == cook and r["policy"] == "dual"]
    ax.scatter([r["var_r"] for r in sub][::6], [r["e_alpha"] for r in sub][::6], s=10, alpha=0.45, color=color, label=cook_name[cook])
ax.set_xlabel("结束方差")
ax.set_ylabel("进度偏差")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(FIG / "F10_var_error.png", dpi=150)
plt.close(fig)

print("extra", len(rows))
