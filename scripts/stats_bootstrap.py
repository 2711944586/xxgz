"""Bootstrap confidence intervals and pairwise policy contrasts.

The main tables report medians of 4860 samples with no uncertainty. This script
adds:

1. a percentile bootstrap CI on the median ``e_alpha`` per policy and per
   thickness;
2. a pairwise contrast table with a confidence interval on the difference and
   a Cliff's delta effect size.

    $env:PYTHONPATH="src"
    python scripts/stats_bootstrap.py

Writes ``results/logs/stats_bootstrap.json``. The numbers feed ch5's
statistics table; nothing here changes a point estimate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "results" / "logs"
sys.path.insert(0, str(ROOT / "src"))

S1 = json.loads((LOG / "s1_summary.json").read_text(encoding="utf-8"))
POLICIES = ("open", "pid", "mpc", "dual")
RNG = np.random.default_rng(20261018)
N_BOOT = 2000


def bootstrap_median(values: np.ndarray, n_boot: int = N_BOOT) -> tuple[float, float]:
    """Percentile bootstrap CI on the median."""
    idx = RNG.integers(0, values.size, size=(n_boot, values.size))
    meds = np.median(values[idx], axis=1)
    return float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))


def bootstrap_median_diff(a: np.ndarray, b: np.ndarray,
                          n_boot: int = N_BOOT) -> tuple[float, float, float]:
    """CI on median(a) - median(b), resampling each side independently.

    The two arrays are different rows (not paired observations), so the
    bootstrap resamples each independently and takes the difference of medians
    inside each replicate. Truncating one array to the other's length would
    align unrelated rows and is wrong.
    """
    idx_a = RNG.integers(0, a.size, size=(n_boot, a.size))
    idx_b = RNG.integers(0, b.size, size=(n_boot, b.size))
    diffs = np.median(a[idx_a], axis=1) - np.median(b[idx_b], axis=1)
    point = float(np.median(a) - np.median(b))
    return point, float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))


def cliffs_delta(a: np.ndarray, b: np.ndarray, cap: int = 2000) -> float:
    """P(a > b) - P(a < b), subsampled for cost."""
    a = a[:cap] if a.size > cap else a
    b = b[:cap] if b.size > cap else b
    gt = sum(float(np.mean(a_i > b)) for a_i in a) / a.size
    lt = sum(float(np.mean(a_i < b)) for a_i in a) / a.size
    return gt - lt


def by_policy(policy: str, length: float | None = None) -> np.ndarray:
    rows = [r for r in S1 if r["policy"] == policy
            and (length is None or r["length_mm"] == length)]
    return np.array([r["e_alpha"] for r in rows], dtype=float)


def main() -> None:
    table = []
    print("=== medians with 95% bootstrap CI ===")
    for policy in POLICIES:
        v = by_policy(policy)
        lo, hi = bootstrap_median(v)
        row = {
            "scope": "all",
            "policy": policy,
            "n": int(v.size),
            "median": round(float(np.median(v)), 4),
            "ci_lo": round(lo, 4),
            "ci_hi": round(hi, 4),
        }
        table.append(row)
        print(f"  all      {policy:5s} {row['median']:+.4f} "
              f"[{row['ci_lo']:+.4f}, {row['ci_hi']:+.4f}]")
    for length in (15.0, 30.0, 50.0):
        for policy in POLICIES:
            v = by_policy(policy, length)
            lo, hi = bootstrap_median(v)
            row = {
                "scope": f"{int(length)}mm",
                "policy": policy,
                "n": int(v.size),
                "median": round(float(np.median(v)), 4),
                "ci_lo": round(lo, 4),
                "ci_hi": round(hi, 4),
            }
            table.append(row)
            print(f"  {int(length):3d} mm  {policy:5s} {row['median']:+.4f} "
                  f"[{row['ci_lo']:+.4f}, {row['ci_hi']:+.4f}]")

    print("\n=== pairwise contrasts (all thicknesses) ===")
    contrasts = []
    pairs = [("dual", "mpc"), ("dual", "open"), ("dual", "pid"),
             ("mpc", "open"), ("mpc", "pid")]
    for a, b in pairs:
        va, vb = by_policy(a), by_policy(b)
        point, lo, hi = bootstrap_median_diff(va, vb)
        delta = cliffs_delta(va, vb)
        row = {
            "a": a,
            "b": b,
            "delta_median": round(point, 4),
            "ci_lo": round(lo, 4),
            "ci_hi": round(hi, 4),
            "cliffs_delta": round(float(delta), 4),
        }
        contrasts.append(row)
        print(f"  {a:5s} - {b:5s}  {row['delta_median']:+.4f} "
              f"[{row['ci_lo']:+.4f}, {row['ci_hi']:+.4f}]  "
              f"Cliff's delta {row['cliffs_delta']:+.3f}")

    payload = {
        "kind": "bootstrap uncertainty and pairwise contrasts for S1",
        "n_boot": N_BOOT,
        "seed": 20261018,
        "note": (
            "The medians are point estimates over 4860 rows per policy. The "
            "intervals are percentile bootstraps of the median. Cliff's delta "
            "is P(a>b)-P(a<b) on subsamples of 2000, so |delta|>0.47 is a large "
            "effect by the usual convention."
        ),
        "medians": table,
        "contrasts": contrasts,
    }
    (LOG / "stats_bootstrap.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {LOG / 'stats_bootstrap.json'}")


if __name__ == "__main__":
    main()
