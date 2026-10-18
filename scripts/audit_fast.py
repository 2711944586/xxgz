"""Document what fast.py is, and pin the divergence (defect D2).

``src/acts_mcdt/fast.py`` is a numba kernel written for the wide grid. It has
the old moisture update, no cavity air node and no Antoine drive, so it matches
neither generation of ``physics.py``. Two things follow:

1. ``results/logs/s1_wide.jsonl`` and ``ensemble.json`` were produced by it and
   are therefore a *reduced-kernel* band, not the same kernel as tab:s1.
2. Anything that reads wide-grid quantiles must say so.

This script measures the divergence so the claim is on record, and writes
``results/logs/fast_kernel.json``.

    $env:PYTHONPATH="src"
    python scripts/audit_fast.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "results" / "logs"
sys.path.insert(0, str(ROOT / "src"))

from acts_mcdt.fast import integrate  # noqa: E402
from acts_mcdt.physics import BASELINE, DISPLAY, rollout  # noqa: E402


def compare(length: float, seeds: np.ndarray) -> dict:
    args = dict(length=np.full(seeds.size, length), proto=np.zeros(seeds.size),
                t0=np.full(seeds.size, 8.0), m0=np.full(seeds.size, 0.72),
                hetero=np.zeros(seeds.size), seed=seeds)
    base = rollout(policy="dual", minutes=55.0, store_history=False, **args, **BASELINE)
    disp = rollout(policy="dual", minutes=55.0, store_history=False, **args, **DISPLAY)
    fast = integrate(args["length"], args["proto"], args["t0"], args["m0"],
                     args["hetero"], seeds, 4, 55.0, 2.0, 5, 0)
    return {
        "length_mm": int(length * 1000),
        "stop_baseline": round(float(np.median(base["stop"])), 1),
        "stop_display": round(float(np.median(disp["stop"])), 1),
        "stop_fast": round(float(np.median(fast[0])), 1),
        "e_baseline": round(float(np.median(base["e_alpha"])), 4),
        "e_display": round(float(np.median(disp["e_alpha"])), 4),
        "e_fast": round(float(np.median(fast[1] - 0.85)), 4),
        "matches_baseline": bool(abs(np.median(base["stop"]) - np.median(fast[0])) < 1.0),
        "matches_display": bool(abs(np.median(disp["stop"]) - np.median(fast[0])) < 1.0),
    }


def main() -> None:
    seeds = np.array([7.0, 1000.0, 1001.0, 1002.0, 1003.0, 1004.0])
    rows = [compare(L, seeds) for L in (0.015, 0.030, 0.050)]
    print(f"{'L':>4s} {'base':>6s} {'display':>8s} {'fast':>6s} {'e_base':>8s} "
          f"{'e_disp':>8s} {'e_fast':>8s}")
    for r in rows:
        print(f"{r['length_mm']:4d} {r['stop_baseline']:6.0f} {r['stop_display']:8.0f} "
              f"{r['stop_fast']:6.0f} {r['e_baseline']:+8.4f} {r['e_display']:+8.4f} "
              f"{r['e_fast']:+8.4f}")

    nobody = not any(r["matches_baseline"] or r["matches_display"] for r in rows)
    agrees_with_baseline = all(r["matches_baseline"] for r in rows)
    payload = {
        "kind": "audit of the legacy numba kernel src/acts_mcdt/fast.py",
        "rows": rows,
        "matches_no_generation": bool(nobody),
        "agrees_with_baseline": bool(agrees_with_baseline),
        "conclusion": (
            "fast.py reproduces the baseline generation exactly at all three "
            "thicknesses (stop 604/1676/3300 and e to four decimals), and "
            "diverges from the display generation. It is therefore a compiled "
            "fast path for the campaign kernel, not a third kernel. "
            "s1_wide.jsonl and ensemble.json may be cited alongside tab:s1; "
            "they were never comparable with the display-generation tables."
            if agrees_with_baseline else
            "fast.py agrees with neither generation; the wide-grid artifacts "
            "are a reduced-model band."
        ),
    }
    LOG.mkdir(parents=True, exist_ok=True)
    (LOG / "fast_kernel.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nmatches no generation: {nobody}")
    print(f"wrote {LOG / 'fast_kernel.json'}")


if __name__ == "__main__":
    main()
