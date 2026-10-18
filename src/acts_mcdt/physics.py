"""Vectorized one-dimensional food slab and two-node reduction.

The kernel carries two named switch sets, because the project ran two
generations of it and the monograph cites both:

``BASELINE``
    The campaign kernel. Produced ``results/logs/s1_summary.json``,
    ``s0_summary.json``, ``s2_summary.json``, ``s1_wide.jsonl``.
    Cavity air, water tank, door interlock, Antoine drive and crust feedback
    are all off; the steam valve stays shut outside the probe window.

``DISPLAY``
    The interaction-page kernel. Produced ``demo/public/catalog.json``,
    ``results/logs/study.json``, ``antoine_pairs.json``, ``shell_scan.json``,
    ``ensemble.json`` and ``tab:gridn``. Same integrator, crust feeds back
    into conductance, and the surface vapour-pressure drive is active.

Every log records which set produced it (``results/logs/MANIFEST.json``).
A new campaign must state its set; mixing them inside one table is the
defect this split exists to prevent.
"""

from __future__ import annotations

import numpy as np

# Thermal diffusivity scale (m^2/s): lean tissue order.
ALPHA = 2.0e-7
RHO_C = 3.4e6  # J/(m^3 K)
K_BASE = ALPHA * RHO_C
LATENT = 2.3e6  # J/kg
DX_FRAC = 1.0 / 16.0

# Named switch sets. Pass one with ``generation=`` or spell the switches out.
BASELINE = {
    "cavity_air": False,
    "use_antoine": False,
    "shell_k": 0.0,
    "moisture_bc": "gradient",
    "steam_baseline": 0.0,
}
DISPLAY = {
    "cavity_air": True,
    "use_antoine": True,
    "shell_k": 0.55,
    "moisture_bc": "flux",
    "steam_baseline": 0.15,
}
GENERATIONS = {"baseline": BASELINE, "display": DISPLAY}


def switches(generation: str = "baseline", **overrides) -> dict:
    """Return one named switch set, with optional per-key overrides."""
    if generation not in GENERATIONS:
        raise ValueError(f"unknown generation {generation!r}")
    out = dict(GENERATIONS[generation])
    out.update(overrides)
    return out


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
    store_history: bool = True,
    cook: str = "combi",
    n: int = 16,
    noise_scale: float = 1.0,
    occlude_s: float = 0.0,
    use_mass: bool = True,
    door_s: float | None = None,
    # --- physics switches ---------------------------------------------------
    # Pass ``generation="display"`` (or spell the switches out) for the
    # interaction-page kernel. The defaults are the campaign baseline, which is
    # what results/logs/s1_summary.json and the main tables were produced with.
    # Each switch changes the trajectory, so every campaign must record its set
    # in results/logs/MANIFEST.json.
    generation: str | None = None,
    cavity_air: bool = False,
    use_antoine: bool = False,
    shell_k: float = 0.0,
    moisture_bc: str = "gradient",
    steam_baseline: float = 0.0,
) -> dict:
    """Integrate a batch of slabs.

    Arrays are shape (B,). hetero: 0 uniform, 1 thickness jitter, 2 fat layer.
    policy in {open, pid, mpc, dual}.

    Switch meanings, all off at the baseline:

    ``cavity_air``
        Integrate the cavity air node, the water tank, the door interlock and
        the residual-current proxy, and let them overwrite the commands. The
        interaction page needs these channels; the campaign does not.
    ``use_antoine``
        Add the surface vapour-pressure drive ``p_cav - a_w p_food`` to the
        latent flux. Its sign flips with thickness, which is a result in its
        own right and must be turned on explicitly.
    ``shell_k``
        Multiply the surface conductance by ``1 - shell_k * shell`` so that
        crust raises the surface resistance. Zero keeps the crust a display
        variable only.
    ``moisture_bc``
        ``"gradient"`` is the baseline surface moisture update. ``"flux"``
        divides loss and gain by the cell fraction, which is what the
        interaction-page export was built on.
    ``steam_baseline``
        The steam command outside the probe window. The baseline holds the
        valve shut, which is what s1_summary.json was produced with.
    """
    if generation is not None:
        if generation not in GENERATIONS:
            raise ValueError(f"unknown generation {generation!r}")
        preset = GENERATIONS[generation]
        cavity_air = preset["cavity_air"]
        use_antoine = preset["use_antoine"]
        shell_k = preset["shell_k"]
        moisture_bc = preset["moisture_bc"]
        steam_baseline = preset["steam_baseline"]
    if moisture_bc not in ("gradient", "flux"):
        raise ValueError("moisture_bc must be 'gradient' or 'flux'")
    policy_code = {"open": 1, "pid": 2, "mpc": 3, "dual": 4}[policy]
    b = length.shape[0]
    if n < 2:
        raise ValueError("n must be at least 2")
    steps = int(minutes * 60.0 / dt)
    dx_frac = 1.0 / n
    dx = length * dx_frac
    # Local conductivity. Fat layer lowers k at 1/3 depth.
    # n=16 keeps the historical index 5. Other grids use the same depth fraction.
    fat_index = 5 if n == 16 else int(round((n - 1) / 3.0))
    k = np.full((b, n), K_BASE)
    if np.any(hetero == 2):
        fat = (hetero == 2)[:, None] & (np.arange(n)[None, :] == fat_index)
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
    exhaust = np.full(b, 0.4)
    heater_temp = np.full(b, 40.0)
    # Cavity. Product modes: 0 steam, 1 bake, 2 combi.
    cook_mode = np.full(b, {"steam": 0, "bake": 1, "combi": 2}[cook], dtype=int)
    water = np.full(b, 0.8)
    cav_t = np.full(b, 25.0)
    cav_h = np.full(b, 0.4)
    cav_p = np.full(b, 1.0)
    door = np.zeros(b)
    leak = np.zeros(b)
    # Estimator state. Prior R is deliberately wrong.
    r_hat = np.full(b, 5.0)
    tc_hat = t0 + 0.0
    var_r = np.full(b, 0.64)
    probed = np.zeros(b, dtype=bool)
    probe_locked = np.zeros(b, dtype=bool)
    stop = np.full(b, minutes * 60.0)
    stopped = np.zeros(b, dtype=bool)
    rec_time = []
    rec_alpha = []
    mode = np.zeros(b, dtype=int)  # 0 quality, 1 info, 2 hold

    keep = list(range(0, steps, record_every)) if store_history else []
    hist = {key: [] for key in (
        "time", "t_surf", "t_core", "t_hat", "m_mean", "alpha_m",
        "alpha_b", "r_true_proxy", "r_hat", "var_r", "heat", "heat_req",
        "steam", "fan", "exhaust", "mode", "heater",
        "cook_mode", "water", "cav_t", "cav_h", "cav_p", "door", "leak",
        "vapor", "shell", "path_a", "path_b", "path_c", "r_field",
    )}
    energy_acc = np.zeros(b)
    snap_std = np.full(b, np.nan)
    snap_cold = np.full(b, np.nan)
    held_y = t0 + 0.0

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
        noise_t = 0.4 * unit * noise_scale
        noise_m = 0.004 * _unit_noise(seed + 91 * policy_code, s + 3) * noise_scale
        y_t = t_surf + noise_t
        if now < occlude_s:
            y_t = held_y
        else:
            held_y = y_t
        y_m = np.clip(m_mean + noise_m, 0.0, 1.0)
        if not use_mass:
            y_m = np.zeros(b)
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
            exhaust = np.full(b, 0.35)
            newly = (now >= menu_time) & ~stopped
            stop = np.where(newly, menu_time, stop)
            if np.any(newly):
                snap_std = np.where(newly, t.std(axis=1), snap_std)
                snap_cold = np.where(newly, t.argmin(axis=1).astype(float), snap_cold)
            stopped = stopped | newly
        elif policy == "pid":
            heat_req = np.clip(0.04 * (160.0 - y_cav) + 0.6, 0.0, 1.0)
            steam = (y_m > 0.2).astype(float) * 0.3 if use_mass else np.zeros(b)
            fan = np.full(b, 0.45)
            exhaust = np.full(b, 0.5)
            mode[:] = 0
        else:
            # Observer.
            tau = np.clip(r_hat, 0.8, 8.0) * (length / 0.03) ** 2 * 280.0
            # Cold spot lags the surface. Using y_t as the cold spot removes the lag.
            tc_hat = tc_hat + dt * (y_t - tc_hat) / tau
            tc_hat = np.minimum(tc_hat, y_t - 4.0 * np.maximum(r_hat - 1.0, 0.2))
            if policy == "dual":
                in_probe = (now >= 150.0) & (now < 190.0) & (var_r > 0.25) & (~probe_locked)
                steam = np.where(in_probe & (now < 170.0), 1.0, steam_baseline)
                fan = np.where(in_probe & (now >= 170.0), 1.3, 0.4)
                exhaust = np.where(in_probe & (now < 170.0), 0.05, 0.55)
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
                exhaust = np.full(b, 0.7)
                mode[:] = 0
            margin = 6.0 + 10.0 * np.sqrt(var_r) * (length / 0.03)
            heat_req = np.clip(0.35 + (target_core + margin - tc_hat) / 30.0, 0.15, 1.0)
            ready = (tc_hat > target_core + margin) & (now > 240.0)
            ready = ready & ~((policy == "dual") & (var_r > 0.45) & (length > 0.04))
            newly = ready & ~stopped
            stop = np.where(newly, now, stop)
            if np.any(newly):
                snap_std = np.where(newly, t.std(axis=1), snap_std)
                snap_cold = np.where(newly, t.argmin(axis=1).astype(float), snap_cold)
            stopped = stopped | ready
            heat_req = np.where(stopped, 0.15, heat_req)
            mode = np.where(stopped, 2, mode)

        # Cavity. Product mode selects which actuators may move. The mode
        # restriction belongs to the process, not to the cavity-air switch:
        # the cook-mode study reads it, so it stays unconditional.
        # 0 steam: no dry heat. 1 bake: no steam. 2 combi: all four.
        steam = np.where(cook_mode == 1, 0.0, steam)
        heat_req = np.where(cook_mode == 0, np.minimum(heat_req, 0.25), heat_req)
        exhaust = np.clip(exhaust, 0.0, 1.0)
        # Shield: heater temperature is a hard measurement.
        heat_cmd = heat_req.copy()
        heater_temp = heater_temp + dt * (
            0.015 * heat_cmd * (280.0 - heater_temp) - 0.008 * (heater_temp - 40.0)
        )
        # Full power approaches ~250 C. The shield trims only past 230 C.
        over = np.clip((heater_temp - 230.0) / 40.0, 0.0, 1.0)
        heat_cmd = heat_cmd * (1.0 - 0.75 * over)
        if cavity_air:
            # Hard measurements. Quality estimates never enter these four lines.
            if door_s is not None and now >= door_s:
                door[:] = 1.0
            water = np.clip(water - dt * 1.2e-4 * steam, 0.0, 1.0)
            dry_tank = water < 0.05
            door_open = door > 0.5
            leak = np.where((heater_temp > 200.0) & (cav_h > 0.85), 0.004, 0.0)
            leak_trip = leak > 0.003
            blocked = dry_tank | door_open | leak_trip | (heater_temp >= 250.0)
            heat_cmd = np.where(blocked, 0.0, heat_cmd)
            steam = np.where(blocked, 0.0, steam)
            # Cavity air. Exhaust lowers humidity; steam raises it.
            cav_t = cav_t + dt * (
                0.02 * heat_cmd * (heater_temp - cav_t) - 0.01 * exhaust * (cav_t - 25.0)
            )
            cav_h = np.clip(
                cav_h + dt * (0.015 * steam - 0.02 * exhaust * cav_h - 0.05 * door),
                0.05, 0.98,
            )
            cav_p = 1.0 + 0.04 * cav_h + 0.0004 * np.maximum(cav_t - 100.0, 0.0)
        if (s % record_every == 0) or (s == steps - 1):
            energy_acc += heat_cmd

        h = 12.0 + 55.0 * fan
        q_lat = 18000.0 * steam * (1.0 - aw) - 9000.0 * (1.0 - steam) * np.maximum(aw - 0.35, 0.0) * fan
        if use_antoine:
            # Surface vapour-pressure drive. Antoine coefficients for water,
            # T in C, P in bar: log10(P) = 5.1962 - 1730.63/(T + 233.426).
            p_food = 10.0 ** (5.1962 - 1730.63 / (t[:, 0] + 233.426))
            p_cav = cav_h * 10.0 ** (5.1962 - 1730.63 / (np.maximum(cav_t, 1.0) + 233.426))
            drive = np.clip(p_cav - aw * p_food, -0.4, 0.4)
            q_lat = q_lat + 4000.0 * drive
        t_inf = 90.0 + 95.0 * heat_cmd
        flux = h * (t_inf - t[:, 0]) + q_lat + 7000.0 * heat_cmd
        if shell_k:
            # Crust raises the resistance of the surface cell before conduction.
            k_step = k * (1.0 - shell_k * shell)[:, None]
            k_step[:, 0] = k[:, 0] * (1.0 - shell_k * shell)
            alpha = k_step / RHO_C
        # Conduction.
        lap = np.zeros_like(t)
        lap[:, 1:-1] = (t[:, 2:] - 2 * t[:, 1:-1] + t[:, :-2]) / dx[:, None] ** 2
        lap[:, 0] = (t[:, 1] - t[:, 0]) / dx ** 2 + flux / (K_BASE * dx)
        if door_s is not None and abs(now - door_s) < dt * 0.5:
            t = t.copy()
            t[:, 0] = np.maximum(t[:, 0] - 15.0, 0.0)
        lap[:, -1] = (t[:, -2] - t[:, -1]) / dx ** 2
        t = t + dt * alpha * lap
        t = np.clip(t, 0.0, 220.0)
        # Moisture diffusion and surface loss.
        d = 2.0e-9 * (1.0 + 3.0 * m)
        ml = np.zeros_like(m)
        ml[:, 1:-1] = (m[:, 2:] - 2 * m[:, 1:-1] + m[:, :-2]) / dx[:, None] ** 2
        ml[:, 0] = (m[:, 1] - m[:, 0]) / dx ** 2
        ml[:, -1] = (m[:, -2] - m[:, -1]) / dx ** 2
        if moisture_bc == "flux":
            loss = 8.0e-4 * np.maximum(aw - 0.4, 0.0) * (0.3 + fan) * (1.0 - 0.5 * steam)
            gain = 1.2e-4 * steam * (1.0 - m[:, 0])
            m = m + dt * d * ml
            m[:, 0] = m[:, 0] + dt * (gain - loss)
            m = np.clip(m, 0.02, 0.95)
        else:
            loss = 1.6e-4 * np.maximum(aw - 0.4, 0.0) * (0.3 + fan) * (1.0 - steam)
            gain = 1.1e-4 * steam * (1.0 - m[:, 0])
            ml[:, 0] = ml[:, 0] - loss / DX_FRAC + gain / DX_FRAC
            m = np.clip(m + dt * d * ml, 0.02, 0.95)
        # Kinetics at core and surface.
        rate = 10.0 ** ((t_core - 70.0) / 10.0) / 60.0
        f_value = f_value + dt * rate
        # Browning only when surface is hot and drier.
        alpha_b = alpha_b + dt * 2e-4 * np.maximum(t[:, 0] - 110.0, 0.0) * np.maximum(0.55 - m[:, 0], 0.0)
        alpha_b = np.clip(alpha_b, 0.0, 1.5)
        shell = np.clip(shell + dt * 1.5e-4 * np.maximum(0.45 - m[:, 0], 0.0), 0.0, 1.0)
        # Vapour fraction follows the surface dryness. It is a field, not a second pressure solve.
        vapor = np.clip((1.0 - m[:, 0]) * (0.2 + 0.8 * cav_h), 0.0, 0.9)
        if (s % record_every == 0) or (s == steps - 1):
            rec_time.append(now)
            rec_alpha.append(1.0 - np.exp(-f_value / 2.0))

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
            hist["exhaust"].append(exhaust.copy())
            hist["mode"].append(mode.astype(float).copy())
            hist["heater"].append(heater_temp.copy())
            hist["cook_mode"].append(cook_mode.astype(float).copy())
            hist["water"].append(water.copy())
            hist["cav_t"].append(cav_t.copy())
            hist["cav_h"].append(cav_h.copy())
            hist["cav_p"].append(cav_p.copy())
            hist["door"].append(door.copy())
            hist["leak"].append(leak.copy())
            hist["vapor"].append(vapor.copy())
            hist["shell"].append(shell.copy())
            # Three paths of the same steam command.
            hist["path_a"].append((18000.0 * steam * (1.0 - aw)).copy())
            hist["path_b"].append((9000.0 * (1.0 - steam) * np.maximum(aw - 0.35, 0.0) * fan).copy())
            hist["path_c"].append((0.55 * shell * k[:, 0]).copy())
            hist["r_field"].append((1.2 + 2.5 * shell).copy())

    alpha_end = 1.0 - np.exp(-f_value / 2.0)
    rec_time = np.asarray(rec_time)
    rec_alpha = np.stack(rec_alpha, axis=0)
    nearest = np.argmin(np.abs(rec_time[:, None] - stop[None, :]), axis=0)
    alpha_at_stop = rec_alpha[nearest, np.arange(b)]
    if store_history:
        out = {k: np.stack(v, axis=0) for k, v in hist.items()}
        out["alpha_end"] = out["alpha_m"][-1]
        out["energy"] = out["heat"].sum(axis=0) * dt * record_every
    else:
        out = {}
        out["alpha_end"] = alpha_end
        out["energy"] = energy_acc * dt * record_every
    out["stop"] = stop
    out["alpha_at_stop"] = alpha_at_stop
    out["e_alpha"] = alpha_at_stop - 0.85
    out["proto"] = proto
    out["length"] = length
    out["policy"] = policy
    out["final_var"] = var_r
    out["alpha_b_end"] = alpha_b
    still = np.isnan(snap_std)
    if np.any(still):
        snap_std = np.where(still, t.std(axis=1), snap_std)
        snap_cold = np.where(still, t.argmin(axis=1).astype(float), snap_cold)
    out["t_std_stop"] = snap_std
    out["cold_index_stop"] = snap_cold
    return out
