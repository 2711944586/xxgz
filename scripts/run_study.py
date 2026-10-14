"""Factor study on the cavity-aware kernel. One row per finished case."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from acts_mcdt.physics import rollout

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "results" / "logs"
FIG = ROOT / "results" / "figures" / "study"
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False


def cases():
    foods = (0, 1, 2)
    lengths = (0.015, 0.030, 0.050)
    t0s = (4.0, 8.0, 20.0)
    m0s = (0.62, 0.72, 0.80)
    cooks = ("steam", "bake", "combi")
    policies = ("open", "pid", "mpc", "dual")
    seeds = range(12)
    out = []
    for food in foods:
        for length in lengths:
            for t0 in t0s:
                for m0 in m0s:
                    for cook in cooks:
                        for policy in policies:
                            for seed in seeds:
                                out.append((food, length, t0, m0, cook, policy, seed))
    return out


def run(batch):
    rows = []
    foods, lengths, t0s, m0s, cooks, policies, seeds = zip(*batch)
    for cook in ("steam", "bake", "combi"):
        for policy in ("open", "pid", "mpc", "dual"):
            mask = [(c == cook and p == policy) for c, p in zip(cooks, policies)]
            if not any(mask):
                continue
            idx = [i for i, flag in enumerate(mask) if flag]
            out = rollout(
                length=np.array([lengths[i] for i in idx]),
                proto=np.array([foods[i] for i in idx]),
                t0=np.array([t0s[i] for i in idx]),
                m0=np.array([m0s[i] for i in idx]),
                hetero=np.zeros(len(idx)),
                seed=np.array([seeds[i] for i in idx]),
                policy=policy,
                cook=cook,
                minutes=55.0,
                store_history=False,
            )
            names = ("mince", "potato", "dough")
            for j, i in enumerate(idx):
                rows.append({
                    "food": names[foods[i]],
                    "length_mm": int(lengths[i] * 1000),
                    "t0": t0s[i],
                    "m0": m0s[i],
                    "cook": cook,
                    "policy": policy,
                    "seed": int(seeds[i]),
                    "stop_s": round(float(out["stop"][j]), 1),
                    "e_alpha": round(float(out["e_alpha"][j]), 4),
                    "energy": round(float(out["energy"][j]), 1),
                    "var_r": round(float(out["final_var"][j]), 4),
                })
    return rows


def figures(rows):
    FIG.mkdir(parents=True, exist_ok=True)
    foods = ("mince", "potato", "dough")
    cooks = ("steam", "bake", "combi")
    policies = ("open", "pid", "mpc", "dual")
    # F1 cook x food, median e_alpha
    grid = np.zeros((3, 3))
    for i, food in enumerate(foods):
        for j, cook in enumerate(cooks):
            vals = [r["e_alpha"] for r in rows if r["food"] == food and r["cook"] == cook and r["policy"] == "dual"]
            grid[i, j] = float(np.median(vals))
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    im = ax.imshow(grid, cmap="cividis", vmin=-0.9, vmax=0.2)
    ax.set_xticks(range(3), ["蒸", "烤", "组合"])
    ax.set_yticks(range(3), ["肉糜", "土豆", "面团"])
    for i in range(3):
        for j in range(3):
            ax.text(j, i, f"{grid[i, j]:+.2f}", ha="center", va="center", color="white", fontsize=10)
    fig.colorbar(im, ax=ax, label="进度偏差中位数")
    fig.tight_layout()
    fig.savefig(FIG / "F1_mode_food.png", dpi=150)
    plt.close(fig)
    # F2 thickness
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    for cook, color in zip(cooks, ("#3d6b8a", "#c46b3a", "#6b7a45")):
        xs, ys = [], []
        for length in (15, 30, 50):
            vals = [r["e_alpha"] for r in rows if r["cook"] == cook and r["length_mm"] == length and r["policy"] == "dual"]
            xs.append(length)
            ys.append(float(np.median(vals)))
        ax.plot(xs, ys, marker="o", color=color, label={"steam": "蒸", "bake": "烤", "combi": "组合"}[cook])
    ax.axhline(0, color="#888", lw=0.8)
    ax.set_xlabel("厚度 / mm")
    ax.set_ylabel("进度偏差中位数")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "F2_thickness.png", dpi=150)
    plt.close(fig)
    # F3 policy energy
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    data = []
    for policy in policies:
        data.append([r["energy"] for r in rows if r["policy"] == policy and r["cook"] == "combi"])
    ax.boxplot(data, tick_labels=["开环", "腔温", "无探针", "对偶"], showfliers=False)
    ax.set_ylabel("累计加热")
    fig.tight_layout()
    fig.savefig(FIG / "F3_energy.png", dpi=150)
    plt.close(fig)
    # F4 variance by thickness under dual
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    for length, color in zip((15, 30, 50), ("#8a6a3d", "#3d6b8a", "#6b3d4a")):
        vals = [r["var_r"] for r in rows if r["policy"] == "dual" and r["length_mm"] == length]
        ax.hist(vals, bins=12, alpha=0.55, color=color, label=f"{length} mm")
    ax.set_xlabel("结束时热阻方差")
    ax.set_ylabel("条数")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "F4_variance.png", dpi=150)
    plt.close(fig)
    # F5 stop time vs thickness
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    for policy, color in zip(policies, ("#888", "#c46b3a", "#3d6b8a", "#6b7a45")):
        xs, ys = [], []
        for length in (15, 30, 50):
            vals = [r["stop_s"] / 60 for r in rows if r["policy"] == policy and r["length_mm"] == length and r["cook"] == "combi"]
            xs.append(length)
            ys.append(float(np.median(vals)))
        ax.plot(xs, ys, marker="o", color=color, label={"open": "开环", "pid": "腔温", "mpc": "无探针", "dual": "对偶"}[policy])
    ax.set_xlabel("厚度 / mm")
    ax.set_ylabel("停止时刻中位数 / min")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "F5_stop.png", dpi=150)
    plt.close(fig)
    # F6 initial moisture
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    for m0, color in zip((0.62, 0.72, 0.80), ("#c46b3a", "#3d6b8a", "#6b7a45")):
        vals = [r["e_alpha"] for r in rows if r["m0"] == m0 and r["policy"] == "dual" and r["cook"] == "combi"]
        ax.hist(vals, bins=16, alpha=0.5, color=color, label=f"含水 {m0}")
    ax.set_xlabel("进度偏差")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "F6_moisture.png", dpi=150)
    plt.close(fig)


def main():
    LOG.mkdir(parents=True, exist_ok=True)
    batch = cases()
    print("cases", len(batch), flush=True)
    rows = []
    step = 648
    for start in range(0, len(batch), step):
        rows.extend(run(batch[start:start + step]))
        print(start + len(batch[start:start + step]), flush=True)
    (LOG / "study.json").write_text(json.dumps(rows), encoding="utf-8")
    figures(rows)
    print("wrote", len(rows))


if __name__ == "__main__":
    main()
