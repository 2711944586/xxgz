"""High-resolution campaign: continuous 3-D parameter surfaces.

Earlier campaigns used 2-3 levels per factor, which is why every heatmap came
out as a block and every violin collapsed. This campaign samples the response
surface densely enough that contour structure is resolved by the data rather
than by interpolation:

    length     41 levels  0.010-0.060 m
    t0         31 levels  2-26 degC
    policy      4
    seeds      48 per cell

plus, as separate sweeps:

    length x moisture   41 x 21   (to bound the dead axis properly)
    length x hetero     41 x 3
    length x cook       26 x 3
    deep seeds          120 seeds on 12 focal cells, for the distribution
                        figures that need a real spread

Total about 5.2e5 integrations. Written to results/logs/surface_xl.json.

    $env:PYTHONPATH="src"
    python scripts/run_surfaces_xl.py
"""
from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "results" / "logs"
sys.path.insert(0, str(ROOT / "src"))

POLICIES = ("open", "pid", "mpc", "dual")
LENGTHS = np.round(np.linspace(0.010, 0.060, 41), 5)
TEMPS = np.round(np.linspace(2.0, 26.0, 31), 3)
MOIST = np.round(np.linspace(0.50, 0.88, 21), 4)
HETERO = (0, 1, 2)
COOKS = ("steam", "bake", "combi")
SEEDS = 48
DEEP_SEEDS = 120


def q(v):
    v = np.asarray(v, dtype=float)
    return {
        "p05": round(float(np.percentile(v, 5)), 5),
        "p25": round(float(np.percentile(v, 25)), 5),
        "p50": round(float(np.median(v)), 5),
        "p75": round(float(np.percentile(v, 75)), 5),
        "p95": round(float(np.percentile(v, 95)), 5),
        "mean": round(float(v.mean()), 5),
        "std": round(float(v.std()), 5),
        "n": int(v.size),
    }


def cell(args):
    kind, policy, length, t0, m0, het, cook, nseed = args
    from acts_mcdt.physics import BASELINE, rollout

    n = int(nseed)
    out = rollout(
        length=np.full(n, length), proto=np.zeros(n), t0=np.full(n, t0),
        m0=np.full(n, m0), hetero=np.full(n, het),
        seed=1000.0 + 7919.0 * np.arange(n, dtype=float),
        policy=policy, cook=cook, minutes=55.0, store_history=False, **BASELINE,
    )
    e = out["e_alpha"]
    row = {
        "kind": kind, "policy": policy,
        "length_mm": round(float(length) * 1000, 2),
        "t0": float(t0), "m0": float(m0), "hetero": int(het), "cook": cook,
        "e": q(e),
        "stop": q(out["stop"]), "energy": q(out["energy"]),
        "final_var": q(out["final_var"]),
        "alpha_end": q(out["alpha_end"]),
        "alpha_at_stop": q(out["alpha_at_stop"]),
        "below": round(float(np.mean(np.asarray(e) < 0.0)), 4),
    }
    return row


def main() -> None:
    workers = max(1, (os.cpu_count() or 4) - 4)
    jobs = []

    # surface: length x t0
    for p in POLICIES:
        for L in LENGTHS:
            for t in TEMPS:
                jobs.append(("LT", p, L, t, 0.72, 0, "combi", SEEDS))

    # surface: length x moisture
    for p in POLICIES:
        for L in LENGTHS[::2]:
            for m in MOIST:
                jobs.append(("LM", p, L, 8.0, m, 0, "combi", SEEDS))

    # length x hetero
    for p in POLICIES:
        for L in LENGTHS:
            for h in HETERO:
                jobs.append(("LH", p, L, 8.0, 0.72, h, "combi", SEEDS))

    # length x cook
    for p in POLICIES:
        for L in LENGTHS[::2]:
            for c in COOKS:
                jobs.append(("LC", p, L, 8.0, 0.72, 0, c, SEEDS))

    # deep seeds on focal cells
    for p in POLICIES:
        for L in (0.015, 0.030, 0.050):
            for h in HETERO:
                jobs.append(("DEEP", p, L, 8.0, 0.72, h, "combi", DEEP_SEEDS))

    print(f"workers={workers} jobs={len(jobs)} "
          f"runs={sum(j[-1] for j in jobs):,}", flush=True)

    rows = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for i, row in enumerate(pool.map(cell, jobs, chunksize=4), 1):
            rows.append(row)
            if i % 500 == 0 or i == len(jobs):
                print(f"  {i}/{len(jobs)}", flush=True)

    LOG.mkdir(parents=True, exist_ok=True)
    payload = {
        "kind": "high-resolution continuous surfaces",
        "generation": "baseline",
        "seeds_per_cell": SEEDS,
        "deep_seeds": DEEP_SEEDS,
        "lengths_mm": [round(float(x) * 1000, 2) for x in LENGTHS],
        "temps_c": [float(x) for x in TEMPS],
        "moistures": [float(x) for x in MOIST],
        "policies": list(POLICIES),
        "cells": rows,
    }
    (LOG / "surface_xl.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    mb = (LOG / "surface_xl.json").stat().st_size / 1e6
    print(f"\nwrote surface_xl.json  {len(rows)} cells  "
          f"{sum(r['e']['n'] for r in rows):,} runs  {mb:.1f} MB")


if __name__ == "__main__":
    main()
