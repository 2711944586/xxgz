"""Paired on/off for the Antoine surface term, plus nine stored traces."""

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


def pairs():
    rows = []
    for food in (0, 1, 2):
        for length in (0.015, 0.030, 0.050):
            for seed in range(12):
                for flag in (True, False):
                    out = rollout(
                        length=np.array([length]), proto=np.array([food]),
                        t0=np.array([8.0]), m0=np.array([0.72]), hetero=np.array([0]),
                        seed=np.array([seed]), policy="dual", cook="combi",
                        minutes=55.0, store_history=False, use_antoine=flag,
                    )
                    rows.append({
                        "food": ("mince", "potato", "dough")[food],
                        "length_mm": int(length * 1000),
                        "seed": seed,
                        "antoine": flag,
                        "e_alpha": round(float(out["e_alpha"][0]), 4),
                        "energy": round(float(out["energy"][0]), 1),
                        "stop_s": round(float(out["stop"][0]), 1),
                    })
    (LOG / "antoine_pairs.json").write_text(json.dumps(rows), encoding="utf-8")
    # difference by thickness
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    for length, color in zip((15, 30, 50), ("#8a6a3d", "#3d6b8a", "#c46b3a")):
        diff = []
        for seed in range(12):
            for food in ("mince", "potato", "dough"):
                a = next(r["e_alpha"] for r in rows if r["length_mm"] == length and r["seed"] == seed and r["food"] == food and r["antoine"])
                b = next(r["e_alpha"] for r in rows if r["length_mm"] == length and r["seed"] == seed and r["food"] == food and not r["antoine"])
                diff.append(a - b)
        ax.hist(diff, bins=10, alpha=0.55, color=color, label=f"{length} mm")
    ax.set_xlabel("打开 Antoine 项之后的进度偏差之差")
    ax.set_ylabel("配对数")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "F11_antoine.png", dpi=150)
    plt.close(fig)
    print("pairs", len(rows))


def traces():
    fig, axes = plt.subplots(3, 3, figsize=(9.4, 7.2), sharex=True)
    cooks = ("steam", "bake", "combi")
    names = {"steam": "蒸", "bake": "烤", "combi": "组合"}
    for col, cook in enumerate(cooks):
        for row, length in enumerate((0.015, 0.030, 0.050)):
            out = rollout(
                length=np.array([length]), proto=np.array([0]), t0=np.array([8.0]),
                m0=np.array([0.72]), hetero=np.array([0]), seed=np.array([7]),
                policy="dual", cook=cook, minutes=55.0, store_history=True,
            )
            t = out["time"][:, 0] / 60
            ax = axes[row, col]
            ax.plot(t, out["t_surf"][:, 0], color="#c46b3a", label="表面")
            ax.plot(t, out["t_core"][:, 0], color="#3d6b8a", label="冷点")
            ax.plot(t, out["t_hat"][:, 0], color="#6b7a45", ls="--", label="估计")
            ax.set_ylim(-20, 180)
            if row == 0:
                ax.set_title(names[cook])
            if col == 0:
                ax.set_ylabel(f"{int(length*1000)} mm")
            if row == 2 and col == 2:
                ax.legend(frameon=False, fontsize=7)
    fig.supxlabel("时间 / min")
    fig.tight_layout()
    fig.savefig(FIG / "F12_traces.png", dpi=150)
    plt.close(fig)

    out = rollout(
        length=np.array([0.03]), proto=np.array([0]), t0=np.array([8.0]),
        m0=np.array([0.72]), hetero=np.array([0]), seed=np.array([7]),
        policy="dual", cook="combi", minutes=55.0, store_history=True,
    )
    t = out["time"][:, 0] / 60
    fig, ax = plt.subplots(figsize=(6.6, 3.8))
    ax.plot(t, out["path_a"][:, 0], color="#3d6b8a", label="A")
    ax.plot(t, out["path_b"][:, 0], color="#c46b3a", label="B")
    ax.plot(t, out["path_c"][:, 0], color="#6b7a45", label="C")
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("路径项")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "F13_paths.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.6, 3.8))
    ax.plot(t, out["cav_t"][:, 0], color="#c46b3a", label="腔温")
    ax.set_ylabel("腔温 / °C", color="#c46b3a")
    ax2 = ax.twinx()
    ax2.plot(t, out["cav_h"][:, 0], color="#3d6b8a", label="腔湿")
    ax2.set_ylabel("腔湿", color="#3d6b8a")
    ax.set_xlabel("时间 / min")
    fig.tight_layout()
    fig.savefig(FIG / "F14_cavity.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.6, 3.8))
    ax.plot(t, out["heat_req"][:, 0], color="#8a6a3d", label="请求")
    ax.plot(t, out["heat"][:, 0], color="#c46b3a", label="进入边界")
    ax.plot(t, out["steam"][:, 0], color="#3d6b8a", label="蒸汽")
    ax.plot(t, out["exhaust"][:, 0], color="#6b7a45", label="排汽")
    ax.set_xlabel("时间 / min")
    ax.set_ylim(-0.05, 1.45)
    ax.legend(frameon=False, ncol=4)
    fig.tight_layout()
    fig.savefig(FIG / "F15_actuators.png", dpi=150)
    plt.close(fig)
    print("traces", len(t))


if __name__ == "__main__":
    pairs()
    traces()
