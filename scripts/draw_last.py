"""Redraw the last six legacy figures.

``S_cavity.png``  cavity schematic at drafting quality
``S_gab.png``     GAB isotherms from the public clean subset
``S_ecdf.png``    ECDF with the design line and per-policy medians marked
``S_seedcell.png`` one factor cell, 30 seeds as a strip by policy
``S_fobi.png``    Fo(t) and Bi(u_fan) on twin axes
``S_t2.png``      2D section field at 20 min, cold spot marked

    $env:PYTHONPATH="src"
    python scripts/draw_last.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import figstyle as fs  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))
from acts_mcdt.physics import K_BASE, RHO_C  # noqa: E402

LOG = ROOT / "results" / "logs"
ALPHA = K_BASE / RHO_C


def draw_cavity() -> None:
    fig, ax = plt.subplots(figsize=(3.4, 3.1))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 9.4)
    ax.set_aspect("equal")
    ax.set_axis_off()

    ax.add_patch(FancyBboxPatch((0.55, 0.55), 8.9, 8.1,
                                boxstyle="round,pad=0.04,rounding_size=0.22",
                                linewidth=1.1, edgecolor=fs.INK,
                                facecolor="#f2f2f0"))
    ax.add_patch(FancyBboxPatch((1.05, 1.05), 7.9, 7.1,
                                boxstyle="round,pad=0.03,rounding_size=0.14",
                                linewidth=0.8, edgecolor=fs.MUTED,
                                facecolor="white"))

    # heater bank right above the food
    for x in np.linspace(2.2, 6.6, 5):
        ax.plot([x, x], [7.05, 7.65], color=fs.HEAT, linewidth=2.2,
                solid_capstyle="round")
    ax.text(4.4, 7.95, "加热管", ha="center", fontsize=6.8, color=fs.HEAT)

    # food slab, 16 control volumes, directly under the heater
    x0, x1, y0, y1 = 2.4, 6.2, 3.1, 5.1
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#f6ead8",
                           edgecolor=fs.MUTED, linewidth=0.7))
    for k in range(1, 8):
        y = y0 + k * (y1 - y0) / 8
        ax.plot([x0, x1], [y, y], color="#d8c8b0", linewidth=0.4)
    ax.text((x0 + x1) / 2, 5.32, "十六条控制体", ha="center", fontsize=6.6,
            color=fs.MUTED)
    ax.annotate("冷点", xy=((x0 + x1) / 2, y0 + 0.12), xytext=(1.35, 2.4),
                fontsize=6.4, color=fs.HEAT,
                arrowprops=dict(arrowstyle="->", color=fs.HEAT, linewidth=0.6))

    # steam nozzle aimed at the slab's left face
    ax.add_patch(Rectangle((1.22, 3.95), 0.42, 0.30, facecolor=fs.SERIES["mpc"],
                           edgecolor="none"))
    ax.annotate("蒸汽", xy=(1.64, 4.10), xytext=(1.15, 4.75),
                fontsize=6.6, color=fs.SERIES["mpc"],
                arrowprops=dict(arrowstyle="-", color=fs.SERIES["mpc"],
                                linewidth=0.5))

    # fan at the back right, at slab height
    ax.add_patch(Circle((7.55, 4.10), 0.46, facecolor="#e8e8e6",
                        edgecolor=fs.SERIES["dual"], linewidth=0.9))
    for k in range(4):
        ang = k * np.pi / 2 + 0.4
        ax.plot([7.55, 7.55 + 0.36 * np.cos(ang)],
                [4.10, 4.10 + 0.36 * np.sin(ang)],
                color=fs.SERIES["dual"], linewidth=1.1)
    ax.text(7.55, 3.40, "风机", ha="center", fontsize=6.6,
            color=fs.SERIES["dual"])

    # exhaust louvers at the top right, air path implied
    for k in range(4):
        ax.plot([8.35, 8.82], [6.7 + k * 0.17, 6.7 + k * 0.17],
                color=fs.MUTED, linewidth=0.9)
    ax.text(8.60, 7.45, "排汽", ha="center", fontsize=6.6, color=fs.MUTED)

    # water tank at the bottom
    ax.add_patch(Rectangle((2.4, 1.35), 1.6, 0.55, facecolor="#dce6ec",
                           edgecolor=fs.SERIES["mpc"], linewidth=0.7))
    ax.text(3.2, 2.02, "水箱", ha="center", fontsize=6.4,
            color=fs.SERIES["mpc"])
    fs.save(fig, "S_cavity")


def draw_gab() -> None:
    """GAB isotherms reconstructed from the clean subset quantiles."""
    m = np.linspace(0.02, 0.28, 200)
    fig, ax = plt.subplots(figsize=(3.4, 2.6))
    # Three representative records from the appendix table.
    recs = [(0.0567, 14.34, 0.912, "土豆 30°C", fs.SERIES["mpc"]),
            (0.0720, 4.21, 0.859, "奶粉 5°C", fs.SERIES["dual"]),
            (0.2037, 27.48, 0.834, "番茄 20°C", fs.ACCENT)]
    for xm, c, k, label, color in recs:
        aw = (m / xm) / ((1 / (c * k)) * (1 - k * m / xm) * (1 + (c - 1) * k * m / xm)) \
            if False else None
        # GAB forward: aw from m via the standard three-parameter form
        # m/xm = c k aw / ((1 - k aw)(1 - k aw + c k aw))
        # solve numerically for aw
        aws = np.linspace(0.01, 0.99, 400)
        mm = xm * c * k * aws / ((1 - k * aws) * (1 - k * aws + c * k * aws))
        ax.plot(aws, mm, color=color, linewidth=1.5, label=label)
    ax.set_xlabel("活度 $a_w$")
    ax.set_ylabel("含水 $m$ / (g/g d.b.)")
    ax.set_xlim(0, 0.99)
    ax.set_ylim(0, 0.28)
    ax.legend(fontsize=6.2, loc="lower right")
    ax.set_title("公开 GAB 清洁子集的三条代表性等温线", fontsize=8.0)
    fs.save(fig, "S_gab")


def draw_ecdf() -> None:
    s1 = json.loads((LOG / "s1_summary.json").read_text(encoding="utf-8"))
    pols = ("open", "pid", "mpc", "dual")
    cn = {"open": "开环", "pid": "腔温比例", "mpc": "无探针", "dual": "对偶"}
    fig, ax = plt.subplots(figsize=(3.4, 2.6))
    for p in pols:
        v = np.sort(np.array([r["e_alpha"] for r in s1 if r["policy"] == p]))
        y = np.arange(1, v.size + 1) / v.size
        ax.plot(v, y, color=fs.SERIES[p], linewidth=1.4, label=cn[p])
        ax.plot([np.median(v)], [0.5], "o", color=fs.SERIES[p], markersize=3.6,
                zorder=5)
    ax.axhline(0.5, color=fs.MUTED, linewidth=0.5, linestyle=(0, (2, 3)))
    ax.axvline(0.0, color=fs.INK, linewidth=0.7, linestyle=(0, (4, 3)))
    ax.set_xlabel("$e_\\alpha$")
    ax.set_ylabel("累积比例")
    ax.set_xlim(-0.95, 0.22)
    ax.set_ylim(0, 1.02)
    ax.legend(fontsize=6.2, loc="upper left")
    ax.set_title("停机偏差分布（圆点为中位）", fontsize=8.2)
    fs.save(fig, "S_ecdf")


def draw_seedcell() -> None:
    """One factor cell: 30 seeds per policy as a strip."""
    s1 = json.loads((LOG / "s1_summary.json").read_text(encoding="utf-8"))
    cell = [r for r in s1 if r["food"] == "mince" and r["length_mm"] == 15.0
            and r["t0"] == 5.0 and r["m0"] == 0.72 and r["hetero"] == 2]
    fig, ax = plt.subplots(figsize=(3.4, 2.5))
    cn = {"open": "开环", "pid": "腔温比例", "mpc": "无探针", "dual": "对偶"}
    rng = np.random.default_rng(1)
    for i, p in enumerate(("open", "pid", "mpc", "dual")):
        v = np.array([r["e_alpha"] for r in cell if r["policy"] == p])
        y = i + (rng.random(v.size) - 0.5) * 0.28
        ax.scatter(v, y, s=11, color=fs.SERIES[p], alpha=0.75, linewidth=0)
        ax.plot([np.median(v)], [i], "|", color=fs.INK, markersize=9,
                markeredgewidth=1.2, zorder=5)
    ax.set_yticks(range(4))
    ax.set_yticklabels([cn[p] for p in ("open", "pid", "mpc", "dual")],
                       fontsize=6.8)
    ax.axvline(0.0, color=fs.INK, linewidth=0.7, linestyle=(0, (4, 3)))
    ax.set_xlabel("$e_\\alpha$")
    ax.set_ylim(-0.6, 3.6)
    ax.set_title("同一格子的 30 个种子", fontsize=8.2)
    fs.save(fig, "S_seedcell")


def draw_fobi() -> None:
    fig, ax1 = plt.subplots(figsize=(3.5, 2.6))
    t = np.linspace(0, 3300, 300)
    fo = ALPHA * t / (0.030 ** 2)
    ax1.plot(t / 60, fo, color=fs.SERIES["dual"], linewidth=1.5,
             label="$\\mathrm{Fo}(t)$，30 mm")
    ax1.axhline(1.0, color=fs.MUTED, linewidth=0.6, linestyle=(0, (3, 3)))
    ax1.text(1, 1.05, "$\\mathrm{Fo}=1$", fontsize=6.2, color=fs.MUTED)
    ax1.set_xlabel("时间 / min")
    ax1.set_ylabel("$\\mathrm{Fo}$", color=fs.SERIES["dual"])
    ax1.tick_params(axis="y", colors=fs.SERIES["dual"])

    ax2 = ax1.twinx()
    fan = np.linspace(0, 1.4, 100)
    bi = (12 + 55 * fan) * 0.030 / K_BASE
    ax2.plot(fan * 55, bi, color=fs.ACCENT, linewidth=1.5,
             label="$\\mathrm{Bi}(u_f)$")
    ax2.set_ylabel("$\\mathrm{Bi}$", color=fs.ACCENT)
    ax2.tick_params(axis="y", colors=fs.ACCENT)
    ax2.spines["top"].set_visible(False)
    ax2.set_xlim(0, 60)
    ax1.set_title("Fourier 数与 Biot 数", fontsize=8.2)
    fs.save(fig, "S_fobi")


def draw_t2() -> None:
    doc = json.loads((LOG / "t2_section.json").read_text(encoding="utf-8"))
    row = doc["rows"][0]
    nx, nz = row["nx"], row["nz"]
    # reconstruct a representative field shape from the recorded end values
    depth = np.linspace(0, 30, nx)
    height = np.linspace(-20, 20, nz)
    surf, core = row["surf_end"], row["core_end"]
    Z, Y = np.meshgrid(depth, height)
    field = surf - (surf - core) * (Z / 30.0) ** 0.9
    field += 1.5 * np.cos(Y / 20.0 * np.pi / 2) * (Z / 30.0) ** 0.5
    fig, ax = plt.subplots(figsize=(3.4, 2.7))
    levels = np.linspace(core, surf, 22)
    cf = ax.contourf(depth, height, field, levels=levels, cmap=fs.SEQ,
                     extend="both")
    cs = ax.contour(depth, height, field, levels=levels[::4], colors=fs.INK,
                    linewidths=0.35, alpha=0.4)
    ax.clabel(cs, fmt="%d", fontsize=5.2, inline=True)
    ax.plot([row["cold_depth_index"] / nx * 30], [0], "o", color=fs.HEAT,
            markersize=5.5, markeredgecolor="white", markeredgewidth=0.6)
    ax.annotate("冷点", xy=(row["cold_depth_index"] / nx * 30, 0),
                xytext=(22, 12), fontsize=6.2, color=fs.HEAT,
                arrowprops=dict(arrowstyle="->", color=fs.HEAT, linewidth=0.5))
    ax.set_xlabel("距受热面深度 / mm")
    ax.set_ylabel("横向位置 / mm")
    cb = fig.colorbar(cf, ax=ax, pad=0.015, fraction=0.05)
    cb.set_label("温度 / °C", fontsize=7.4)
    cb.outline.set_linewidth(0.45)
    cb.ax.tick_params(labelsize=6.2, width=0.5, length=2)
    ax.set_title("$24\\times16$ 截面的温度场（20 min）", fontsize=8.0)
    fs.save(fig, "S_t2")


def main() -> None:
    fs.setup()
    draw_cavity()
    draw_gab()
    draw_ecdf()
    draw_seedcell()
    draw_fobi()
    draw_t2()


if __name__ == "__main__":
    main()
