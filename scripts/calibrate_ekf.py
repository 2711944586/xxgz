"""Audit the kernel's resistance yardstick (defect D6).

The probe acceptance test in ``physics.rollout`` is

    r_proxy = clip(gap/8 + 1.2 + 2.5*shell, 0.8, 8.0)
    improved = |r_new - r_proxy| < |r_hat - r_proxy|

so the reference against which an update is judged is itself a clipped
quantity. This script measures how often the clip binds, and what the
unclipped quantity would be, on the same traces the monograph cites.

    $env:PYTHONPATH="src"
    python scripts/calibrate_ekf.py

Writes ``results/logs/proxy_audit.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "results" / "logs"
sys.path.insert(0, str(ROOT / "src"))

from acts_mcdt.physics import rollout, switches  # noqa: E402

GEN = switches("display")


def audit(length: float, policy: str, cook: str = "combi") -> dict:
    out = rollout(length=np.array([length]), proto=np.array([0]), t0=np.array([8.0]),
                  m0=np.array([0.72]), hetero=np.array([0]), seed=np.array([7.0]),
                  policy=policy, cook=cook, minutes=55.0, record_every=4, **GEN)
    gap = out["t_surf"][:, 0] - out["t_core"][:, 0]
    shell = out["shell"][:, 0]
    raw = gap / 8.0 + 1.2 + 2.5 * shell
    clipped = np.clip(raw, 0.8, 8.0)
    r_hat = out["r_hat"][:, 0]
    return {
        "length_mm": int(length * 1000),
        "policy": policy,
        "cook": cook,
        "gap_min_k": round(float(gap.min()), 2),
        "gap_max_k": round(float(gap.max()), 2),
        "gap_mean_k": round(float(gap.mean()), 2),
        "raw_min": round(float(raw.min()), 3),
        "raw_max": round(float(raw.max()), 3),
        "share_at_ceiling": round(float(np.mean(raw >= 8.0)), 4),
        "share_at_floor": round(float(np.mean(raw <= 0.8)), 4),
        "share_clipped": round(float(np.mean((raw >= 8.0) | (raw <= 0.8))), 4),
        "r_hat_min": round(float(r_hat.min()), 3),
        "r_hat_max": round(float(r_hat.max()), 3),
        "r_hat_at_prior_share": round(float(np.mean(np.abs(r_hat - 5.0) < 1e-6)), 4),
    }


def main() -> None:
    rows = []
    for length in (0.015, 0.030, 0.050):
        for policy in ("open", "mpc", "dual"):
            rows.append(audit(length, policy))
    for row in rows:
        print(f"{row['length_mm']:3d} mm {row['policy']:5s} "
              f"gap {row['gap_min_k']:6.1f}..{row['gap_max_k']:6.1f} K  "
              f"raw {row['raw_min']:6.2f}..{row['raw_max']:6.2f}  "
              f"clipped {row['share_clipped']*100:5.1f}%  "
              f"r_hat {row['r_hat_min']:.2f}..{row['r_hat_max']:.2f}")

    worst = max(rows, key=lambda r: r["share_clipped"])
    payload = {
        "kind": "audit of the probe acceptance reference r_proxy",
        "generation": "display",
        "definition": "r_proxy = clip(gap/8 + 1.2 + 2.5*shell, 0.8, 8.0)",
        "rows": rows,
        "worst_case": worst,
        "conclusion": (
            f"The clip binds on up to {worst['share_clipped']*100:.1f}% of steps "
            f"(30 mm {worst['policy']}). The acceptance test therefore compares a "
            "candidate update against a saturated constant for most of the run, "
            "which is not the same as comparing it against a measured "
            "resistance. Reported variance collapse (0.64 -> 0.224) is certified "
            "by that saturated yardstick and must be read with this caveat, or "
            "the proxy must be rescaled."
        ),
    }
    LOG.mkdir(parents=True, exist_ok=True)
    (LOG / "proxy_audit.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {LOG / 'proxy_audit.json'}")
    print("worst case:", worst["length_mm"], "mm", worst["policy"],
          f"{worst['share_clipped']*100:.1f}% clipped")


if __name__ == "__main__":
    main()
