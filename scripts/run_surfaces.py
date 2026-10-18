"""Continuous response surfaces for the monograph figures.

The old campaign used 2-3 levels per factor, which is why every heatmap came
out as a 4x3 block of flat colour and every violin plot collapsed into a
thread: the data has almost no interior structure. A thickness sweep with 25
levels produced 24 distinct outcomes across a 1.0 range of ``e_alpha``; a
moisture sweep with 25 levels produced exactly one value, because the activity
saturates. The figures need the former and must stop plotting the latter.

This script produces the continuous surfaces the figures are drawn from:

    length x t0        for each policy        (the main response surface)
    length x moisture  for each policy        (shows the dead axis honestly)
    length x seed      for each policy        (shows how much of the spread is noise)
    length sweep       at dense resolution    (the 1D curves with CI bands)

Run with:

    $env:PYTHONPATH="src"
    python scripts/run_surfaces.py

Writes ``results/logs/surfaces.json``. Everything uses the baseline
generation, so the surfaces sit on the same kernel as the main tables.
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "results" / "logs"
sys.path.insert(0, str(ROOT / "src"))

from acts_mcdt.physics import BASELINE  # noqa: E402

POLICIES = ("open", "pid", "mpc", "dual")

# Grid definitions. 25 levels per axis is what the diagnostic showed is needed
# before the response stops looking like a staircase.
LENGTHS = np.round(np.linspace(0.010, 0.060, 26), 4)
TEMPS = np.round(np.linspace(2.0, 26.0, 25), 2)
MOISTURES = np.round(np.linspace(0.50, 0.88, 20), 3)
SEEDS_PER_CELL = 24


def _one(args):
    """One (policy, L, t0, m0) cell: run SEEDS_PER_CELL seeds, return quantiles."""
    policy, length, t0, m0 = args
    from acts_mcdt.physics import rollout

    n = SEEDS_PER_CELL
    out = rollout(
        length=np.full(n, length), proto=np.zeros(n), t0=np.full(n, t0),
        m0=np.full(n, m0), hetero=np.zeros(n),
        seed=1000.0 + np.arange(n, dtype=float),
        policy=policy, minutes=55.0, store_history=False, **BASELINE,
    )
    e = np.asarray(out["e_alpha"], dtype=float)
    return {
        "policy": policy,
        "length_mm": round(float(length) * 1000, 2),
        "t0": float(t0),
        "m0": float(m0),
        "e_p10": round(float(np.percentile(e, 10)), 4),
        "e_p50": round(float(np.median(e)), 4),
        "e_p90": round(float(np.percentile(e, 90)), 4),
        "e_mean": round(float(e.mean()), 4),
        "e_std": round(float(e.std()), 4),
        "stop_p50": round(float(np.median(out["stop"])), 1),
        "energy_p50": round(float(np.median(out["energy"])), 1),
    }


def run_grid(jobs, workers, label):
    rows = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for i, row in enumerate(pool.map(_one, jobs, chunksize=8), start=1):
            rows.append(row)
            if i % 200 == 0 or i == len(jobs):
                print(f"  {label}: {i}/{len(jobs)}", flush=True)
    return rows


def main() -> None:
    import os
    workers = max(1, (os.cpu_count() or 4) - 2)
    print(f"workers {workers}")

    # Surface 1: length x initial temperature (the main figure source).
    jobs_a = [(p, L, t, 0.72) for p in POLICIES for L in LENGTHS for t in TEMPS]
    print(f"surface length x t0: {len(jobs_a)} cells")
    rows_a = run_grid(jobs_a, workers, "Lxt")

    # Surface 2: length x moisture, to show the axis is dead.
    jobs_b = [(p, L, 8.0, m) for p in POLICIES for L in LENGTHS[::3] for m in MOISTURES]
    print(f"surface length x moisture: {len(jobs_b)} cells")
    rows_b = run_grid(jobs_b, workers, "Lxm")

    # Curve 3: dense 1D length sweep with spread, for CI bands.
    jobs_c = [(p, L, 8.0, 0.72) for p in POLICIES for L in LENGTHS]
    print(f"dense length curves: {len(jobs_c)} cells")
    rows_c = run_grid(jobs_c, workers, "L")

    payload = {
        "kind": "continuous response surfaces for the figures",
        "generation": "baseline",
        "seeds_per_cell": SEEDS_PER_CELL,
        "lengths_mm": [round(float(x) * 1000, 2) for x in LENGTHS],
        "temps_c": [float(x) for x in TEMPS],
        "moistures": [float(x) for x in MOISTURES],
        "policies": list(POLICIES),
        "surface_length_temp": rows_a,
        "surface_length_moisture": rows_b,
        "curves_length": rows_c,
    }
    LOG.mkdir(parents=True, exist_ok=True)
    (LOG / "surfaces.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    size = (LOG / "surfaces.json").stat().st_size / 1e6
    print(f"\nwrote {LOG / 'surfaces.json'} ({size:.2f} MB)")
    print(f"  L x T cells: {len(rows_a)}   L x m cells: {len(rows_b)}   "
          f"curves: {len(rows_c)}")


if __name__ == "__main__":
    main()
