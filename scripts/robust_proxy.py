"""Robustness of the campaign to the resistance-reference ceiling.

The probe acceptance test compares a candidate ``r`` against
``r_proxy = clip(gap/8 + 1.2 + 2.5*shell, R_MIN, R_MAX)``. The original code
used ``R_MAX = 8.0``, and because the raw expression spans 1.2-19.4 the ceiling
pinned 48.8% of the 30 mm dual run and 97.1% of the 50 mm dual run.

This script re-runs the campaign with the ceiling widened to 20.0 and reports
both the saturation drop and the change in every published statistic. The
point is a robustness claim, so it is written as a check rather than a new
campaign: if the numbers move, the paper has to be rebuilt; if they do not,
the report can say the reference was saturated and the conclusions survived
correcting it.

    $env:PYTHONPATH="src"
    python scripts/robust_proxy.py

Writes ``results/logs/proxy_robustness.json``.
"""

from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "results" / "logs"
sys.path.insert(0, str(ROOT / "src"))

from acts_mcdt.physics import DISPLAY, R_MAX, rollout  # noqa: E402

POLICIES = ("open", "pid", "mpc", "dual")


def s1_cases():
    cases = []
    for proto in range(3):
        for length in (0.015, 0.030, 0.050):
            for t0 in (5.0, 20.0):
                for m0 in (0.64, 0.72, 0.80):
                    for hetero in (0, 1, 2):
                        for seed in range(30):
                            cases.append((proto, length, t0, m0, hetero, seed))
    a = {k: np.array([c[i] for c in cases], dtype=float)
         for i, k in enumerate(["proto", "length", "t0", "m0", "hetero", "seed"])}
    return a, 1000.0 + a["seed"] + 17.0 * a["proto"]


def saturation_profile():
    """Share of steps at the ceiling, with the old and new boxes."""
    profile = {}
    for length in (0.015, 0.030, 0.050):
        for policy in ("open", "mpc", "dual"):
            out = rollout(length=np.array([length]), proto=np.array([0]),
                          t0=np.array([8.0]), m0=np.array([0.72]),
                          hetero=np.array([0]), seed=np.array([7.0]),
                          policy=policy, minutes=55.0, record_every=1, **DISPLAY)
            gap = np.maximum(out["t_surf"][:, 0] - out["t_core"][:, 0], 0.3)
            raw = gap / 8.0 + 1.2 + 2.5 * out["shell"][:, 0]
            profile[f"{int(length*1000)}mm_{policy}"] = {
                "raw_min": round(float(raw.min()), 3),
                "raw_max": round(float(raw.max()), 3),
                "share_at_8": round(float(np.mean(raw >= 8.0)), 4),
                "share_at_20": round(float(np.mean(raw >= R_MAX)), 4),
            }
    return profile


def main() -> None:
    s1 = json.loads((LOG / "s1_summary.json").read_text(encoding="utf-8"))
    a, seed = s1_cases()

    print("=== S1 reproduction with R_MAX = 20.0 ===")
    rows = []
    for policy in POLICIES:
        out = rollout(length=a["length"], proto=a["proto"], t0=a["t0"], m0=a["m0"],
                      hetero=a["hetero"], seed=seed, policy=policy, minutes=55.0,
                      store_history=False)
        log = np.array([r["e_alpha"] for r in s1 if r["policy"] == policy])
        logv = np.array([r["var_r"] for r in s1 if r["policy"] == policy])
        med_new = float(st.median(out["e_alpha"]))
        med_log = float(st.median(log))
        row = {
            "policy": policy,
            "n": int(log.size),
            "log_median_e": round(med_log, 4),
            "new_median_e": round(med_new, 4),
            "delta_median_e": round(med_new - med_log, 6),
            "log_median_var": round(float(np.median(logv)), 4),
            "new_median_var": round(float(np.median(out["final_var"])), 4),
            "max_abs_row_diff": round(float(np.max(np.abs(log - out["e_alpha"]))), 6),
        }
        rows.append(row)
        print(f"  {policy:5s} log {med_log:+.4f} new {med_new:+.4f} "
              f"delta {row['delta_median_e']:+.6f} | max row diff {row['max_abs_row_diff']:.6f}")

    profile = saturation_profile()
    print("\n=== saturation profile ===")
    for key, val in profile.items():
        print(f"  {key:12s} raw {val['raw_min']:6.2f}..{val['raw_max']:6.2f}  "
              f"at 8.0: {val['share_at_8']*100:5.1f}%   at 20.0: {val['share_at_20']*100:5.1f}%")

    unchanged = all(r["max_abs_row_diff"] < 1e-4 for r in rows)
    payload = {
        "kind": "robustness of the campaign to the resistance-reference ceiling",
        "old_ceiling": 8.0,
        "new_ceiling": R_MAX,
        "s1_rows": rows,
        "saturation_profile": profile,
        "verdict": (
            "The reference was saturated for up to 97% of the run under the old "
            "ceiling and 0% under the new one, yet every S1 row is unchanged to "
            "1e-4. The campaign conclusions are therefore robust to the ceiling, "
            "and the fix removes a real methodological defect without "
            "invalidating the reported numbers."
            if unchanged else
            "The ceiling changes the campaign; the reported tables must be rebuilt."
        ),
        "unchanged": unchanged,
    }
    (LOG / "proxy_robustness.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nunchanged: {unchanged}")
    print(f"wrote {LOG / 'proxy_robustness.json'}")


if __name__ == "__main__":
    main()
