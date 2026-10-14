# -*- coding: utf-8 -*-
"""Redraw campaign / study figures with Chinese labels and readable type."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, to_rgb

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "results" / "logs"
FIG = ROOT / "results" / "figures"
PAPER = FIG / "paper"
STUDY = FIG / "study"

INK = "#1c1a17"
MUTED = "#5c564c"
HEAT = "#c45c26"
STEAM = "#2a6f7f"
NAVY = "#1f4e79"
SAGE = "#4a6b4e"
GOLD = "#b8860b"
LINE = "#d9d2c5"
POL_C = {"open": MUTED, "pid": HEAT, "mpc": STEAM, "dual": NAVY}
POL_N = {"open": "开环", "pid": "腔温比例", "mpc": "无探针", "dual": "对偶"}
FOOD_N = {"mince": "肉糜", "potato": "土豆", "dough": "面团"}
COOK_N = {"steam": "蒸", "bake": "烤", "combi": "组合"}
POLICIES = ("open", "pid", "mpc", "dual")
FOODS = ("mince", "potato", "dough")
COOKS = ("steam", "bake", "combi")

HEATMAP = LinearSegmentedColormap.from_list(
    "acts_heat", ["#1f4e79", "#7aa0b8", "#f4efe4", "#e0a36a", "#c45c26"]
)


def setup():
    mpl.rcParams.update({
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "text.color": INK,
        "axes.linewidth": 0.85,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": LINE,
        "grid.linewidth": 0.5,
        "grid.alpha": 0.85,
        "legend.frameon": False,
        "legend.fontsize": 9.5,
        "savefig.dpi": 220,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.12,
        "font.size": 10.6,
        "axes.titlesize": 11.6,
        "axes.labelsize": 10.8,
        "xtick.labelsize": 9.6,
        "ytick.labelsize": 9.6,
        "figure.constrained_layout.use": True,
    })


def save(fig, *paths):
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path)
    plt.close(fig)


def ink_or_white(val, vmin, vmax, cmap):
    t = np.clip((val - vmin) / (vmax - vmin + 1e-12), 0, 1)
    r, g, b = to_rgb(cmap(t))
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    return INK if lum > 0.55 else "white"


def heatmap(ax, grid, rows, cols, vmin, vmax, cmap, fmt="{:+.2f}"):
    ax.grid(False)
    im = ax.imshow(grid, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    ax.set_xticks(range(len(cols)), cols)
    ax.set_yticks(range(len(rows)), rows)
    ax.spines["top"].set_visible(True)
    ax.spines["right"].set_visible(True)
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            ax.text(
                j, i, fmt.format(grid[i, j]), ha="center", va="center",
                color=ink_or_white(grid[i, j], vmin, vmax, cmap), fontsize=10.5,
            )
    return im


def draw_trace_panels(df):
    t = df["time"].to_numpy() / 60.0
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    ax.axvspan(150 / 60, 190 / 60, color=STEAM, alpha=0.12, zorder=0)
    ax.plot(t, df["t_surf"], color=HEAT, lw=1.9, label="表面")
    ax.plot(t, df["t_core"], color=STEAM, lw=1.9, label="冷点")
    ax.plot(t, df["t_hat"], color=GOLD, lw=1.7, ls="--", label="估计")
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("温度 / ℃")
    ax.legend(loc="center right", fontsize=8.6, frameon=False)
    ax.set_xlim(0, 55)
    save(fig, FIG / "D1_temperature.png", PAPER / "D1_temperature.png")

    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    ax.plot(t, df["m_mean"], color=STEAM, lw=1.9)
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("平均含水")
    lo, hi = float(df["m_mean"].min()), float(df["m_mean"].max())
    pad = max(0.004, 0.25 * (hi - lo))
    ax.set_ylim(lo - pad, hi + pad)
    ax.yaxis.get_major_formatter().set_useOffset(False)
    ax.yaxis.get_major_formatter().set_scientific(False)
    ax.set_xlim(0, 55)
    save(fig, FIG / "D2_moisture.png", PAPER / "D2_moisture.png")

    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    ax.axvspan(150 / 60, 190 / 60, color=STEAM, alpha=0.12, zorder=0)
    ax.plot(t, df["alpha_m"], color=HEAT, lw=1.9, label="冷点进度")
    ax.plot(t, df["alpha_b"] if "alpha_b" in df.columns else np.zeros(len(df)),
            color=NAVY, lw=1.6, label="表面褐变代理")
    ax.axhline(0.85, color=MUTED, lw=0.9, ls=":")
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("进度")
    ax.legend(loc="upper left")
    ax.set_xlim(0, 55)
    ax.set_ylim(-0.02, 1.05)
    save(fig, FIG / "D3_progress.png", PAPER / "D3_progress.png")

    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    ax.axvspan(150 / 60, 190 / 60, color=STEAM, alpha=0.12, zorder=0)
    ax.plot(t, df["var_r"], color=HEAT, lw=1.9)
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("热阻方差")
    ax.set_xlim(0, 55)
    ax.set_ylim(0.15, 0.72)
    save(fig, FIG / "D6_variance.png", PAPER / "D6_variance.png")

    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    ax.plot(t, df["heat_req"], color=GOLD, lw=1.6, label="请求")
    ax.plot(t, df["heat"], color=HEAT, lw=1.9, label="指令")
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("加热")
    ax.legend(loc="upper right")
    ax.set_xlim(0, 55)
    ax.set_ylim(0, 1.05)
    save(fig, FIG / "D19_projection.png", PAPER / "D19_projection.png")


def draw_s1(rows):
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for p in POLICIES:
        xs = [15, 30, 50]
        ys = [
            float(np.median([r["e_alpha"] for r in rows if r["policy"] == p and abs(r["length_mm"] - L) < 0.2]))
            for L in xs
        ]
        ax.plot(xs, ys, marker="o", ms=6, lw=1.9, color=POL_C[p], label=POL_N[p])
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_xticks([15, 30, 50])
    ax.set_xlabel("厚度 / mm")
    ax.set_ylabel("停机进度偏差中位")
    ax.legend(ncol=2, loc="lower right")
    save(fig, FIG / "D7_thickness.png", PAPER / "D7_thickness.png")

    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    bins = np.linspace(-0.9, 0.2, 37)
    for p in POLICIES:
        vals = np.array([r["e_alpha"] for r in rows if r["policy"] == p])
        ax.hist(vals, bins=bins, histtype="step", density=True, lw=1.7, color=POL_C[p], label=POL_N[p])
    ax.axvline(0, color=INK, lw=0.7)
    ax.set_xlabel(r"停机进度偏差 $e_\alpha$")
    ax.set_ylabel("密度")
    ax.legend(loc="upper left", fontsize=8.4, frameon=False)
    save(fig, FIG / "D10_policy.png", PAPER / "D10_policy.png")

    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.9))
    names = [POL_N[p] for p in POLICIES]
    energy = [float(np.median([r["energy"] for r in rows if r["policy"] == p])) for p in POLICIES]
    stop = [float(np.median([r["stop_s"] for r in rows if r["policy"] == p])) for p in POLICIES]
    colors = [POL_C[p] for p in POLICIES]
    axes[0].bar(names, energy, color=colors, width=0.62)
    axes[0].set_ylabel("累计加热中位")
    axes[1].bar(names, stop, color=colors, width=0.62)
    axes[1].set_ylabel("停机时刻中位 / s")
    for ax in axes:
        ax.tick_params(axis="x", labelrotation=0)
        ax.set_ylim(bottom=0)
    save(fig, FIG / "D11_energy_stop.png", PAPER / "D11_energy_stop.png")

    grid = np.zeros((3, 4))
    for i, food in enumerate(FOODS):
        for j, p in enumerate(POLICIES):
            grid[i, j] = float(np.median([r["e_alpha"] for r in rows if r["food"] == food and r["policy"] == p]))
    fig, ax = plt.subplots(figsize=(7.6, 4.1))
    im = heatmap(ax, grid, [FOOD_N[f] for f in FOODS], [POL_N[p] for p in POLICIES], -0.85, 0.16, HEATMAP)
    cb = fig.colorbar(im, ax=ax, pad=0.03, fraction=0.046)
    cb.set_label("停机进度偏差中位")
    save(fig, FIG / "D25_e_alpha.png", PAPER / "D25_e_alpha.png")

    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    for p in POLICIES:
        part = [
            r for r in rows
            if r["policy"] == p and abs(r["length_mm"] - 15) < 0.2
            and r["food"] == "mince" and r["t0"] == 5.0 and abs(r["m0"] - 0.72) < 1e-6 and r["hetero"] == 2
        ]
        ax.scatter([r["seed"] for r in part], [r["stop_s"] for r in part],
                   s=22, color=POL_C[p], label=POL_N[p], zorder=3)
    ax.set_xlabel("种子")
    ax.set_ylabel("停机时刻 / s")
    ax.legend(ncol=2, loc="best")
    save(fig, FIG / "D23_seed_stop.png", PAPER / "D23_seed_stop.png")


def draw_s2(s2):
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    levels = ["0", "15", "30", "60"]
    xs = [0, 15, 30, 60]
    meds, q10, q90 = [], [], []
    for lv in levels:
        vals = np.array([r["e_alpha"] for r in s2 if r["factor"] == "occlude" and r["level"] == lv])
        meds.append(float(np.median(vals)))
        q10.append(float(np.quantile(vals, 0.1)))
        q90.append(float(np.quantile(vals, 0.9)))
    ax.fill_between(xs, q10, q90, color=HEAT, alpha=0.18, label="十分位–九十分位")
    ax.plot(xs, meds, marker="o", ms=7, color=HEAT, lw=1.9, label="中位")
    ax.set_xticks(xs, [f"{x} s" for x in xs])
    ax.set_xlabel("开局保持表面读数的时长 / s")
    ax.set_ylabel(r"停机进度偏差 $e_\alpha$")
    ax.legend(loc="upper left")
    save(fig, FIG / "D15_occlusion.png", PAPER / "D15_occlusion.png")


def draw_study(rows):
    grid = np.zeros((4, 3))
    for i, p in enumerate(POLICIES):
        for j, c in enumerate(COOKS):
            grid[i, j] = float(np.median([r["e_alpha"] for r in rows if r["policy"] == p and r["cook"] == c]))
    fig, ax = plt.subplots(figsize=(6.6, 4.5))
    im = heatmap(ax, grid, [POL_N[p] for p in POLICIES], [COOK_N[c] for c in COOKS], -0.9, 0.16, HEATMAP)
    cb = fig.colorbar(im, ax=ax, pad=0.03, fraction=0.046)
    cb.set_label("进度偏差中位")
    save(fig, STUDY / "F7_policy_cook.png", PAPER / "F7_policy_cook.png")

    grid = np.zeros((3, 3))
    for i, f in enumerate(FOODS):
        for j, c in enumerate(COOKS):
            grid[i, j] = float(np.median([
                r["e_alpha"] for r in rows if r["food"] == f and r["cook"] == c and r["policy"] == "dual"
            ]))
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    im = heatmap(ax, grid, [FOOD_N[f] for f in FOODS], [COOK_N[c] for c in COOKS], -0.9, 0.16, HEATMAP)
    cb = fig.colorbar(im, ax=ax, pad=0.03, fraction=0.046)
    cb.set_label("进度偏差中位")
    save(fig, STUDY / "F1_mode_food.png")

    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    for c in COOKS:
        sub = [r for r in rows if r["cook"] == c and r["policy"] == "dual"]
        ax.scatter(
            [r["var_r"] for r in sub], [r["e_alpha"] for r in sub],
            s=9, alpha=0.28, color={"steam": STEAM, "bake": HEAT, "combi": SAGE}[c],
            label=COOK_N[c], rasterized=True,
        )
    ax.set_xlabel("结束方差")
    ax.set_ylabel("停机进度偏差")
    ax.legend(markerscale=1.8)
    save(fig, STUDY / "F10_var_error.png")


def main():
    setup()
    print("trace csv")
    df = pd.read_csv(LOG / "demo_seed7_dual.csv")
    draw_trace_panels(df)
    print("s1")
    s1 = json.loads((LOG / "s1_summary.json").read_text(encoding="utf-8"))
    draw_s1(s1)
    print("s2")
    s2 = json.loads((LOG / "s2_summary.json").read_text(encoding="utf-8"))
    draw_s2(s2)
    print("study")
    study = json.loads((LOG / "study.json").read_text(encoding="utf-8"))
    draw_study(study)
    print("done")


if __name__ == "__main__":
    main()
