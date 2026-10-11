"""Run S0--S2 and write logs plus figures.

S1 grid: 3 foods x 3 thicknesses x 2 initial temperatures x 3 moistures
x 3 heterogeneity levels x 30 seeds, four policies inside each case.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from acts_mcdt.physics import prototypes, rollout, thicknesses
from acts_mcdt.propositions import cold_spot_bound, pulse_rank, shield_domain, steady_sensitivity

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "results" / "logs"
FIG = ROOT / "results" / "figures"
POLICIES = ("open", "pid", "mpc", "dual")


def design_s1(seeds: int = 30):
    rows = []
    case = 0
    for proto, name in enumerate(prototypes()):
        for length in thicknesses():
            for t0 in (5.0, 20.0):
                for m0 in (0.64, 0.72, 0.80):
                    for hetero in (0, 1, 2):
                        for seed in range(seeds):
                            rows.append((case, name, proto, length, t0, m0, hetero, seed))
                            case += 1
    return rows


def run_rows(rows, minutes=55.0):
    summary = []
    # Group by identical geometry so one batch shares a seed column.
    # Each row is independent because noise uses the seed array.
    chunk = 48
    for start in range(0, len(rows), chunk):
        part = rows[start:start + chunk]
        for policy in POLICIES:
            out = rollout(
                length=np.array([r[3] for r in part]),
                proto=np.array([r[2] for r in part]),
                t0=np.array([r[4] for r in part]),
                m0=np.array([r[5] for r in part]),
                hetero=np.array([r[6] for r in part]),
                seed=np.array([1000 + r[7] + 17 * r[2] for r in part]),
                policy=policy,
                minutes=minutes,
            )
            for i, row in enumerate(part):
                summary.append({
                    "suite": "S1",
                    "case": row[0],
                    "food": row[1],
                    "length_mm": round(row[3] * 1000, 1),
                    "t0": row[4],
                    "m0": row[5],
                    "hetero": row[6],
                    "seed": row[7],
                    "policy": policy,
                    "stop_s": round(float(out["stop"][i]), 1),
                    "e_alpha": round(float(out["e_alpha"][i]), 4),
                    "energy": round(float(out["energy"][i]), 1),
                    "var_r": round(float(out["final_var"][i]), 4),
                    "alpha_b": round(float(out["alpha_b"][-1, i]), 4),
                    "augmented": False,
                    "source": "simulation",
                })
        print(f"S1 {start + len(part)}/{len(rows)}", flush=True)
    return summary


def trace_one():
    out = {}
    for policy in POLICIES:
        out[policy] = rollout(
            length=np.array([0.03]),
            proto=np.array([0]),
            t0=np.array([8.0]),
            m0=np.array([0.72]),
            hetero=np.array([0]),
            seed=np.array([7]),
            policy=policy,
            minutes=55.0,
            record_every=4,
        )
    return out


def write_figures(summary, traces):
    FIG.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    tr = traces["dual"]
    ax.plot(tr["time"][:, 0] / 60, tr["t_surf"][:, 0], label="surface", color="#e07a3d")
    ax.plot(tr["time"][:, 0] / 60, tr["t_core"][:, 0], label="cold spot", color="#7eb8c9")
    ax.plot(tr["time"][:, 0] / 60, tr["t_hat"][:, 0], label="estimate", color="#d6c07a", ls="--")
    ax.set_xlabel("time (min)")
    ax.set_ylabel("temperature (C)")
    ax.legend(frameon=False)
    ax.set_title("D1  dual control, mince, 30 mm, seed 7")
    fig.tight_layout()
    fig.savefig(FIG / "D1_temperature.png", dpi=140)
    plt.close()

    foods = list(prototypes())
    policies = list(POLICIES)
    med = np.zeros((len(foods), len(policies)))
    for i, food in enumerate(foods):
        for j, policy in enumerate(policies):
            vals = [r["e_alpha"] for r in summary if r["food"] == food and r["policy"] == policy]
            med[i, j] = float(np.median(vals))
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    im = ax.imshow(med, cmap="coolwarm", vmin=-0.4, vmax=0.2)
    ax.set_xticks(range(4), policies)
    ax.set_yticks(range(3), foods)
    for i in range(3):
        for j in range(4):
            ax.text(j, i, f"{med[i, j]:.2f}", ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax, label="median e_alpha")
    ax.set_title("D25  cold-spot progress error at stop")
    fig.tight_layout()
    fig.savefig(FIG / "D25_e_alpha.png", dpi=140)
    plt.close()

    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    for policy, color in zip(policies, ("#888", "#c4543a", "#7eb8c9", "#e07a3d")):
        vals = [r["e_alpha"] for r in summary if r["policy"] == policy]
        ax.hist(vals, bins=30, histtype="step", density=True, label=policy, color=color, lw=1.6)
    ax.axvline(0.0, color="k", lw=0.6)
    ax.set_xlabel("e_alpha")
    ax.set_ylabel("density")
    ax.legend(frameon=False)
    ax.set_title("D10  progress error by policy")
    fig.tight_layout()
    fig.savefig(FIG / "D10_policy.png", dpi=140)
    plt.close()

    # Probe variance on the demo trace.
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.plot(tr["time"][:, 0] / 60, tr["var_r"][:, 0], color="#e07a3d")
    ax.set_xlabel("time (min)")
    ax.set_ylabel("Var(R)")
    ax.set_title("D6  resistance variance, dual, seed 7")
    fig.tight_layout()
    fig.savefig(FIG / "D6_variance.png", dpi=140)
    plt.close()


def aggregate(summary):
    out = {}
    for policy in POLICIES:
        vals = np.array([r["e_alpha"] for r in summary if r["policy"] == policy])
        out[policy] = {
            "n": int(vals.size),
            "median_e_alpha": round(float(np.median(vals)), 4),
            "frac_under": round(float(np.mean(vals < 0)), 4),
            "median_energy": round(float(np.median([r["energy"] for r in summary if r["policy"] == policy])), 1),
        }
    return out


def main():
    LOG.mkdir(parents=True, exist_ok=True)
    checks = {
        "steady": steady_sensitivity(),
        "pulse": pulse_rank(),
        "budget": cold_spot_bound(),
        "shield": shield_domain(),
    }
    # drop arrays
    checks["steady"] = {"spread": checks["steady"]["spread"], "passed": checks["steady"]["passed"]}
    checks["pulse"] = {"lag_p4": checks["pulse"]["lag_p4"], "lag_steam": checks["pulse"]["lag_steam"], "passed": checks["pulse"]["passed"]}
    checks["budget"] = {"bound": checks["budget"]["bound"], "realized": checks["budget"]["realized"], "passed": checks["budget"]["passed"]}
    (LOG / "propositions.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")

    rows = design_s1(30)
    summary = run_rows(rows)
    (LOG / "s1_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    stats = aggregate(summary)
    (LOG / "s1_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    traces = trace_one()
    demo = traces["dual"]
    cols = ["time", "t_surf", "t_core", "t_hat", "m_mean", "alpha_m", "var_r", "heat", "heat_req", "steam", "mode"]
    lines = [",".join(cols)]
    for i in range(demo["time"].shape[0]):
        lines.append(",".join(str(round(float(demo[c][i, 0]), 5)) for c in cols))
    (LOG / "demo_seed7_dual.csv").write_text("\n".join(lines), encoding="utf-8")
    write_figures(summary, traces)
    print(json.dumps(stats, indent=2))
    print("checks", checks)


if __name__ == "__main__":
    main()
