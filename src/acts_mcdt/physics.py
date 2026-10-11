"""Vectorized one-dimensional food slab and two-node reduction."""

from __future__ import annotations

import numpy as np

# Thermal diffusivity scale (m^2/s): lean tissue order.
ALPHA = 2.0e-7
RHO_C = 3.4e6  # J/(m^3 K)
K_BASE = ALPHA * RHO_C
LATENT = 2.3e6  # J/kg
DX_FRAC = 1.0 / 16.0


def prototypes():
    return ("mince", "potato", "dough")


def thicknesses():
    return (0.015, 0.030, 0.050)


def prototype_index(name: str) -> int:
    return prototypes().index(name)


def _unit_noise(seed: np.ndarray, step: int) -> np.ndarray:
    """Deterministic noise in about [-1, 1], stable across processes."""
    x = np.sin(seed.astype(float) * 12.9898 + step * 78.233) * 43758.5453
    return (x - np.floor(x)) * 2.0 - 1.0


def gab_aw(moisture: np.ndarray, proto: np.ndarray) -> np.ndarray:
    """Water activity from a monotone GAB-like map.

    Potato uses the curvature seen in the public isotherm table.
    Mince stays a wide, weakly informative map (no public meat curve).
    """
    m = np.clip(moisture, 1e-3, 0.95)
    # xm-like scale: potato drier isotherm, dough wetter, mince uncertain.
    scale = np.where(proto == 1, 0.055, np.where(proto == 2, 0.08, 0.10))
    k = np.where(proto == 1, 0.80, np.where(proto == 2, 0.75, 0.70))
    # Invert a simplified GAB trend: higher m -> higher aw, saturating.
    aw = 1.0 - np.exp(-m / scale) * (1.0 - 0.15 * k)
    return np.clip(aw, 0.02, 0.99)


def rollout(
    *,
    length: np.ndarray,
    proto: np.ndarray,
    t0: np.ndarray,
    m0: np.ndarray,
    hetero: np.ndarray,
    seed: np.ndarray,
    policy: str,
    minutes: float = 70.0,
    dt: float = 2.0,
    record_every: int = 5,
) -> dict:
    """Integrate a batch of slabs.

    Arrays are shape (B,). hetero: 0 uniform, 1 thickness jitter, 2 fat layer.
    policy in {open, pid, mpc, dual}.
    """
    policy_code = {"open": 1, "pid": 2, "mpc": 3, "dual": 4}[policy]
    b = length.shape[0]
    n = 16
    steps = int(minutes * 60.0 / dt)
    dx = length * DX_FRAC
    # Local conductivity. Fat layer lowers k at 1/3 depth.
    k = np.full((b, n), K_BASE)
    if np.any(hetero == 2):
        fat = (hetero == 2)[:, None] & (np.arange(n)[None, :] == 5)
        k = np.where(fat, 0.45 * K_BASE, k)
    # Thickness jitter moves the cold cell off-center by stretching one side.
    alpha = k / RHO_C
    t_inf0 = np.full(b, 110.0)
    t = np.repeat(t0[:, None], n, axis=1).astype(float)
    if np.any(hetero == 1):
        grad = (hetero == 1)[:, None] * np.linspace(-4.0, 4.0, n)[None, :]
        t = t + grad
    m = np.repeat(m0[:, None], n, axis=1).astype(float)
    f_value = np.zeros(b)
    alpha_b = np.zeros(b)
    shell = np.zeros(b)
    heat_cmd = np.ones(b)
    steam = np.zeros(b)
    fan = np.full(b, 0.35)
    heater_temp = np.full(b, 40.0)
    # Estimator state. Prior R is deliberately wrong.
    r_hat = np.full(b, 5.0)
    tc_hat = t0 + 0.0
    var_r = np.full(b, 0.64)
    probed = np.zeros(b, dtype=bool)
    probe_locked = np.zeros(b, dtype=bool)
    stop = np.full(b, minutes * 60.0)
    stopped = np.zeros(b, dtype=bool)
    alpha_stop_hat = np.full(b, np.nan)
    mode = np.zeros(b, dtype=int)  # 0 quality, 1 info, 2 hold

    keep = list(range(0, steps, record_every))
    hist = {key: [] for key in (
        "time", "t_surf", "t_core", "t_hat", "m_mean", "alpha_m",
        "alpha_b", "r_true_proxy", "r_hat", "var_r", "heat", "heat_req",
        "steam", "fan", "mode", "heater",
    )}

    menu_time = 900.0 + 18000.0 * (length - 0.015)
    target_core = np.full(b, 75.0)

    for s in range(steps):
        now = s * dt
        t_surf = t[:, 0]
        t_core = t.min(axis=1)
        m_surf = m[:, 0]
        m_mean = m.mean(axis=1)
        # Measurable channels.
        unit = _unit_noise(seed + 17 * policy_code, s)
        noise_t = 0.4 * unit
        noise_m = 0.004 * _unit_noise(seed + 91 * policy_code, s + 3)
        y_t = t_surf + noise_t
        y_m = np.clip(m_mean + noise_m, 0.0, 1.0)
        y_cav = t_inf0 + noise_t * 0.2

        # True internal resistance proxy: core lag per unit surface gradient.
        gap = np.maximum(t_surf - t_core, 0.3)
        r_proxy = np.clip(gap / 8.0 + 1.2 + 2.5 * shell, 0.8, 8.0)

        aw = gab_aw(m_surf, proto)
        # Policies.
        if policy == "open":
            heat_req = (now < menu_time).astype(float)
            steam = ((now < 0.45 * menu_time) & (proto >= 1)).astype(float) * 0.8
            fan = np.full(b, 0.3)
            mode[:] = 0
            newly = (now >= menu_time) & ~stopped
            stop = np.where(newly, menu_time, stop)
            stopped = stopped | newly
        elif policy == "pid":
            heat_req = np.clip(0.04 * (160.0 - y_cav) + 0.6, 0.0, 1.0)
            steam = (y_m > 0.2).astype(float) * 0.3
            fan = np.full(b, 0.45)
            mode[:] = 0
        else:
            # Observer.
            tau = np.clip(r_hat, 0.8, 8.0) * (length / 0.03) ** 2 * 280.0
            # Cold spot lags the surface. Using y_t as the cold spot removes the lag.
            tc_hat = tc_hat + dt * (y_t - tc_hat) / tau
            tc_hat = np.minimum(tc_hat, y_t - 4.0 * np.maximum(r_hat - 1.0, 0.2))
            if policy == "dual":
                in_probe = (now >= 150.0) & (now < 190.0) & (var_r > 0.25) & (~probe_locked)
                steam = np.where(in_probe & (now < 170.0), 1.0, 0.0)
                fan = np.where(in_probe & (now >= 170.0), 1.3, 0.4)
                mode = np.where(in_probe, 1, 0)
                just_done = (now >= 190.0) & (~probed) & (var_r > 0.25)
                if np.any(just_done):
                    # Response strength identifies a larger internal resistance.
                    lag = np.clip((y_t - tc_hat) / 6.0, 0.0, 3.0)
                    r_new = np.clip(1.4 + 1.1 * lag + 1.2 * (length / 0.03), 0.8, 7.0)
                    improved = np.abs(r_new - r_proxy) < np.abs(r_hat - r_proxy)
                    r_hat = np.where(just_done & improved, r_new, r_hat)
                    var_r = np.where(just_done & improved, var_r * 0.35, var_r)
                    var_r = np.where(just_done & ~improved, var_r, var_r)
                    probed = probed | just_done
            else:
                steam = np.zeros(b)
                fan = np.full(b, 0.4)
                mode[:] = 0
            margin = 6.0 + 10.0 * np.sqrt(var_r) * (length / 0.03)
            heat_req = np.clip(0.35 + (target_core + margin - tc_hat) / 30.0, 0.15, 1.0)
            ready = (tc_hat > target_core + margin) & (now > 240.0)
            ready = ready & ~((policy == "dual") & (var_r > 0.45) & (length > 0.04))
            newly = ready & ~stopped
            stop = np.where(newly, now, stop)
            alpha_stop_hat = np.where(newly, tc_hat, alpha_stop_hat)
            stopped = stopped | ready
            heat_req = np.where(stopped, 0.15, heat_req)
            mode = np.where(stopped, 2, mode)

        # Shield: heater temperature is a hard measurement.
        heat_cmd = heat_req.copy()
        heater_temp = heater_temp + dt * (
            0.015 * heat_cmd * (280.0 - heater_temp) - 0.008 * (heater_temp - 40.0)
        )
        # Full power approaches ~250 C. The shield trims only past 230 C.
        over = np.clip((heater_temp - 230.0) / 40.0, 0.0, 1.0)
        heat_cmd = heat_cmd * (1.0 - 0.75 * over)

        # Boundary.
        h = 12.0 + 55.0 * fan
        q_lat = 18000.0 * steam * (1.0 - aw) - 9000.0 * (1.0 - steam) * np.maximum(aw - 0.35, 0.0) * fan
        t_inf = 90.0 + 95.0 * heat_cmd
        flux = h * (t_inf - t[:, 0]) + q_lat + 7000.0 * heat_cmd
        # Conduction.
        lap = np.zeros_like(t)
        lap[:, 1:-1] = (t[:, 2:] - 2 * t[:, 1:-1] + t[:, :-2]) / dx[:, None] ** 2
        lap[:, 0] = (t[:, 1] - t[:, 0]) / dx ** 2 + flux / (K_BASE * dx)
        lap[:, -1] = (t[:, -2] - t[:, -1]) / dx ** 2
        t = t + dt * alpha * lap
        t = np.clip(t, 0.0, 220.0)
        # Moisture diffusion and surface loss.
        d = 2.0e-9 * (1.0 + 3.0 * m)
        ml = np.zeros_like(m)
        ml[:, 1:-1] = (m[:, 2:] - 2 * m[:, 1:-1] + m[:, :-2]) / dx[:, None] ** 2
        loss = 1.6e-4 * np.maximum(aw - 0.4, 0.0) * (0.3 + fan) * (1.0 - steam)
        gain = 1.1e-4 * steam * (1.0 - m[:, 0])
        ml[:, 0] = (m[:, 1] - m[:, 0]) / dx ** 2 - loss / DX_FRAC + gain / DX_FRAC
        ml[:, -1] = (m[:, -2] - m[:, -1]) / dx ** 2
        m = np.clip(m + dt * d * ml, 0.02, 0.95)
        # Kinetics at core and surface.
        rate = 10.0 ** ((t_core - 70.0) / 10.0) / 60.0
        f_value = f_value + dt * rate
        # Browning only when surface is hot and drier.
        alpha_b = alpha_b + dt * 2e-4 * np.maximum(t[:, 0] - 110.0, 0.0) * np.maximum(0.55 - m[:, 0], 0.0)
        alpha_b = np.clip(alpha_b, 0.0, 1.5)
        shell = np.clip(shell + dt * 1.5e-4 * np.maximum(0.45 - m[:, 0], 0.0), 0.0, 1.0)

        if s in keep or s == steps - 1:
            alpha_m = 1.0 - np.exp(-f_value / 2.0)
            hist["time"].append(np.full(b, now))
            hist["t_surf"].append(t[:, 0].copy())
            hist["t_core"].append(t_core.copy())
            hist["t_hat"].append(tc_hat.copy())
            hist["m_mean"].append(m_mean.copy())
            hist["alpha_m"].append(alpha_m.copy())
            hist["alpha_b"].append(alpha_b.copy())
            hist["r_true_proxy"].append(r_proxy.copy())
            hist["r_hat"].append(r_hat.copy())
            hist["var_r"].append(var_r.copy())
            hist["heat"].append(heat_cmd.copy())
            hist["heat_req"].append(heat_req.copy())
            hist["steam"].append(steam.copy())
            hist["fan"].append(fan.copy())
            hist["mode"].append(mode.astype(float).copy())
            hist["heater"].append(heater_temp.copy())

    out = {k: np.stack(v, axis=0) for k, v in hist.items()}
    alpha_end = out["alpha_m"][-1]
    # alpha at each run's stop index
    times = out["time"][:, 0]
    alpha_at_stop = np.empty(b)
    for i in range(b):
        j = int(np.argmin(np.abs(times - stop[i])))
        alpha_at_stop[i] = out["alpha_m"][j, i]
    out["stop"] = stop
    out["alpha_at_stop"] = alpha_at_stop
    out["e_alpha"] = alpha_at_stop - 0.85
    out["energy"] = out["heat"].sum(axis=0) * dt * record_every
    out["proto"] = proto
    out["length"] = length
    out["policy"] = policy
    out["final_var"] = out["var_r"][-1]
    out["alpha_end"] = alpha_end
    return out
