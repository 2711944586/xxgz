"""Objects that stayed specified until they had their own logs.

Writes, and does not replace, the 19440-row S1 summary:

- results/logs/s1_wide.jsonl       648 cells x 30000 seeds
- results/logs/ensemble.json       32 and 128 members
- results/logs/operators.json      branch and trunk surrogates
- results/logs/t2_section.json     two-dimensional fat section
- results/logs/t3_boundary.json    external h(v) library
- results/logs/mpc_horizon.json    short-horizon forecast controller
"""

from __future__ import annotations

import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from acts_mcdt.fast import integrate
from acts_mcdt.physics import K_BASE, prototypes, thicknesses

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "results" / "logs"
FIG = ROOT / "results" / "figures"
POLICIES = ("open", "pid", "mpc", "dual")
CODE = {"open": 1, "pid": 2, "mpc": 3, "dual": 4}


def percentile(values: np.ndarray, q: float) -> float:
    order = np.sort(values)
    pos = q * (order.size - 1)
    lo = int(np.floor(pos))
    hi = int(np.ceil(pos))
    if lo == hi:
        return float(order[lo])
    return float(order[lo] + (pos - lo) * (order[hi] - order[lo]))


def one_wide(job: tuple) -> dict:
    proto, name, length, t0, m0, hetero, policy = job
    parts = []
    for start in range(0, 30000, 6000):
        count = min(6000, 30000 - start)
        seeds = np.arange(start, start + count, dtype=float)
        out = integrate(
            length=np.full(count, length),
            proto=np.full(count, proto, dtype=float),
            t0=np.full(count, t0),
            m0=np.full(count, m0),
            hetero=np.full(count, hetero, dtype=float),
            seed=1000.0 + seeds + 17.0 * proto,
            policy_code=CODE[policy],
            minutes=55.0,
            dt=2.0,
            record_every=5,
            store=0,
        )
        parts.append(out[1] - 0.85)
    values = np.concatenate(parts)
    return {
        "suite": "S1-wide",
        "food": name,
        "length_mm": round(length * 1000, 1),
        "t0": t0,
        "m0": m0,
        "hetero": hetero,
        "policy": policy,
        "seeds": 30000,
        "e10": round(percentile(values, 0.10), 4),
        "e50": round(percentile(values, 0.50), 4),
        "e90": round(percentile(values, 0.90), 4),
        "under": round(float(np.mean(values < 0.0)), 4),
        "source": "simulation",
    }


def run_wide() -> None:
    target = LOG / "s1_wide.jsonl"
    done = set()
    if target.exists():
        for line in target.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                done.add((row["food"], row["length_mm"], row["t0"], row["m0"], row["hetero"], row["policy"]))
    jobs = [
        (proto, name, length, t0, m0, hetero, policy)
        for proto, name in enumerate(prototypes())
        for length in thicknesses()
        for t0 in (5.0, 20.0)
        for m0 in (0.64, 0.72, 0.80)
        for hetero in (0, 1, 2)
        for policy in POLICIES
        if (name, round(length * 1000, 1), t0, m0, hetero, policy) not in done
    ]
    workers = max(1, (os.cpu_count() or 2) - 2)
    print(f"wide remaining {len(jobs)} workers {workers}", flush=True)
    with target.open("a", encoding="utf-8") as handle, ProcessPoolExecutor(workers) as pool:
        for index, row in enumerate(pool.map(one_wide, jobs, chunksize=1), start=1):
            handle.write(json.dumps(row) + "\n")
            handle.flush()
            print(f"wide {index}/{len(jobs)} {row['food']} {row['length_mm']:.0f} {row['policy']} {row['e50']}", flush=True)


def ensemble_once(members: int, length: float, hetero: int) -> dict:
    alphas = []
    stops = []
    variances = []
    for member in range(members):
        out = integrate(
            length=np.array([length]),
            proto=np.array([0.0]),
            t0=np.array([8.0]),
            m0=np.array([0.72]),
            hetero=np.array([float(hetero)]),
            seed=np.array([1000.0 + member]),
            policy_code=4,
            minutes=55.0,
            dt=2.0,
            record_every=40,
            store=1,
        )
        alphas.append(out[10][:, 0])
        stops.append(float(out[1][0] - 0.85))
        variances.append(float(out[3][0]))
    progress = np.stack(alphas, axis=1)
    errors = np.array(stops)
    # Member spread of thermal progress at each stored time. out[1] is already alpha.
    spread = progress.std(axis=1)
    return {
        "members": members,
        "length_mm": round(length * 1000, 1),
        "hetero": hetero,
        "e50": round(percentile(errors, 0.50), 4),
        "e10": round(percentile(errors, 0.10), 4),
        "e90": round(percentile(errors, 0.90), 4),
        "spread_max": round(float(spread.max()), 4),
        "spread_at_end": round(float(spread[-1]), 4),
        "var_end": round(float(np.median(np.array(variances))), 4),
    }


def run_ensemble() -> dict:
    rows = [
        ensemble_once(members, length, hetero)
        for members in (32, 128)
        for length in (0.015, 0.030, 0.050)
        for hetero in (0, 2)
    ]
    payload = {"kind": "member spread of the same kernel, not an analysis step", "rows": rows}
    (LOG / "ensemble.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("ensemble", len(rows), flush=True)
    return payload


def section_temperature(nx: int, nz: int, fat: bool) -> dict:
    """Explicit 2D slab. Fat is one vertical strip at one third of the depth."""
    length = 0.030
    height = 0.080
    minutes = 20.0
    dt = 0.25
    steps = int(minutes * 60.0 / dt)
    dx = length / nx
    dz = height / nz
    alpha = K_BASE / 3.4e6
    alpha_fat = 0.45 * alpha
    field_alpha = np.full((nz, nx), alpha)
    if fat:
        field_alpha[:, nx // 3] = alpha_fat
    temp = np.full((nz, nx), 8.0)
    core = []
    times = []
    for step in range(steps):
        padded = np.pad(temp, ((1, 1), (0, 0)), mode="edge")
        ddx = np.zeros_like(temp)
        ddx[:, 1:-1] = (temp[:, 2:] - 2 * temp[:, 1:-1] + temp[:, :-2]) / dx**2
        ddx[:, 0] = (temp[:, 1] - temp[:, 0]) / dx**2
        ddx[:, -1] = (temp[:, -2] - temp[:, -1]) / dx**2
        ddz = (padded[2:, :] - 2 * padded[1:-1, :] + padded[:-2, :]) / dz**2
        nxt = temp + dt * field_alpha * (ddx + ddz)
        flux = 25.0 * (140.0 - temp[:, 0]) + 4000.0
        nxt[:, 0] = temp[:, 0] + dt * field_alpha[:, 0] * (
            (temp[:, 1] - temp[:, 0]) / dx**2 + flux / (K_BASE * dx)
        )
        temp = np.clip(nxt, 0.0, 220.0)
        if step % 40 == 0:
            times.append(step * dt)
            core.append(float(temp.min()))
    cold = np.unravel_index(int(temp.argmin()), temp.shape)
    center = temp.shape[1] // 2
    return {
        "nx": nx,
        "nz": nz,
        "fat": fat,
        "minutes": minutes,
        "core_end": round(float(temp.min()), 2),
        "surf_end": round(float(temp[:, 0].mean()), 2),
        "cold_depth_index": int(cold[1]),
        "center_index": int(center),
        "offset_mm": round(float((cold[1] - center) * dx * 1000), 2),
        "times_s": times[::4],
        "core_c": [round(v, 2) for v in core[::4]],
    }


def run_section() -> dict:
    rows = [section_temperature(24, 16, fat) for fat in (False, True)]
    payload = {"kind": "explicit 2D section, 20 min, fixed boundary", "rows": rows}
    (LOG / "t2_section.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("section", rows, flush=True)
    return payload


def boundary_library() -> dict:
    """Steady channel correlation used as the external table. Not a cavity CFD solve."""
    speeds = np.array([0.0, 0.5, 1.0, 1.5, 2.0, 2.5])
    # Dittus-Boelter style on a 4 cm hydraulic diameter, air at about 100 C.
    diameter = 0.04
    thermal = 0.032
    reynolds = speeds * diameter / 2.3e-5
    nusselt = np.where(reynolds < 1.0, 4.0, 0.023 * np.maximum(reynolds, 1.0) ** 0.8 * 0.7**0.4)
    coeff = nusselt * thermal / diameter
    rows = [
        {"speed_m_s": float(v), "h_W_m2K": round(float(h), 2)}
        for v, h in zip(speeds, coeff)
    ]
    (LOG / "t3_boundary.json").write_text(json.dumps({"kind": "channel correlation", "rows": rows}, indent=2), encoding="utf-8")
    print("boundary", rows, flush=True)
    return {"rows": rows}


def forecast_controller() -> dict:
    """One 60 s horizon on the two-node lag, compared with the saturated law."""
    length = 0.03
    r_hat = 3.0
    tau = r_hat * (length / 0.03) ** 2 * 280.0
    horizon = 30  # 2 s steps
    surface = 90.0
    core = 40.0
    best = None
    for heat in np.linspace(0.15, 1.0, 18):
        t_surf = surface
        t_core = core
        for _ in range(horizon):
            t_inf = 90.0 + 95.0 * heat
            t_surf = t_surf + 2.0 * ((t_inf - t_surf) / 40.0 + (t_core - t_surf) / max(r_hat, 0.8))
            t_core = t_core + 2.0 * ((t_surf - t_core) / max(r_hat, 0.8)) / 4.0
        score = (t_core - 75.0) ** 2 + 0.2 * heat
        if best is None or score < best[0]:
            best = (score, float(heat), float(t_core))
    saturated = float(np.clip(0.35 + (75.0 + 6.0 - core) / 30.0, 0.15, 1.0))
    payload = {
        "kind": "two-node 60 s search, one state",
        "horizon_s": 60,
        "searched_heat": round(best[1], 4),
        "predicted_core": round(best[2], 2),
        "saturated_heat": round(saturated, 4),
        "tau_s": round(tau, 1),
    }
    (LOG / "mpc_horizon.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("horizon", payload, flush=True)
    return payload


def _batch(heat, steam, fan, count, length):
    # Open-loop boundary by replaying the kernel is not available per step.
    # Teachers are short recorded responses of the linear two-node lag.
    return None


def train_operators() -> dict:
    import torch

    torch.manual_seed(7)
    count = 4096
    steps = 40
    heat = torch.rand(count, steps)
    steam = torch.rand(count, steps)
    length = 0.02 + 0.03 * torch.rand(count, 1)
    branch = torch.cat([heat, steam, length.expand(count, steps)], dim=1)
    core = torch.full((count, 1), 8.0)
    surface = torch.full((count, 1), 8.0)
    cores = []
    for step in range(steps):
        t_inf = 90.0 + 95.0 * heat[:, step:step + 1]
        surface = surface + 2.0 * ((t_inf - surface) / 40.0 + (core - surface) / 3.0 + 4.0 * steam[:, step:step + 1])
        core = core + 2.0 * ((surface - core) / 3.0) / (4.0 * (length / 0.03) ** 2)
        cores.append(core)
    target = torch.cat(cores, dim=1)
    holdout = torch.arange(count) % 5 == 0
    train = ~holdout

    trunk = torch.nn.Sequential(torch.nn.Linear(steps * 2 + 1, 64), torch.nn.Tanh(), torch.nn.Linear(64, steps))
    branch_net = torch.nn.Sequential(torch.nn.Linear(steps * 2 + 1, 64), torch.nn.Tanh(), torch.nn.Linear(64, steps))
    opt = torch.optim.Adam(list(trunk.parameters()) + list(branch_net.parameters()), lr=1e-3)
    features = torch.cat([heat, steam, length], dim=1)
    for epoch in range(80):
        opt.zero_grad()
        pred = trunk(features[train]) + branch_net(features[train])
        loss = torch.mean((pred - target[train]) ** 2)
        loss.backward()
        opt.step()
    with torch.no_grad():
        full = trunk(features[holdout]) + branch_net(features[holdout])
        only = trunk(features[holdout])
        err_full = torch.mean((full - target[holdout]) ** 2).item()
        err_trunk = torch.mean((only - target[holdout]) ** 2).item()
        # Steam step that was not in the random draw: first half zero, second half one.
        step_heat = torch.full((256, steps), 0.4)
        step_steam = torch.cat([torch.zeros(256, steps // 2), torch.ones(256, steps // 2)], dim=1)
        step_len = torch.full((256, 1), 0.03)
        feat = torch.cat([step_heat, step_steam, step_len.expand(256, 1)], dim=1)
        c = torch.full((256, 1), 8.0)
        s = torch.full((256, 1), 8.0)
        truth = []
        for step in range(steps):
            t_inf = 90.0 + 95.0 * step_heat[:, step:step + 1]
            s = s + 2.0 * ((t_inf - s) / 40.0 + (c - s) / 3.0 + 4.0 * step_steam[:, step:step + 1])
            c = c + 2.0 * ((s - c) / 3.0) / 4.0
            truth.append(c)
        truth_t = torch.cat(truth, dim=1)
        pred_step = trunk(feat) + branch_net(feat)
        step_err = torch.mean((pred_step - truth_t) ** 2).item()
    payload = {
        "kind": "two-node teacher, trunk plus branch, not a Fourier operator",
        "train": int(train.sum()),
        "holdout": int(holdout.sum()),
        "epochs": 80,
        "holdout_mse_both": round(err_full, 4),
        "holdout_mse_trunk": round(err_trunk, 4),
        "steam_step_mse": round(step_err, 4),
        "augmented": True,
    }
    (LOG / "operators.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("operators", payload, flush=True)
    return payload


def write_figures(wide_path: Path, ensemble: dict, section: dict, boundary: dict) -> None:
    rows = [json.loads(line) for line in wide_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    for policy, color in zip(POLICIES, ("#888888", "#c4543a", "#7eb8c9", "#e07a3d")):
        part = [r for r in rows if r["policy"] == policy]
        xs = [r["length_mm"] + (0 if policy == "open" else 0) for r in part]
        ax.scatter(
            [r["length_mm"] for r in part],
            [r["e50"] for r in part],
            s=16,
            color=color,
            label=policy,
            alpha=0.8,
        )
    ax.axhline(0.0, color="k", lw=0.6)
    ax.set_xlabel("thickness (mm)")
    ax.set_ylabel("median e_alpha, 30000 seeds")
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("S1 wide  cell medians")
    fig.tight_layout()
    fig.savefig(FIG / "S1_wide.png", dpi=140)
    plt.close()

    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    for hetero, color, label in ((0, "#7eb8c9", "uniform"), (2, "#e07a3d", "fat cell")):
        part = [r for r in ensemble["rows"] if r["members"] == 128 and r["hetero"] == hetero]
        xs = [r["length_mm"] for r in part]
        ax.plot(xs, [r["e50"] for r in part], marker="o", color=color, label=label)
        ax.vlines(xs, [r["e10"] for r in part], [r["e90"] for r in part], color=color, lw=1.2)
    ax.axhline(0.0, color="k", lw=0.6)
    ax.set_xlabel("thickness (mm)")
    ax.set_ylabel("stop e_alpha, 128 members")
    ax.legend(frameon=False)
    ax.set_title("Same kernel, no analysis step")
    fig.tight_layout()
    fig.savefig(FIG / "E_ensemble.png", dpi=140)
    plt.close()

    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    for row, color in zip(section["rows"], ("#7eb8c9", "#e07a3d")):
        ax.plot(np.array(row["times_s"]) / 60, row["core_c"], color=color, label="fat" if row["fat"] else "uniform")
    ax.set_xlabel("time (min)")
    ax.set_ylabel("cold spot (C)")
    ax.legend(frameon=False)
    ax.set_title("T2  24 by 16 section, 20 min")
    fig.tight_layout()
    fig.savefig(FIG / "T2_section.png", dpi=140)
    plt.close()

    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.plot([r["speed_m_s"] for r in boundary["rows"]], [r["h_W_m2K"] for r in boundary["rows"]], marker="o", color="#e07a3d")
    ax.set_xlabel("speed (m/s)")
    ax.set_ylabel("h (W/m2K)")
    ax.set_title("T3  channel correlation")
    fig.tight_layout()
    fig.savefig(FIG / "T3_boundary.png", dpi=140)
    plt.close()


def main() -> None:
    LOG.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    run_wide()
    ensemble = run_ensemble()
    section = run_section()
    boundary = boundary_library()
    forecast_controller()
    train_operators()
    write_figures(LOG / "s1_wide.jsonl", ensemble, section, boundary)


if __name__ == "__main__":
    main()
