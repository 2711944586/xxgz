"""S0 grid check and S2 boundary scan. Does not rewrite the 19440-row log.

S0 compares n=16 with n=8 on six cases of each food.
S2 uses 30 mm only: probe window, occlusion, mass channel, fat layer, one door opening.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from acts_mcdt.physics import prototypes, rollout

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "results" / "logs"
FIG = ROOT / "results" / "figures"


def _roll(count, **kwargs):
    base = dict(
        length=np.full(count, kwargs.pop("length", 0.030)),
        proto=np.full(count, kwargs.pop("proto", 0)),
        t0=np.full(count, kwargs.pop("t0", 5.0)),
        m0=np.full(count, kwargs.pop("m0", 0.72)),
        hetero=np.full(count, kwargs.pop("hetero", 0)),
        seed=kwargs.pop("seed"),
        policy=kwargs.pop("policy", "dual"),
        minutes=55.0,
        store_history=False,
    )
    base.update(kwargs)
    return rollout(**base)


def run_s0() -> list[dict]:
    rows = []
    for proto, name in enumerate(prototypes()):
        for seed in range(6):
            fine = _roll(1, proto=proto, seed=np.array([1000 + seed + 17 * proto]), n=16)
            coarse = _roll(1, proto=proto, seed=np.array([1000 + seed + 17 * proto]), n=8)
            rows.append({
                "suite": "S0",
                "food": name,
                "seed": seed,
                "e16": round(float(fine["e_alpha"][0]), 4),
                "e8": round(float(coarse["e_alpha"][0]), 4),
                "delta_e": round(float(coarse["e_alpha"][0] - fine["e_alpha"][0]), 4),
                "stop16": round(float(fine["stop"][0]), 1),
                "stop8": round(float(coarse["stop"][0]), 1),
                "source": "simulation",
            })
            print(f"S0 {name} {seed} {rows[-1]['delta_e']}", flush=True)
    return rows


def run_s2() -> list[dict]:
    rows = []
    seeds = np.arange(40)
    base_seed = 1000 + seeds

    def add(factor, level, **kwargs):
        out = _roll(40, seed=base_seed, **kwargs)
        for i in range(40):
            rows.append({
                "suite": "S2",
                "factor": factor,
                "level": level,
                "seed": int(seeds[i]),
                "e_alpha": round(float(out["e_alpha"][i]), 4),
                "stop_s": round(float(out["stop"][i]), 1),
                "var_r": round(float(out["final_var"][i]), 4),
                "t_std": round(float(out["t_std_stop"][i]), 4),
                "source": "simulation",
            })
        print(f"S2 {factor} {level}", flush=True)

    add("probe", "dual", policy="dual")
    add("probe", "mpc", policy="mpc")
    for seconds in (0.0, 15.0, 30.0, 60.0):
        add("occlude", str(int(seconds)), occlude_s=seconds)
    add("mass", "on", use_mass=True)
    add("mass", "off", use_mass=False)
    add("fat", "off", hetero=0)
    add("fat", "on", hetero=2)
    add("door", "closed")
    add("door", "at300", door_s=300.0)
    return rows


def _median(rows, **match):
    vals = [
        r["e_alpha"] for r in rows
        if all(r[key] == value for key, value in match.items())
    ]
    return float(np.median(vals))


def write_figures(s0, s2) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    foods = list(prototypes())
    for food, color in zip(foods, ("#e07a3d", "#7eb8c9", "#d6c07a")):
        part = [r for r in s0 if r["food"] == food]
        ax.scatter([r["seed"] for r in part], [r["delta_e"] for r in part], label=food, color=color)
    ax.axhline(0.0, color="k", lw=0.6)
    ax.set_xlabel("seed")
    ax.set_ylabel("e(n=8) - e(n=16)")
    ax.legend(frameon=False)
    ax.set_title("S0  grid halving, dual, 30 mm")
    fig.tight_layout()
    fig.savefig(FIG / "S0_grid.png", dpi=140)
    plt.close()

    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    levels = ["0", "15", "30", "60"]
    meds = [_median(s2, factor="occlude", level=level) for level in levels]
    ax.plot([0, 15, 30, 60], meds, marker="o", color="#e07a3d")
    ax.set_xlabel("occlusion (s)")
    ax.set_ylabel("median e_alpha")
    ax.set_title("D15  surface hold, dual, 30 mm, 40 seeds")
    fig.tight_layout()
    fig.savefig(FIG / "D15_occlusion.png", dpi=140)
    plt.close()

    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    names = ["mass on", "mass off", "fat off", "fat on", "door shut", "door 300 s"]
    keys = [
        ("mass", "on"), ("mass", "off"), ("fat", "off"), ("fat", "on"),
        ("door", "closed"), ("door", "at300"),
    ]
    vals = [_median(s2, factor=a, level=b) for a, b in keys]
    ax.bar(names, vals, color="#7eb8c9")
    ax.tick_params(axis="x", labelrotation=25)
    ax.set_ylabel("median e_alpha")
    ax.set_title("S2  channel and boundary, dual, 30 mm")
    fig.tight_layout()
    fig.savefig(FIG / "S2_factors.png", dpi=140)
    plt.close()


def main() -> None:
    LOG.mkdir(parents=True, exist_ok=True)
    s0 = run_s0()
    s2 = run_s2()
    (LOG / "s0_summary.json").write_text(json.dumps(s0, indent=2), encoding="utf-8")
    (LOG / "s2_summary.json").write_text(json.dumps(s2), encoding="utf-8")
    write_figures(s0, s2)
    delta = np.array([r["delta_e"] for r in s0])
    print("S0 median |delta|", round(float(np.median(np.abs(delta))), 4), "max", round(float(np.max(np.abs(delta))), 4))
    print("S2 rows", len(s2))


if __name__ == "__main__":
    main()
