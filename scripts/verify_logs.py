"""Recompute logged cells and compare against results/logs.

Run from the repository root with ``src`` on PYTHONPATH:

    $env:PYTHONPATH="src"
    python scripts/verify_logs.py

Exit code 0 means every checked cell reproduces inside the stated tolerance.
The checks are deliberately small: a handful of cells per artifact, chosen to
pin the generation, not to re-run a campaign.
"""

from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from acts_mcdt.physics import DISPLAY, rollout  # noqa: E402

LOG = ROOT / "results" / "logs"

CHECKS = []


def check(name, got, want, tol):
    ok = abs(got - want) <= tol
    CHECKS.append((name, ok, got, want, tol))
    return ok


def main() -> int:
    # 1. S1 overall medians (baseline generation).
    log = json.loads((LOG / "s1_summary.json").read_text(encoding="utf-8"))
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
    seed = 1000.0 + a["seed"] + 17.0 * a["proto"]
    for policy in ("open", "pid", "mpc", "dual"):
        out = rollout(length=a["length"], proto=a["proto"], t0=a["t0"], m0=a["m0"],
                      hetero=a["hetero"], seed=seed, policy=policy, minutes=55.0,
                      store_history=False)
        want = st.median([r["e_alpha"] for r in log if r["policy"] == policy])
        check(f"S1 median e_alpha [{policy}]", st.median(out["e_alpha"]), want, 2e-4)

    # 2. seed-7 trace. This is the display generation: ch5.4 and the demo page
    #    both quote 1866 s / +0.145, and only the display kernel returns it.
    #    The baseline returns 1676 s / -0.095 for the same case; that difference
    #    is the generation split recorded in MANIFEST.json.
    out = rollout(length=np.array([0.03]), proto=np.array([0]), t0=np.array([8.0]),
                  m0=np.array([0.72]), hetero=np.array([0]), seed=np.array([7.0]),
                  policy="dual", minutes=55.0, store_history=False, **DISPLAY)
    check("seed 7 stop (display)", float(out["stop"][0]), 1866.0, 0.5)
    check("seed 7 e_alpha (display)", float(out["e_alpha"][0]), 0.145, 5e-3)
    check("seed 7 energy (display)", float(out["energy"][0]), 1864.0, 1.0)
    base = rollout(length=np.array([0.03]), proto=np.array([0]), t0=np.array([8.0]),
                   m0=np.array([0.72]), hetero=np.array([0]), seed=np.array([7.0]),
                   policy="dual", minutes=55.0, store_history=False)
    check("seed 7 stop (baseline, divergence guard)", float(base["stop"][0]), 1676.0, 0.5)

    # 3. S0 grid pairing.
    s0 = json.loads((LOG / "s0_summary.json").read_text(encoding="utf-8"))
    row = s0[0]
    proto = ("mince", "potato", "dough").index(row["food"])
    args = dict(length=np.array([0.030]), proto=np.array([proto]), t0=np.array([5.0]),
                m0=np.array([0.72]), hetero=np.array([0]), seed=np.array([1000 + row["seed"] + 17 * proto]),
                policy="dual", minutes=55.0, store_history=False)
    check("S0 e16", float(rollout(n=16, **args)["e_alpha"][0]), row["e16"], 1e-3)
    check("S0 e8", float(rollout(n=8, **args)["e_alpha"][0]), row["e8"], 1e-3)

    # 4. S2 probe contrast.
    s2 = json.loads((LOG / "s2_summary.json").read_text(encoding="utf-8"))
    seeds = 1000.0 + np.arange(40, dtype=float)
    for policy in ("dual", "mpc"):
        out = rollout(length=np.full(40, 0.030), proto=np.zeros(40), t0=np.full(40, 5.0),
                      m0=np.full(40, 0.72), hetero=np.zeros(40), seed=seeds,
                      policy=policy, minutes=55.0, store_history=False)
        want = st.median([r["e_alpha"] for r in s2
                          if r["factor"] == "probe" and r["level"] == policy])
        check(f"S2 probe [{policy}]", st.median(out["e_alpha"]), want, 1e-3)

    # 5. Display generation: study cell and demo frame.
    study = json.loads((LOG / "study.json").read_text(encoding="utf-8"))
    vals = []
    for t0 in (4.0, 8.0, 20.0):
        for m0 in (0.62, 0.72, 0.80):
            out = rollout(length=np.full(12, 0.030), proto=np.zeros(12),
                          t0=np.full(12, t0), m0=np.full(12, m0),
                          hetero=np.zeros(12), seed=np.arange(12, dtype=float),
                          policy="dual", cook="combi", minutes=55.0,
                          store_history=False, **DISPLAY)
            vals.extend(float(x) for x in out["e_alpha"])
    want = st.median([r["e_alpha"] for r in study
                      if r["policy"] == "dual" and r["cook"] == "combi"])
    check("study combi/dual median", st.median(vals), want, 2e-3)

    catalog = json.loads((ROOT / "demo" / "public" / "catalog.json").read_text(encoding="utf-8"))
    frame = [r for r in catalog if r["key"] == "dual_combi_30" and abs(r["time"] - 1680) < 1][0]
    out = rollout(length=np.array([0.03]), proto=np.array([0]), t0=np.array([8.0]),
                  m0=np.array([0.72]), hetero=np.array([0]), seed=np.array([7.0]),
                  policy="dual", minutes=55.0, record_every=4, **DISPLAY)
    j = int(1680 / 8)
    check("catalog t2 at 1680 s", float(out["t_core"][j, 0]), frame["t2"], 1e-3)
    check("catalog alpha at 1680 s", float(out["alpha_m"][j, 0]), frame["alpha"], 1e-4)

    width = max(len(name) for name, *_ in CHECKS)
    failed = 0
    for name, ok, got, want, tol in CHECKS:
        mark = "ok  " if ok else "FAIL"
        failed += 0 if ok else 1
        print(f"  [{mark}] {name:<{width}} got {got:+.6f} want {want:+.6f} tol {tol:g}")
    print(f"\n{len(CHECKS) - failed}/{len(CHECKS)} checks reproduced")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
