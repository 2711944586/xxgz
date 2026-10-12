"""Compiled inner step of the sixteen-cell kernel.

The arithmetic matches rollout() when the optional boundary flags stay at
their defaults. Those flags stay in the NumPy loop.
"""

from __future__ import annotations

import numpy as np
from numba import njit


@njit(cache=True)
def _noise(seed, step):
    x = np.sin(seed * 12.9898 + step * 78.233) * 43758.5453
    return (x - np.floor(x)) * 2.0 - 1.0


@njit(cache=True)
def integrate(
    length, proto, t0, m0, hetero, seed, policy_code, minutes, dt, record_every, store,
):
    b = length.shape[0]
    n = 16
    steps = int(minutes * 60.0 / dt)
    dx = length / n
    k_base = 2.0e-7 * 3.4e6
    k = np.full((b, n), k_base)
    for i in range(b):
        if hetero[i] == 2:
            k[i, 5] = 0.45 * k_base
    alpha = k / 3.4e6
    temp = np.empty((b, n))
    moist = np.empty((b, n))
    for i in range(b):
        for j in range(n):
            temp[i, j] = t0[i]
            moist[i, j] = m0[i]
            if hetero[i] == 1:
                temp[i, j] += -4.0 + 8.0 * j / (n - 1)
    f_value = np.zeros(b)
    alpha_b = np.zeros(b)
    shell = np.zeros(b)
    heater = np.full(b, 40.0)
    r_hat = np.full(b, 5.0)
    tc_hat = t0.copy()
    var_r = np.full(b, 0.64)
    probed = np.zeros(b, dtype=np.int8)
    stopped = np.zeros(b, dtype=np.int8)
    stop = np.full(b, minutes * 60.0)
    energy = np.zeros(b)
    nrec = steps // record_every + 1
    rec_t = np.empty(nrec)
    rec_a = np.empty((nrec, b))
    nkeep = nrec if store else 0
    hist_t = np.empty((nkeep, b))
    hist_surf = np.empty((nkeep, b))
    hist_core = np.empty((nkeep, b))
    hist_hat = np.empty((nkeep, b))
    hist_m = np.empty((nkeep, b))
    hist_am = np.empty((nkeep, b))
    hist_ab = np.empty((nkeep, b))
    hist_var = np.empty((nkeep, b))
    hist_heat = np.empty((nkeep, b))
    hist_req = np.empty((nkeep, b))
    hist_steam = np.empty((nkeep, b))
    hist_heater = np.empty((nkeep, b))
    rec = 0
    kept = 0
    for s in range(steps):
        now = s * dt
        core = np.empty(b)
        mean_m = np.empty(b)
        for i in range(b):
            cmin = temp[i, 0]
            acc = 0.0
            for j in range(n):
                acc += moist[i, j]
                if temp[i, j] < cmin:
                    cmin = temp[i, j]
            core[i] = cmin
            mean_m[i] = acc / n
        for i in range(b):
            noise_t = 0.4 * _noise(seed[i] + 17.0 * policy_code, s)
            noise_m = 0.004 * _noise(seed[i] + 91.0 * policy_code, s + 3)
            y_t = temp[i, 0] + noise_t
            y_m = mean_m[i] + noise_m
            if y_m < 0.0:
                y_m = 0.0
            if y_m > 1.0:
                y_m = 1.0
            y_cav = 110.0 + noise_t * 0.2
            gap = temp[i, 0] - core[i]
            if gap < 0.3:
                gap = 0.3
            r_proxy = gap / 8.0 + 1.2 + 2.5 * shell[i]
            if r_proxy < 0.8:
                r_proxy = 0.8
            if r_proxy > 8.0:
                r_proxy = 8.0
            m_surf = moist[i, 0]
            if m_surf < 1e-3:
                m_surf = 1e-3
            if m_surf > 0.95:
                m_surf = 0.95
            scale = 0.10
            kk = 0.70
            if proto[i] == 1:
                scale = 0.055
                kk = 0.80
            elif proto[i] == 2:
                scale = 0.08
                kk = 0.75
            aw = 1.0 - np.exp(-m_surf / scale) * (1.0 - 0.15 * kk)
            if aw < 0.02:
                aw = 0.02
            if aw > 0.99:
                aw = 0.99
            menu = 900.0 + 18000.0 * (length[i] - 0.015)
            if policy_code == 1:
                heat_req = 1.0 if now < menu else 0.0
                steam = 0.8 if (now < 0.45 * menu and proto[i] >= 1) else 0.0
                fan = 0.3
                if now >= menu and stopped[i] == 0:
                    stop[i] = menu
                    stopped[i] = 1
            elif policy_code == 2:
                heat_req = 0.04 * (160.0 - y_cav) + 0.6
                if heat_req < 0.0:
                    heat_req = 0.0
                if heat_req > 1.0:
                    heat_req = 1.0
                steam = 0.3 if y_m > 0.2 else 0.0
                fan = 0.45
            else:
                tau = r_hat[i]
                if tau < 0.8:
                    tau = 0.8
                if tau > 8.0:
                    tau = 8.0
                tau = tau * (length[i] / 0.03) ** 2 * 280.0
                tc_hat[i] = tc_hat[i] + dt * (y_t - tc_hat[i]) / tau
                cap = y_t - 4.0 * max(r_hat[i] - 1.0, 0.2)
                if tc_hat[i] > cap:
                    tc_hat[i] = cap
                if policy_code == 4:
                    in_probe = now >= 150.0 and now < 190.0 and var_r[i] > 0.25 and probed[i] == 0
                    steam = 1.0 if (in_probe and now < 170.0) else 0.0
                    fan = 1.3 if (in_probe and now >= 170.0) else 0.4
                    if now >= 190.0 and probed[i] == 0 and var_r[i] > 0.25:
                        lag = (y_t - tc_hat[i]) / 6.0
                        if lag < 0.0:
                            lag = 0.0
                        if lag > 3.0:
                            lag = 3.0
                        r_new = 1.4 + 1.1 * lag + 1.2 * (length[i] / 0.03)
                        if r_new < 0.8:
                            r_new = 0.8
                        if r_new > 7.0:
                            r_new = 7.0
                        if abs(r_new - r_proxy) < abs(r_hat[i] - r_proxy):
                            r_hat[i] = r_new
                            var_r[i] *= 0.35
                        probed[i] = 1
                else:
                    steam = 0.0
                    fan = 0.4
                margin = 6.0 + 10.0 * np.sqrt(var_r[i]) * (length[i] / 0.03)
                heat_req = 0.35 + (75.0 + margin - tc_hat[i]) / 30.0
                if heat_req < 0.15:
                    heat_req = 0.15
                if heat_req > 1.0:
                    heat_req = 1.0
                ready = tc_hat[i] > 75.0 + margin and now > 240.0
                if policy_code == 4 and var_r[i] > 0.45 and length[i] > 0.04:
                    ready = False
                if ready and stopped[i] == 0:
                    stop[i] = now
                if ready:
                    stopped[i] = 1
                if stopped[i] == 1:
                    heat_req = 0.15
            heater[i] = heater[i] + dt * (
                0.015 * heat_req * (280.0 - heater[i]) - 0.008 * (heater[i] - 40.0)
            )
            over = (heater[i] - 230.0) / 40.0
            if over < 0.0:
                over = 0.0
            if over > 1.0:
                over = 1.0
            heat = heat_req * (1.0 - 0.75 * over)
            if s % record_every == 0 or s == steps - 1:
                energy[i] += heat
            h = 12.0 + 55.0 * fan
            q_lat = 18000.0 * steam * (1.0 - aw) - 9000.0 * (1.0 - steam) * max(aw - 0.35, 0.0) * fan
            t_inf = 90.0 + 95.0 * heat
            flux = h * (t_inf - temp[i, 0]) + q_lat + 7000.0 * heat
            nxt = np.empty(n)
            inv = 1.0 / (dx[i] * dx[i])
            for j in range(1, n - 1):
                nxt[j] = temp[i, j] + dt * alpha[i, j] * (temp[i, j + 1] - 2.0 * temp[i, j] + temp[i, j - 1]) * inv
            nxt[0] = temp[i, 0] + dt * alpha[i, 0] * (
                (temp[i, 1] - temp[i, 0]) * inv + flux / (k_base * dx[i])
            )
            nxt[n - 1] = temp[i, n - 1] + dt * alpha[i, n - 1] * (temp[i, n - 2] - temp[i, n - 1]) * inv
            for j in range(n):
                if nxt[j] < 0.0:
                    nxt[j] = 0.0
                if nxt[j] > 220.0:
                    nxt[j] = 220.0
            nm = np.empty(n)
            for j in range(n):
                coef = 2.0e-9 * (1.0 + 3.0 * moist[i, j])
                if 0 < j < n - 1:
                    nm[j] = moist[i, j] + dt * coef * (moist[i, j + 1] - 2.0 * moist[i, j] + moist[i, j - 1]) * inv
            loss = 1.6e-4 * max(aw - 0.4, 0.0) * (0.3 + fan) * (1.0 - steam)
            gain = 1.1e-4 * steam * (1.0 - moist[i, 0])
            coef0 = 2.0e-9 * (1.0 + 3.0 * moist[i, 0])
            nm[0] = moist[i, 0] + dt * coef0 * ((moist[i, 1] - moist[i, 0]) * inv - loss * n + gain * n)
            coefn = 2.0e-9 * (1.0 + 3.0 * moist[i, n - 1])
            nm[n - 1] = moist[i, n - 1] + dt * coefn * (moist[i, n - 2] - moist[i, n - 1]) * inv
            for j in range(n):
                if nm[j] < 0.02:
                    nm[j] = 0.02
                if nm[j] > 0.95:
                    nm[j] = 0.95
                temp[i, j] = nxt[j]
                moist[i, j] = nm[j]
            rate = 10.0 ** ((core[i] - 70.0) / 10.0) / 60.0
            f_value[i] += dt * rate
            grow = temp[i, 0] - 110.0
            if grow < 0.0:
                grow = 0.0
            dry = 0.55 - moist[i, 0]
            if dry < 0.0:
                dry = 0.0
            alpha_b[i] += dt * 2.0e-4 * grow * dry
            if alpha_b[i] > 1.5:
                alpha_b[i] = 1.5
            crust = 0.45 - moist[i, 0]
            if crust < 0.0:
                crust = 0.0
            shell[i] += dt * 1.5e-4 * crust
            if shell[i] > 1.0:
                shell[i] = 1.0
        if s % record_every == 0 or s == steps - 1:
            rec_t[rec] = now
            for i in range(b):
                rec_a[rec, i] = 1.0 - np.exp(-f_value[i] / 2.0)
            if store:
                for i in range(b):
                    cmin = temp[i, 0]
                    acc = 0.0
                    for j in range(n):
                        acc += moist[i, j]
                        if temp[i, j] < cmin:
                            cmin = temp[i, j]
                    hist_t[kept, i] = now
                    hist_surf[kept, i] = temp[i, 0]
                    hist_core[kept, i] = cmin
                    hist_hat[kept, i] = tc_hat[i]
                    hist_m[kept, i] = acc / n
                    hist_am[kept, i] = rec_a[rec, i]
                    hist_ab[kept, i] = alpha_b[i]
                    hist_var[kept, i] = var_r[i]
                    hist_heat[kept, i] = heat
                    hist_req[kept, i] = heat_req
                    hist_steam[kept, i] = steam
                    hist_heater[kept, i] = heater[i]
                kept += 1
            rec += 1
    alpha_stop = np.empty(b)
    for i in range(b):
        best = 0
        best_gap = abs(rec_t[0] - stop[i])
        for j in range(1, rec):
            gap = abs(rec_t[j] - stop[i])
            if gap < best_gap:
                best_gap = gap
                best = j
        alpha_stop[i] = rec_a[best, i]
    return (
        stop, alpha_stop, energy * dt * record_every, var_r, alpha_b,
        hist_t[:kept], hist_surf[:kept], hist_core[:kept], hist_hat[:kept],
        hist_m[:kept], hist_am[:kept], hist_ab[:kept], hist_var[:kept],
        hist_heat[:kept], hist_req[:kept], hist_steam[:kept], hist_heater[:kept],
    )
