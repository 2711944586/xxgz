"""Checks that match the outline propositions on the two-node limit."""

from __future__ import annotations

import numpy as np


def steady_sensitivity(r_values=(1.0, 3.0, 6.0), t_inf=100.0) -> dict:
    """At equilibrium with no phase change, surface and core meet t_inf."""
    temps = []
    for r in r_values:
        t1, t2 = t_inf, t_inf
        for _ in range(400):
            t1 += 0.05 * ((t_inf - t1) / 1.0 + (t2 - t1) / r)
            t2 += 0.05 * ((t1 - t2) / r) / 4.0
        temps.append((t1, t2))
    arr = np.array(temps)
    spread = float(arr.max() - arr.min())
    return {"temps": arr, "spread": spread, "passed": spread < 1e-3}


def pulse_rank() -> dict:
    """A steam-then-fan pair must move the resistance estimate more than steam alone."""

    def response(steam_then_fan: bool) -> float:
        t1, t2, r_hat = 20.0, 20.0, 2.0
        r_true = 4.0
        for step in range(80):
            steam = 1.0 if step < 20 else 0.0
            fan = 1.4 if steam_then_fan and step >= 20 else 0.3
            h = 1.0 + fan
            q = 8.0 * steam - 1.5 * fan * (1.0 - steam)
            t1 += 0.1 * (h * (90.0 - t1) + q + (t2 - t1) / r_true)
            t2 += 0.1 * ((t1 - t2) / r_true) / 4.0
        lag = t1 - t2
        return lag

    both = response(True)
    steam = response(False)
    # The second segment has to add information, not a fixed percentage.
    return {"lag_p4": both, "lag_steam": steam, "passed": both > steam + 1.0}


def cold_spot_bound(tau2=30.0, tau=3.0, delta_ts=12.0) -> dict:
    predicted = tau / tau2 * delta_ts
    # Discrete filter.
    t2 = 0.0
    t1 = delta_ts
    dt = 0.05
    for _ in range(int(tau / dt)):
        t2 += dt * (t1 - t2) / tau2
    return {"bound": predicted, "realized": t2, "passed": t2 <= predicted + 1e-6}


def shield_domain() -> dict:
    """Heater limit does not depend on the quality posterior."""

    def project(request: float, heater: float, posterior: float) -> float:
        del posterior
        if heater > 210.0:
            return min(request, 0.25)
        return request

    a = project(1.0, 230.0, 0.1)
    b = project(1.0, 230.0, 0.9)
    c = project(1.0, 100.0, 0.9)
    return {"clipped": a, "same": a == b, "open": c, "passed": a == b and a < c}
