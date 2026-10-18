"""Write the seed-7 combi trace the page is allowed to read."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from acts_mcdt.physics import rollout

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "demo" / "public"
LOG = ROOT / "results" / "logs"


def main() -> None:
    out = rollout(
        length=np.array([0.03]),
        proto=np.array([0]),
        t0=np.array([8.0]),
        m0=np.array([0.72]),
        hetero=np.array([0]),
        seed=np.array([7]),
        policy="dual",
        minutes=55.0,
        dt=2.0,
        record_every=4,
        cook="combi",
        generation="display",
    )
    n = out["time"].shape[0]
    cols = [
        "time", "t_surf", "t_core", "t_hat", "m_mean", "alpha_m",
        "r_hat", "var_r", "heat", "heat_req", "steam", "fan", "exhaust",
        "mode", "heater", "water", "cav_t", "cav_h", "cav_p", "shell",
        "vapor", "path_a", "path_b", "path_c",
    ]
    lines = [",".join(cols)]
    for i in range(n):
        lines.append(",".join(str(round(float(out[c][i, 0]), 5)) for c in cols))
    text = "\n".join(lines) + "\n"
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "seed7_combi.csv").write_text(text, encoding="utf-8")
    (LOG / "demo_seed7_dual.csv").write_text(text, encoding="utf-8")
    summary = {
        "stop_s": round(float(out["stop"][0]), 3),
        "e_alpha": round(float(out["e_alpha"][0]), 5),
        "energy": round(float(out["energy"][0]), 3),
        "path_a": round(float(out["path_a"].max()), 3),
        "path_b": round(float(out["path_b"].max()), 3),
        "path_c": round(float(out["path_c"].max()), 3),
        "probe_valid": bool(out["var_r"][-1, 0] < 0.64),
        "policy": "dual",
        "cook_mode": "combi",
    }
    parameters = {
        "seed": 7,
        "length_m": 0.03,
        "t0_c": 8.0,
        "m0": 0.72,
        "proto": "mince",
        "policy": "dual",
        "cook_mode": "combi",
        "dt_s": 2.0,
        "record_every": 4,
        "minutes": 55,
        "cells": 16,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT / "parameters.json").write_text(json.dumps(parameters, indent=2), encoding="utf-8")
    catalog = {}
    for policy in ("open", "pid", "mpc", "dual"):
        for cook in ("steam", "bake", "combi"):
            for length in (0.015, 0.03, 0.05):
                key = f"{policy}_{cook}_{int(length * 1000)}"
                catalog[key] = rollout(
                    length=np.array([length]),
                    proto=np.array([0]),
                    t0=np.array([8.0]),
                    m0=np.array([0.72]),
                    hetero=np.array([0]),
                    seed=np.array([7]),
                    policy=policy,
                    minutes=55.0,
                    dt=2.0,
                    record_every=4,
                    cook=cook,
                    generation="display",
                )
    frames = []
    for key, item in catalog.items():
        count = item["time"].shape[0]
        for i in range(count):
            frames.append({
                "key": key,
                "time": round(float(item["time"][i, 0]), 3),
                "t1": round(float(item["t_surf"][i, 0]), 4),
                "t2": round(float(item["t_core"][i, 0]), 4),
                "hat": round(float(item["t_hat"][i, 0]), 4),
                "m": round(float(item["m_mean"][i, 0]), 5),
                "alpha": round(float(item["alpha_m"][i, 0]), 5),
                "rHat": round(float(item["r_hat"][i, 0]), 4),
                "varR": round(float(item["var_r"][i, 0]), 4),
                "heat": round(float(item["heat"][i, 0]), 4),
                "heatReq": round(float(item["heat_req"][i, 0]), 4),
                "steam": round(float(item["steam"][i, 0]), 4),
                "fan": round(float(item["fan"][i, 0]), 4),
                "exhaust": round(float(item["exhaust"][i, 0]), 4),
                "mode": int(item["mode"][i, 0]),
                "heater": round(float(item["heater"][i, 0]), 3),
                "water": round(float(item["water"][i, 0]), 4),
                "cavT": round(float(item["cav_t"][i, 0]), 3),
                "cavH": round(float(item["cav_h"][i, 0]), 4),
                "shell": round(float(item["shell"][i, 0]), 4),
                "pathA": round(float(item["path_a"][i, 0]), 2),
                "pathB": round(float(item["path_b"][i, 0]), 2),
                "pathC": round(float(item["path_c"][i, 0]), 2),
            })
    (OUT / "catalog.json").write_text(json.dumps(frames), encoding="utf-8")
    print(f"rows {n} stop {summary['stop_s']} catalog {len(frames)}")


if __name__ == "__main__":
    main()
