"""Cold-spot position uncertainty as a state, without leaving 1D (tier C).

The cross-check in tier A showed that the 1D lowest cell tracks the 2D cold spot
to 0.31 K, so the temperature reading is sound. What the 1D kernel genuinely
loses is *where* the cold spot is, and that matters for one decision: a probe
placed by a user. This script quantifies the position uncertainty that the
reported temperature does not carry.

    $env:PYTHONPATH="src"
    python scripts/run_coldspot_position.py

Writes ``results/logs/coldspot_position.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "results" / "logs"
sys.path.insert(0, str(ROOT / "src"))

from acts_mcdt.physics import K_BASE, RHO_C  # noqa: E402

ALPHA = K_BASE / RHO_C
DT = 2.0


def section(nx: int, nz: int, fat_col: int | None, minutes: float = 20.0) -> dict:
    """2D explicit section; returns the cold spot and its neighbourhood."""
    length, height = 0.030, 0.040
    dx, dz = length / nx, height / nz
    dt = min(DT, 0.4 * min(dx, dz) ** 2 / ALPHA)
    field_alpha = np.full((nz, nx), ALPHA)
    if fat_col is not None:
        field_alpha[:, fat_col] = 0.45 * ALPHA
    temp = np.full((nz, nx), 8.0)
    for _ in range(int(minutes * 60.0 / dt)):
        ddx = np.zeros_like(temp)
        ddx[:, 1:-1] = (temp[:, 2:] - 2 * temp[:, 1:-1] + temp[:, :-2]) / dx ** 2
        ddx[:, 0] = (temp[:, 1] - temp[:, 0]) / dx ** 2
        ddx[:, -1] = (temp[:, -2] - temp[:, -1]) / dx ** 2
        ddz = np.zeros_like(temp)
        ddz[1:-1, :] = (temp[2:, :] - 2 * temp[1:-1, :] + temp[:-2, :]) / dz ** 2
        flux = 25.0 * (140.0 - temp[:, 0]) + 4000.0
        nxt = temp + dt * field_alpha * (ddx + ddz)
        nxt[:, 0] = temp[:, 0] + dt * field_alpha[:, 0] * (
            (temp[:, 1] - temp[:, 0]) / dx ** 2 + flux / (K_BASE * dx))
        temp = np.clip(nxt, 0.0, 220.0)

    flat = temp.ravel()
    order = np.argsort(flat)
    # How many cells are within 0.5 K of the minimum: a direct measure of how
    # "flat" the cold region is, and therefore how uncertain its location is.
    near = int(np.sum(flat <= flat.min() + 0.5))
    cold = np.unravel_index(int(temp.argmin()), temp.shape)
    return {
        "nx": nx,
        "nz": nz,
        "fat_col": fat_col,
        "cold_row": int(cold[0]),
        "cold_col": int(cold[1]),
        "cold_c": round(float(temp.min()), 3),
        "cells_within_0p5K": near,
        "share_of_field_within_0p5K": round(near / flat.size, 4),
        "depth_from_face_mm": round(float(cold[1] * dx * 1000), 3),
        "spread_top10_c": round(float(flat[order[9]] - flat[order[0]]), 3),
    }


def main() -> None:
    rows = [
        section(24, 16, None),
        section(24, 16, 8),
        section(48, 32, None),
        section(48, 32, 16),
    ]
    for row in rows:
        print(f"  {row['nx']}x{row['nz']} fat={row['fat_col']} "
              f"cold=({row['cold_row']},{row['cold_col']}) "
              f"T={row['cold_c']:.3f} within0.5K={row['cells_within_0p5K']} "
              f"({row['share_of_field_within_0p5K']*100:.1f}% of field) "
              f"depth={row['depth_from_face_mm']:.2f} mm")

    base = rows[0]
    payload = {
        "kind": "cold-spot position uncertainty in a 2D section",
        "boundary": {"h_W_m2K": 25.0, "t_air_c": 140.0, "q_rad_W_m2": 4000.0},
        "rows": rows,
        "conclusion": (
            f"On the 24x16 grid {base['cells_within_0p5K']} cells sit within "
            f"0.5 K of the minimum ({base['share_of_field_within_0p5K']*100:.1f}% "
            "of the field), so the cold spot is a plateau, not a point. The "
            "reported single depth is one representative of that plateau, and "
            "a probe aimed at it has an uncertainty of the plateau width. This "
            "is why the paper scores the cold-spot temperature (which the 1D "
            "kernel reproduces to 0.31 K) and does not score a cold-spot "
            "position: the position is genuinely ill-determined on the "
            "temperature evidence alone."
        ),
    }
    LOG.mkdir(parents=True, exist_ok=True)
    (LOG / "coldspot_position.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {LOG / 'coldspot_position.json'}")


if __name__ == "__main__":
    main()
