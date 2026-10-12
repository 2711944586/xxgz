"""S1 with 30 000 seeds. Same kernel, summary only.

The 30-seed log stays at results/logs/s1_summary.json. This script writes
results/logs/s1_wide.jsonl, one factor cell per line.
"""

from __future__ import annotations

import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from acts_mcdt.physics import prototypes, rollout, thicknesses

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "results" / "logs"
POLICIES = ("open", "pid", "mpc", "dual")
SEEDS = 30000
CHUNK = 1500


def percentiles(values: np.ndarray) -> dict:
    order = np.sort(values)
    n = order.size

    def at(q: float) -> float:
        pos = q * (n - 1)
        lo = int(np.floor(pos))
        hi = int(np.ceil(pos))
        if lo == hi:
            return float(order[lo])
        return float(order[lo] + (pos - lo) * (order[hi] - order[lo]))

    return {
        "n": int(n),
        "e10": round(at(0.10), 4),
        "e50": round(at(0.50), 4),
        "e90": round(at(0.90), 4),
        "under": round(float(np.mean(values < 0.0)), 4),
    }


def one_cell(job: tuple) -> dict:
    proto, name, length, t0, m0, hetero, policy = job
    parts = []
    for start in range(0, SEEDS, CHUNK):
        count = min(CHUNK, SEEDS - start)
        seeds = np.arange(start, start + count)
        out = rollout(
            length=np.full(count, length),
            proto=np.full(count, proto),
            t0=np.full(count, t0),
            m0=np.full(count, m0),
            hetero=np.full(count, hetero),
            seed=1000 + seeds + 17 * proto,
            policy=policy,
            minutes=55.0,
            store_history=False,
        )
        parts.append(out["e_alpha"])
    stats = percentiles(np.concatenate(parts))
    stats.update({
        "suite": "S1-wide",
        "food": name,
        "length_mm": round(length * 1000, 1),
        "t0": t0,
        "m0": m0,
        "hetero": hetero,
        "policy": policy,
        "seeds": SEEDS,
        "source": "simulation",
    })
    return stats


def main() -> None:
    LOG.mkdir(parents=True, exist_ok=True)
    jobs = [
        (proto, name, length, t0, m0, hetero, policy)
        for proto, name in enumerate(prototypes())
        for length in thicknesses()
        for t0 in (5.0, 20.0)
        for m0 in (0.64, 0.72, 0.80)
        for hetero in (0, 1, 2)
        for policy in POLICIES
    ]
    target = LOG / "s1_wide.jsonl"
    workers = max(1, (os.cpu_count() or 2) - 1)
    done = 0
    with target.open("w", encoding="utf-8") as handle, ProcessPoolExecutor(workers) as pool:
        for stats in pool.map(one_cell, jobs, chunksize=1):
            handle.write(json.dumps(stats, ensure_ascii=False) + "\n")
            handle.flush()
            done += 1
            print(
                f"{done}/{len(jobs)} {stats['food']} {stats['length_mm']:.0f} "
                f"{stats['policy']} {stats['e50']}",
                flush=True,
            )
    print("wrote", target, "cells", done)


if __name__ == "__main__":
    main()
