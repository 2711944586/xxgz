"""Product modes of one steam-bake cavity.

The food slab receives fluxes. This module decides which of the four
actuators may move, and which hard measurements overwrite them.
"""

from __future__ import annotations

STEAM = 0
BAKE = 1
COMBI = 2
NAMES = ("steam", "bake", "combi")


def apply_mode(mode: int, heat: float, steam: float, fan: float, exhaust: float):
    """Return the four commands after the product mode."""
    if mode == STEAM:
        return min(heat, 0.25), steam, fan, exhaust
    if mode == BAKE:
        return heat, 0.0, fan, max(exhaust, 0.45)
    return heat, steam, fan, exhaust


def project(heat_req, steam, heater, water, door, leak):
    """Hard measurements overwrite the quality request.

    The four inequalities do not read a quality estimate.
    """
    blocked = (water < 0.05) or (door > 0.5) or (leak > 0.003) or (heater >= 250.0)
    if blocked:
        return 0.0, 0.0, True
    if heater > 230.0:
        over = min(1.0, max(0.0, (heater - 230.0) / 40.0))
        return heat_req * (1.0 - 0.75 * over), steam, False
    return heat_req, steam, False
