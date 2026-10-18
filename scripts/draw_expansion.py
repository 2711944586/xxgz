# -*- coding: utf-8 -*-
"""Expansion figures from unused logs plus extra kernel rollouts."""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, to_rgb
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, FancyArrowPatch
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from acts_mcdt.physics import rollout  # noqa: E402

FIG = ROOT / "results" / "figures" / "paper"
LOG = ROOT / "results" / "logs"
FIG.mkdir(parents=True, exist_ok=True)

INK = "#1c1a17"
MUTED = "#5c564c"
HEAT = "#c45c26"
STEAM = "#2a6f7f"
NAVY = "#1f4e79"
SAGE = "#4a6b4e"
GOLD = "#b8860b"
LINE = "#d9d2c5"
BG = "#fbf8f2"
POL_C = {"open": MUTED, "pid": HEAT, "mpc": STEAM, "dual": NAVY}
POL_N = {"open": "开环", "pid": "腔温比例", "mpc": "无探针", "dual": "对偶"}
FOOD_N = {"mince": "肉糜", "potato": "土豆", "dough": "面团"}
COOK_N = {"steam": "蒸", "bake": "烤", "combi": "组合"}
COOK_C = {"steam": STEAM, "bake": HEAT, "combi": SAGE}

HEATMAP = LinearSegmentedColormap.from_list(
    "acts_heat", ["#f4efe4", "#f0c27a", "#c45c26", "#6b1d12"]
)
DIVERGE = LinearSegmentedColormap.from_list(
    "acts_div", ["#1f4e79", "#7aa0b8", "#f4efe4", "#e0a36a", "#c45c26"]
)


def setup_style():
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
        "legend.fontsize": 8.6,
        "savefig.dpi": 240,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.06,
        "font.size": 9.6,
        "axes.titlesize": 10.4,
        "axes.labelsize": 9.8,
        "xtick.labelsize": 8.6,
        "ytick.labelsize": 8.6,
        "lines.solid_capstyle": "round",
        "lines.solid_joinstyle": "round",
    })


def save(fig, name):
    fig.savefig(FIG / name)
    plt.close(fig)


def col(hist, key):
    arr = np.asarray(hist[key])
    return arr[:, 0] if arr.ndim > 1 else arr


def med(rows, pred, key):
    vals = [r[key] for r in rows if pred(r)]
    return float(np.median(vals)) if vals else np.nan


def qtile(vals, q):
    return float(np.quantile(vals, q)) if len(vals) else np.nan


def ink_or_white(val, vmin, vmax, cmap):
    t = np.clip((val - vmin) / (vmax - vmin + 1e-12), 0, 1)
    r, g, b = to_rgb(cmap(t))
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    return INK if lum > 0.55 else "white"


def heatmap(ax, grid, rows, cols, vmin, vmax, cmap, fmt="{:+.2f}"):
    ax.grid(False)
    ny, nx = grid.shape
    im = ax.imshow(
        grid, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto",
        interpolation="nearest", rasterized=False,
    )
    ax.set_xticks(range(nx), cols)
    ax.set_yticks(range(ny), rows)
    ax.set_xticks(np.arange(-0.5, nx, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, ny, 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=1.15, zorder=3)
    ax.tick_params(which="minor", bottom=False, left=False, length=0)
    ax.set_xlim(-0.5, nx - 0.5)
    ax.set_ylim(ny - 0.5, -0.5)
    for sp in ax.spines.values():
        sp.set_visible(True)
        sp.set_linewidth(0.7)
        sp.set_color(INK)
    fs = 8.8 if max(nx, ny) >= 4 else 9.4
    for i in range(ny):
        for j in range(nx):
            ax.text(
                j, i, fmt.format(grid[i, j]), ha="center", va="center",
                color=ink_or_white(grid[i, j], vmin, vmax, cmap),
                fontsize=fs, zorder=4,
            )
    return im


def slim_cbar(fig, im, ax, label):
    cb = fig.colorbar(im, ax=ax, fraction=0.034, pad=0.014, shrink=0.88)
    cb.set_label(label, fontsize=8.8)
    cb.outline.set_linewidth(0.55)
    cb.ax.tick_params(length=2.0, width=0.55, labelsize=7.8)
    return cb


def line_kw(color, ms=5.0, lw=1.45):
    return dict(
        color=color, lw=lw, marker="o", ms=ms,
        markerfacecolor=color, markeredgecolor="white",
        markeredgewidth=0.9, zorder=3, solid_capstyle="round",
    )


def run_one(**kw):
    defaults = dict(
        proto=np.array([0]), t0=np.array([8.0]), m0=np.array([0.72]),
        hetero=np.array([0]), seed=np.array([7]), policy="dual",
        minutes=55.0, dt=2.0, record_every=4, store_history=True, cook="combi",
        length=np.array([0.03]),
    )
    defaults.update(kw)
    return rollout(**defaults)


def extra_rollouts():
    out = {}
    print("extra: grid n")
    grid = []
    for n in (8, 12, 16, 24, 32):
        h = run_one(n=n, store_history=True)
        t = col(h, "time")
        k1680 = int(np.argmin(np.abs(t - 1680.0)))
        rec = {
            "n": n,
            "e_alpha": float(h["e_alpha"][0]),
            "stop_s": float(h["stop"][0]),
            "energy": float(h["energy"][0]),
            "alpha_end": float(h["alpha_end"][0]),
            "t_core_1680": float(col(h, "t_core")[k1680]),
            "t_surf_1680": float(col(h, "t_surf")[k1680]),
            "alpha_1680": float(col(h, "alpha_m")[k1680]),
            "var_end": float(h["final_var"][0]),
        }
        grid.append(rec)
        out[f"grid_{n}"] = h
    out["grid_rows"] = grid

    print("extra: four policies")
    for p in ("open", "pid", "mpc", "dual"):
        out[f"pol_{p}"] = run_one(policy=p)

    print("extra: thickness")
    for L in (15, 30, 50):
        out[f"L_{L}"] = run_one(length=np.array([L / 1000.0]))

    print("extra: cook")
    for c in ("steam", "bake", "combi"):
        out[f"cook_{c}"] = run_one(cook=c)

    print("extra: moisture")
    for m0 in (0.64, 0.72, 0.80):
        out[f"m_{m0}"] = run_one(m0=np.array([m0]))

    print("extra: 50 mm 70 min")
    out["L50_70"] = run_one(length=np.array([0.05]), minutes=70.0)
    out["L50_55"] = out["L_50"]
    return out


def dump_stats(s1, study, s0, s2, wide, ens, extra):
    stats = {"kind": "campaign-log and extra-rollout summaries"}

    def pack(rows, key="e_alpha"):
        v = np.array([r[key] for r in rows], float)
        return {
            "n": int(len(v)),
            "p10": round(qtile(v, 0.1), 4),
            "p50": round(qtile(v, 0.5), 4),
            "p90": round(qtile(v, 0.9), 4),
            "mean": round(float(np.mean(v)), 4),
        }

    s1_pol = {}
    for p in ("open", "pid", "mpc", "dual"):
        sub = [r for r in s1 if r["policy"] == p]
        s1_pol[p] = {
            "e": pack(sub, "e_alpha"),
            "energy": pack(sub, "energy"),
            "stop": pack(sub, "stop_s"),
            "under": round(float(np.mean([r["e_alpha"] < 0 for r in sub])), 4),
        }
        by_L = {}
        for L in (15, 30, 50):
            sl = [r for r in sub if r["length_mm"] == L]
            by_L[str(L)] = {
                "e50": round(med(sl, lambda r: True, "e_alpha"), 4),
                "under": round(float(np.mean([r["e_alpha"] < 0 for r in sl])), 4),
                "E50": round(med(sl, lambda r: True, "energy"), 1),
                "t50": round(med(sl, lambda r: True, "stop_s"), 1),
            }
        s1_pol[p]["by_length"] = by_L
    stats["s1_policy"] = s1_pol

    s1_food = {}
    for food in ("mince", "potato", "dough"):
        sub = [r for r in s1 if r["food"] == food and r["policy"] == "dual"]
        s1_food[food] = pack(sub)
    stats["s1_dual_food"] = s1_food

    s1_t0 = {}
    for t0 in (5.0, 20.0):
        sub = [r for r in s1 if r["t0"] == t0 and r["policy"] == "dual"]
        s1_t0[str(t0)] = pack(sub)
    stats["s1_dual_t0"] = s1_t0

    s1_m0 = {}
    for m0 in (0.64, 0.72, 0.80):
        sub = [r for r in s1 if abs(r["m0"] - m0) < 1e-9 and r["policy"] == "dual"]
        s1_m0[str(m0)] = pack(sub)
    stats["s1_dual_m0"] = s1_m0

    s1_het = {}
    for h in (0, 1, 2):
        sub = [r for r in s1 if r["hetero"] == h and r["policy"] == "dual"]
        s1_het[str(h)] = pack(sub)
    stats["s1_dual_hetero"] = s1_het

    study_cross = {}
    for p in ("open", "pid", "mpc", "dual"):
        study_cross[p] = {}
        for c in ("steam", "bake", "combi"):
            sub = [r for r in study if r["policy"] == p and r["cook"] == c]
            study_cross[p][c] = {
                "e50": round(med(sub, lambda r: True, "e_alpha"), 4),
                "E50": round(med(sub, lambda r: True, "energy"), 1),
                "under": round(float(np.mean([r["e_alpha"] < 0 for r in sub])), 4),
            }
    stats["study_cross"] = study_cross

    s2_fac = defaultdict(lambda: defaultdict(list))
    for r in s2:
        s2_fac[r["factor"]][str(r["level"])].append(r["e_alpha"])
    stats["s2"] = {
        f: {lv: {
            "p50": round(float(np.median(vs)), 4),
            "p10": round(qtile(vs, 0.1), 4),
            "p90": round(qtile(vs, 0.9), 4),
            "n": len(vs),
        } for lv, vs in levels.items()}
        for f, levels in s2_fac.items()
    }

    stats["s0"] = [
        {"food": r["food"], "seed": r["seed"], "e16": r["e16"], "e8": r["e8"],
         "delta_e": r["delta_e"], "stop16": r["stop16"], "stop8": r["stop8"]}
        for r in s0
    ]
    stats["s0_delta_p50"] = round(float(np.median([r["delta_e"] for r in s0])), 4)

    stats["ensemble"] = ens
    stats["wide_n"] = len(wide)
    stats["grid_rows"] = extra["grid_rows"]
    extra_sum = {}
    for key, h in extra.items():
        if key in ("grid_rows",) or not isinstance(h, dict) or "e_alpha" not in h:
            continue
        extra_sum[key] = {
            "e_alpha": round(float(h["e_alpha"][0]), 4),
            "stop_s": round(float(h["stop"][0]), 1),
            "energy": round(float(h["energy"][0]), 1),
            "alpha_end": round(float(h["alpha_end"][0]), 4),
            "var_end": round(float(h["final_var"][0]), 4),
        }
    stats["extra"] = extra_sum
    (LOG / "expansion_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return stats


def draw_s1_heatmap(s1):
    pols = ("open", "pid", "mpc", "dual")
    Ls = (15, 30, 50)
    grid = np.zeros((4, 3))
    for i, p in enumerate(pols):
        for j, L in enumerate(Ls):
            grid[i, j] = med(
                s1, lambda r, p=p, L=L: r["policy"] == p and r["length_mm"] == L, "e_alpha"
            )
    fig, ax = plt.subplots(figsize=(5.35, 3.25))
    im = heatmap(
        ax, grid, [POL_N[p] for p in pols], [f"{L} mm" for L in Ls],
        -0.9, 0.16, DIVERGE, fmt="{:+.3f}",
    )
    slim_cbar(fig, im, ax, r"中位进度偏差 $e_\alpha$")
    save(fig, "X_s1_heat_policy_thick.png")


def draw_s1_violin(s1):
    pols = ("open", "pid", "mpc", "dual")
    data = [[r["e_alpha"] for r in s1 if r["policy"] == p] for p in pols]
    fig, ax = plt.subplots(figsize=(5.85, 3.25))
    parts = ax.violinplot(data, showmedians=True, showextrema=False, widths=0.82)
    for body, p in zip(parts["bodies"], pols):
        body.set_facecolor(POL_C[p])
        body.set_alpha(0.55)
        body.set_edgecolor(INK)
    parts["cmedians"].set_color(INK)
    ax.axhline(0, color=MUTED, lw=0.8, ls="--")
    ax.set_xticks(range(1, 5), [POL_N[p] for p in pols])
    ax.set_ylabel(r"$e_\alpha$")
    ax.set_title("")
    save(fig, "X_s1_violin.png")


def draw_s1_ecdf(s1):
    fig, ax = plt.subplots(figsize=(5.85, 3.25))
    for p in ("open", "pid", "mpc", "dual"):
        v = np.sort([r["e_alpha"] for r in s1 if r["policy"] == p])
        y = np.linspace(0, 1, len(v), endpoint=True)
        ax.plot(v, y, color=POL_C[p], lw=1.45, label=POL_N[p], solid_capstyle="round")
    ax.axvline(0, color=MUTED, lw=0.8, ls="--", zorder=0)
    ax.annotate(
        r"设计线 $e_\alpha=0$", xy=(0, 0.18), xytext=(0.12, 0.18),
        fontsize=8.4, color=MUTED,
        arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6),
    )
    ax.set_xlabel(r"$e_\alpha$")
    ax.set_ylabel("经验分布")
    ax.legend(loc="upper left", fontsize=8.4, frameon=False)
    ax.set_title("")
    save(fig, "X_s1_ecdf.png")


def draw_s1_pareto(s1):
    fig, ax = plt.subplots(figsize=(5.85, 3.40))
    rng = np.random.default_rng(7)
    for p in ("open", "pid", "mpc", "dual"):
        sub = [r for r in s1 if r["policy"] == p]
        idx = rng.choice(len(sub), size=min(900, len(sub)), replace=False)
        e = [sub[i]["e_alpha"] for i in idx]
        E = [sub[i]["energy"] for i in idx]
        ax.scatter(E, e, s=8, alpha=0.28, color=POL_C[p], label=POL_N[p], linewidths=0)
    ax.axhline(0, color=MUTED, lw=0.8, ls="--")
    ax.set_xlabel("累计加热")
    ax.set_ylabel(r"$e_\alpha$")
    ax.legend(markerscale=2.4, loc="lower right", fontsize=8.4, frameon=False)
    ax.set_title("")
    save(fig, "X_s1_pareto.png")


def draw_s1_factors(s1):
    fig, axes = plt.subplots(1, 3, figsize=(8.6, 3.15), sharey=True)
    dual = [r for r in s1 if r["policy"] == "dual"]
    # food
    foods = ("mince", "potato", "dough")
    data = [[r["e_alpha"] for r in dual if r["food"] == f] for f in foods]
    axes[0].boxplot(data, tick_labels=[FOOD_N[f] for f in foods], showfliers=False,
                    medianprops=dict(color=HEAT, lw=1.5), boxprops=dict(color=INK))
    axes[0].axhline(0, color=MUTED, lw=0.7, ls="--")
    axes[0].set_title("食品")
    axes[0].set_ylabel(r"$e_\alpha$")
    # t0
    t0s = (5.0, 20.0)
    data = [[r["e_alpha"] for r in dual if r["t0"] == t] for t in t0s]
    axes[1].boxplot(data, tick_labels=[r"$5^\circ$C", r"$20^\circ$C"], showfliers=False,
                    medianprops=dict(color=HEAT, lw=1.5), boxprops=dict(color=INK))
    axes[1].axhline(0, color=MUTED, lw=0.7, ls="--")
    axes[1].set_title("初温")
    # m0
    m0s = (0.64, 0.72, 0.80)
    data = [[r["e_alpha"] for r in dual if abs(r["m0"] - m) < 1e-9] for m in m0s]
    axes[2].boxplot(data, tick_labels=["0.64", "0.72", "0.80"], showfliers=False,
                    medianprops=dict(color=HEAT, lw=1.5), boxprops=dict(color=INK))
    axes[2].axhline(0, color=MUTED, lw=0.7, ls="--")
    axes[2].set_title("初始含水")
    fig.tight_layout()
    save(fig, "X_s1_factors.png")


def draw_s1_hetero(s1):
    fig, ax = plt.subplots(figsize=(5.35, 3.15))
    names = {0: "均匀", 1: "厚度抖动", 2: "脂肪层"}
    for h, color in zip((0, 1, 2), (SAGE, GOLD, HEAT)):
        ys = [
            med(s1, lambda r, h=h, L=L: r["policy"] == "dual" and r["hetero"] == h and r["length_mm"] == L, "e_alpha")
            for L in (15, 30, 50)
        ]
        ax.plot([15, 30, 50], ys, label=names[h], **line_kw(color))
    ax.axhline(0, color=MUTED, lw=0.8, ls="--")
    ax.set_xlabel("厚度 / mm")
    ax.set_ylabel(r"中位 $e_\alpha$")
    ax.legend(loc="lower left", fontsize=8.4, frameon=False)
    save(fig, "X_s1_hetero.png")


def draw_s1_under_bars(s1):
    fig, ax = plt.subplots(figsize=(5.55, 3.25))
    x = np.arange(3)
    w = 0.18
    Ls = (15, 30, 50)
    for i, p in enumerate(("open", "pid", "mpc", "dual")):
        ys = []
        for L in Ls:
            sl = [r for r in s1 if r["policy"] == p and r["length_mm"] == L]
            ys.append(float(np.mean([r["e_alpha"] < 0 for r in sl])))
        ax.bar(x + (i - 1.5) * w, ys, width=w, color=POL_C[p], label=POL_N[p], edgecolor=INK, lw=0.4)
    ax.set_xticks(x, [f"{L} mm" for L in Ls])
    ax.set_ylabel(r"$P(e_\alpha<0)$")
    ax.set_ylim(0, 1.08)
    ax.legend(
        ncol=2, loc="lower center", bbox_to_anchor=(0.5, 1.02),
        fontsize=8.2, frameon=True, fancybox=False, edgecolor=LINE,
        framealpha=0.92, columnspacing=1.05, handlelength=1.4,
    )
    ax.set_title("")
    fig.subplots_adjust(top=0.82)
    save(fig, "X_s1_under.png")


def draw_study_facet(study):
    fig, axes = plt.subplots(1, 3, figsize=(9.8, 3.5), sharey=True)
    for ax, c in zip(axes, ("steam", "bake", "combi")):
        for p in ("open", "pid", "mpc", "dual"):
            ys = [
                med(study, lambda r, p=p, c=c, L=L: r["policy"] == p and r["cook"] == c and r["length_mm"] == L, "e_alpha")
                for L in (15, 30, 50)
            ]
            ax.plot([15, 30, 50], ys, label=POL_N[p], **line_kw(POL_C[p], ms=4.6, lw=1.35))
        ax.axhline(0, color=MUTED, lw=0.7, ls="--")
        ax.set_title(COOK_N[c])
        ax.set_xlabel("厚度 / mm")
    axes[0].set_ylabel(r"中位 $e_\alpha$")
    axes[2].legend(fontsize=8)
    save(fig, "X_study_facet.png")


def draw_study_t0_m0(study):
    dual = [r for r in study if r["policy"] == "dual" and r["cook"] == "combi"]
    t0s = sorted({r["t0"] for r in dual})
    m0s = sorted({r["m0"] for r in dual})
    grid = np.zeros((len(t0s), len(m0s)))
    for i, t0 in enumerate(t0s):
        for j, m0 in enumerate(m0s):
            grid[i, j] = med(dual, lambda r, t0=t0, m0=m0: r["t0"] == t0 and abs(r["m0"] - m0) < 1e-9, "e_alpha")
    fig, ax = plt.subplots(figsize=(5.15, 3.15))
    im = heatmap(
        ax, grid, [f"{t:.0f} °C" for t in t0s], [f"{m:.2f}" for m in m0s],
        -0.9, 0.16, DIVERGE,
    )
    ax.set_xlabel("初始含水")
    ax.set_ylabel("初温")
    slim_cbar(fig, im, ax, r"中位 $e_\alpha$")
    save(fig, "X_study_t0m0.png")


def draw_s0(s0):
    fig, ax = plt.subplots(figsize=(5.35, 3.15))
    markers = {"mince": "o", "potato": "s", "dough": "D"}
    for food in ("mince", "potato", "dough"):
        sub = [r for r in s0 if r["food"] == food]
        ax.scatter([r["e16"] for r in sub], [r["e8"] for r in sub],
                   marker=markers[food], color={"mince": HEAT, "potato": STEAM, "dough": SAGE}[food],
                   s=42, label=FOOD_N[food], edgecolor=INK, lw=0.4)
    lim = [-0.18, 0.14]
    ax.plot(lim, lim, color=MUTED, lw=0.8, ls="--")
    ax.set_xlabel(r"16 控制体 $e_\alpha$")
    ax.set_ylabel(r"8 控制体 $e_\alpha$")
    ax.legend(loc="lower right", fontsize=8.4, frameon=False)
    ax.set_title("")
    save(fig, "X_s0_pair.png")

    fig, ax = plt.subplots(figsize=(5.35, 3.15))
    foods = ("mince", "potato", "dough")
    data = [[r["delta_e"] for r in s0 if r["food"] == f] for f in foods]
    ax.boxplot(data, tick_labels=[FOOD_N[f] for f in foods], showfliers=False,
               medianprops=dict(color=HEAT, lw=1.6), boxprops=dict(color=INK))
    ax.set_ylabel(r"$e_8-e_{16}$")
    ax.set_title("")
    save(fig, "X_s0_delta.png")


def draw_s2(s2):
    # probe
    fig, ax = plt.subplots(figsize=(5.35, 3.15))
    data = [
        [r["e_alpha"] for r in s2 if r["factor"] == "probe" and r["level"] == lv]
        for lv in ("dual", "mpc")
    ]
    vp = ax.violinplot(data, showmedians=True, showextrema=False)
    for body, c in zip(vp["bodies"], (NAVY, STEAM)):
        body.set_facecolor(c)
        body.set_alpha(0.55)
    vp["cmedians"].set_color(INK)
    ax.set_xticks([1, 2], ["对偶探针", "无探针"])
    ax.set_ylabel(r"$e_\alpha$")
    ax.set_title("")
    save(fig, "X_s2_probe.png")

    fig, ax = plt.subplots(figsize=(5.45, 3.20))
    levels = ("0", "15", "30", "60")
    xs = [int(lv) for lv in levels]
    p50, p10, p90, stops = [], [], [], []
    for lv in levels:
        sub = [r for r in s2 if r["factor"] == "occlude" and r["level"] == lv]
        v = np.array([r["e_alpha"] for r in sub])
        p50.append(float(np.median(v)))
        p10.append(float(np.quantile(v, 0.1)))
        p90.append(float(np.quantile(v, 0.9)))
        stops.append(float(np.median([r["stop_s"] for r in sub])))
    ax.plot(xs, p50, label=r"$e_\alpha$ 中位", **line_kw(STEAM, ms=5.4, lw=1.5))
    ax.plot(xs, p10, color=STEAM, marker="v", ms=4.4, lw=0.9, ls=":",
            markerfacecolor=STEAM, markeredgecolor="white", markeredgewidth=0.7, label="十分位")
    ax.plot(xs, p90, color=STEAM, marker="^", ms=4.4, lw=0.9, ls=":",
            markerfacecolor=STEAM, markeredgecolor="white", markeredgewidth=0.7, label="九十分位")
    ax2 = ax.twinx()
    ax2.spines["right"].set_visible(True)
    ax2.plot(xs, np.array(stops) / 60.0, color=HEAT, marker="s", ms=4.8, lw=1.35, ls="--",
             markerfacecolor=HEAT, markeredgecolor="white", markeredgewidth=0.7, label="停机中位")
    ax.set_xticks(xs, [f"{x} s" for x in xs])
    ax.set_xlabel("开局保持表面读数的时长 / s")
    ax.set_ylabel(r"$e_\alpha$")
    ax2.set_ylabel("停机 / min")
    ax.set_ylim(-0.18, -0.02)
    lo, hi = min(stops) / 60.0, max(stops) / 60.0
    ax2.set_ylim(lo - 0.08, hi + 0.08)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8.2)
    ax.set_title("")
    save(fig, "X_s2_occlude.png")

    fig, axes = plt.subplots(1, 3, figsize=(8.6, 3.15), sharey=True)
    specs = [
        ("fat", ("off", "on"), ("关", "开"), "脂肪层"),
        ("door", ("closed", "at300"), ("关闭", "300 s 开门"), "门"),
        ("mass", ("on", "off"), ("开", "关"), "质量通道"),
    ]
    for ax, (fac, lvs, labs, title) in zip(axes, specs):
        data = [[r["e_alpha"] for r in s2 if r["factor"] == fac and r["level"] == lv] for lv in lvs]
        ax.boxplot(data, tick_labels=labs, showfliers=False,
                   medianprops=dict(color=HEAT, lw=1.5), boxprops=dict(color=INK))
        ax.axhline(0, color=MUTED, lw=0.6, ls="--")
        ax.set_title(title)
    axes[0].set_ylabel(r"$e_\alpha$")
    fig.tight_layout()
    save(fig, "X_s2_three.png")

    base = float(np.median([r["e_alpha"] for r in s2 if r["factor"] == "probe" and r["level"] == "dual"]))
    labels = ["无探针", "脂肪夹层", "300 s 开门", "读数保持 60 s", "质量通道关"]
    picks = [
        ("probe", "mpc"), ("fat", "on"), ("door", "at300"), ("occlude", "60"), ("mass", "off"),
    ]
    vals = []
    for fac, lv in picks:
        m = float(np.median([r["e_alpha"] for r in s2 if r["factor"] == fac and r["level"] == lv]))
        vals.append(m - base)
    order = np.argsort(vals)
    labels = [labels[i] for i in order]
    vals = [vals[i] for i in order]
    fig, ax = plt.subplots(figsize=(5.55, 3.20))
    colors = [HEAT if v < 0 else SAGE for v in vals]
    ax.barh(labels, vals, color=colors, edgecolor=INK, lw=0.45, height=0.62)
    ax.axvline(0, color=MUTED, lw=0.8, ls="--")
    for y, v in enumerate(vals):
        inside = abs(v) >= 0.08
        x = v / 2 if inside else v + (0.012 if v >= 0 else -0.012)
        ax.text(
            x, y, f"{v:+.3f}",
            ha="center" if inside else ("left" if v >= 0 else "right"),
            va="center", fontsize=9.0,
            color="white" if inside and v < 0 else INK,
        )
    lo, hi = min(vals), max(vals)
    ax.set_xlim(lo - 0.04, hi + 0.08)
    ax.set_xlabel(r"相对对偶基线的中位 $\Delta e_\alpha$")
    ax.set_title("")
    save(fig, "X_s2_radar.png")


def draw_ensemble(ens):
    rows = ens["rows"] if isinstance(ens, dict) else ens
    fig, ax = plt.subplots(figsize=(5.45, 3.20))
    for members, marker in ((32, "o"), (128, "s")):
        sub = [r for r in rows if r["members"] == members]
        ax.scatter(
            [r["length_mm"] for r in sub],
            [r["spread_max"] for r in sub],
            c=[HEAT if r["hetero"] == 2 else STEAM for r in sub],
            marker=marker, s=64, edgecolor=INK, lw=0.4,
            label=f"{members} 成员",
        )
    ax.set_xlabel("厚度 / mm")
    ax.set_ylabel("成员最大散布")
    ax.legend()
    ax.set_title("")
    save(fig, "X_ens_spread.png")

    fig, ax = plt.subplots(figsize=(5.45, 3.20))
    width = 0.36
    xs = np.arange(6)
    labels = []
    e50 = []
    e10 = []
    e90 = []
    for L in (15, 30, 50):
        for h in (0, 2):
            r = next(x for x in rows if x["members"] == 32 and x["length_mm"] == L and x["hetero"] == h)
            labels.append(f"{int(L)}\n{'脂肪' if h else '均匀'}")
            e50.append(r["e50"])
            e10.append(r["e10"])
            e90.append(r["e90"])
    ax.bar(xs, e50, width=width, color=NAVY, edgecolor=INK, lw=0.4)
    ax.vlines(xs, e10, e90, color=INK, lw=1.2)
    ax.axhline(0, color=MUTED, lw=0.7, ls="--")
    ax.set_xticks(xs, labels, fontsize=8.5)
    ax.set_ylabel(r"$e_\alpha$ 分位")
    ax.set_title("")
    save(fig, "X_ens_quantile.png")


def draw_wide(wide):
    pols = ("open", "pid", "mpc", "dual")
    Ls = (15.0, 30.0, 50.0)
    grid = np.zeros((4, 3))
    under = np.zeros((4, 3))
    for i, p in enumerate(pols):
        for j, L in enumerate(Ls):
            sub = [r for r in wide if r["policy"] == p and r["length_mm"] == L]
            grid[i, j] = float(np.median([r["e50"] for r in sub]))
            under[i, j] = float(np.median([r["under"] for r in sub]))
    fig, ax = plt.subplots(figsize=(5.35, 3.25))
    im = heatmap(
        ax, grid, [POL_N[p] for p in pols], ["15 mm", "30 mm", "50 mm"],
        -0.9, 0.16, DIVERGE,
    )
    slim_cbar(fig, im, ax, r"格子中位 $e_{50}$")
    save(fig, "X_wide_heat.png")

    fig, ax = plt.subplots(figsize=(5.35, 3.15))
    for p in pols:
        sub = [r for r in wide if r["policy"] == p]
        byL = []
        lo = []
        hi = []
        for L in Ls:
            sl = [r for r in sub if r["length_mm"] == L]
            byL.append(float(np.median([r["e50"] for r in sl])))
            lo.append(float(np.median([r["e10"] for r in sl])))
            hi.append(float(np.median([r["e90"] for r in sl])))
        ax.fill_between(Ls, lo, hi, color=POL_C[p], alpha=0.16)
        ax.plot(Ls, byL, label=POL_N[p], **line_kw(POL_C[p]))
    ax.axhline(0, color=MUTED, lw=0.8, ls="--")
    ax.set_xlabel("厚度 / mm")
    ax.set_ylabel(r"$e_{10}$–$e_{50}$–$e_{90}$")
    ax.legend(fontsize=8.2)
    save(fig, "X_wide_band.png")

    fig, ax = plt.subplots(figsize=(5.35, 3.25))
    im = heatmap(
        ax, under, [POL_N[p] for p in pols], ["15 mm", "30 mm", "50 mm"],
        0, 1, plt.cm.YlOrBr, fmt="{:.2f}",
    )
    slim_cbar(fig, im, ax, "格子未达比例的中位")
    save(fig, "X_wide_under.png")


def reconstruct_section_field(nx=24, nz=16, fat=False):
    from acts_mcdt.physics import K_BASE

    length = 0.030
    height = 0.080
    minutes = 20.0
    dt = 0.25
    steps = int(minutes * 60.0 / dt)
    dx = length / nx
    dz = height / nz
    alpha = K_BASE / 3.4e6
    field_alpha = np.full((nz, nx), alpha)
    if fat:
        field_alpha[:, nx // 3] = 0.45 * alpha
    temp = np.full((nz, nx), 8.0)
    for _ in range(steps):
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
    return temp


def draw_t2_t3(t2, t3):
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    for r, color, lab in zip(t2["rows"], (STEAM, HEAT), ("无脂肪层", "脂肪层")):
        ax.plot(np.array(r["times_s"]) / 60.0, r["core_c"], color=color, lw=1.9, label=lab)
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("截面冷点 / °C")
    ax.legend(loc="lower right")
    ax.set_title("")
    save(fig, "X_t2_core.png")

    r0 = t2["rows"][0]
    field = reconstruct_section_field(r0["nx"], r0["nz"], fat=False)
    fig, ax = plt.subplots(figsize=(5.55, 3.25))
    ax.grid(False)
    ax.spines["top"].set_visible(True)
    ax.spines["right"].set_visible(True)
    im = ax.imshow(
        field, origin="lower", aspect="auto", cmap=HEATMAP,
        vmin=8, vmax=130, interpolation="nearest",
        extent=(-0.5, r0["nx"] - 0.5, -0.5, r0["nz"] - 0.5),
    )
    cold = r0["cold_depth_index"]
    center = r0["center_index"]
    ax.axvline(center, color=HEAT, ls="--", lw=1.1, label="几何中心")
    ax.axvline(cold, color=STEAM, ls="-", lw=1.3, label="冷列")
    ax.set_xlabel("深度索引（表面 → 对称面）")
    ax.set_ylabel("横向索引")
    ax.set_title("")
    ax.legend(loc="upper left", fontsize=8.4)
    slim_cbar(fig, im, ax, "温度 / °C")
    save(fig, "X_t2_grid.png")

    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    u = [r["speed_m_s"] for r in t3["rows"]]
    h = [r["h_W_m2K"] for r in t3["rows"]]
    ax.plot(u, h, **line_kw(STEAM, ms=4.8, lw=1.45))
    ax.set_xlabel(r"通道风速 / m·s$^{-1}$")
    ax.set_ylabel(r"$h$ / W·m$^{-2}$·K$^{-1}$")
    ax.set_title("")
    save(fig, "X_t3_h.png")


def draw_antoine_shell(ant, shell):
    fig, ax = plt.subplots(figsize=(5.35, 3.15))
    for L, color in zip((15, 30, 50), (STEAM, GOLD, HEAT)):
        on = [r["e_alpha"] for r in ant if r["length_mm"] == L and r["antoine"]]
        off = [r["e_alpha"] for r in ant if r["length_mm"] == L and not r["antoine"]]
        d = np.array(on) - np.array(off)
        ax.scatter(np.full_like(d, L) + np.linspace(-1.2, 1.2, len(d)), d,
                   color=color, s=22, alpha=0.75, label=f"{L} mm", linewidths=0)
    ax.axhline(0, color=MUTED, lw=0.8, ls="--")
    ax.set_xlabel("厚度 / mm")
    ax.set_ylabel(r"$\Delta e_\alpha$（开 − 关）")
    ax.legend(fontsize=8.2, loc="upper right")
    ax.set_title("")
    save(fig, "X_ant_delta.png")

    fig, ax = plt.subplots(figsize=(5.35, 3.15))
    factors = sorted({r["factor"] for r in shell})
    for L, color in zip((15, 30, 50), (STEAM, GOLD, HEAT)):
        ys = [med(shell, lambda r, f=f, L=L: r["factor"] == f and r["length_mm"] == L, "e_alpha") for f in factors]
        ax.plot(factors, ys, label=f"{L} mm", **line_kw(color, ms=4.8, lw=1.4))
    ax.axhline(0, color=MUTED, lw=0.8, ls="--")
    ax.set_xlabel("结壳导热乘子")
    ax.set_ylabel(r"中位 $e_\alpha$")
    ax.legend()
    ax.set_title("")
    save(fig, "X_shell.png")


def draw_extra_traces(extra):
    fig, axes = plt.subplots(3, 1, figsize=(6.8, 7.2), sharex=True)
    for p in ("open", "pid", "mpc", "dual"):
        h = extra[f"pol_{p}"]
        t = col(h, "time") / 60.0
        axes[0].plot(t, col(h, "t_core"), color=POL_C[p], lw=1.7, label=POL_N[p])
        axes[1].plot(t, col(h, "alpha_m"), color=POL_C[p], lw=1.7)
        axes[2].plot(t, col(h, "heat"), color=POL_C[p], lw=1.4)
    axes[1].axhline(0.85, color=MUTED, ls="--", lw=0.8)
    axes[0].set_ylabel("冷点 / °C")
    axes[1].set_ylabel(r"$\alpha_m$")
    axes[2].set_ylabel("加热指令")
    axes[2].set_xlabel("时间 / min")
    axes[0].legend(ncol=4, fontsize=8, loc="lower right")
    axes[0].set_title("")
    save(fig, "X_trace_policy.png")

    fig, axes = plt.subplots(2, 1, figsize=(6.6, 5.4), sharex=True)
    for L, color in zip((15, 30, 50), (STEAM, GOLD, HEAT)):
        h = extra[f"L_{L}"]
        t = col(h, "time") / 60.0
        axes[0].plot(t, col(h, "t_core"), color=color, lw=1.8, label=f"{L} mm")
        axes[0].plot(t, col(h, "t_surf"), color=color, lw=1.0, ls=":")
        axes[1].plot(t, col(h, "alpha_m"), color=color, lw=1.8)
    axes[1].axhline(0.85, color=MUTED, ls="--", lw=0.8)
    axes[0].set_ylabel("温度 / °C")
    axes[1].set_ylabel(r"$\alpha_m$")
    axes[1].set_xlabel("时间 / min")
    axes[0].legend()
    axes[0].set_title("")
    save(fig, "X_trace_thick.png")

    fig, axes = plt.subplots(2, 1, figsize=(6.6, 5.4), sharex=True)
    for c in ("steam", "bake", "combi"):
        h = extra[f"cook_{c}"]
        t = col(h, "time") / 60.0
        axes[0].plot(t, col(h, "t_core"), color=COOK_C[c], lw=1.8, label=COOK_N[c])
        axes[1].plot(t, col(h, "steam"), color=COOK_C[c], lw=1.5)
    axes[0].set_ylabel("冷点 / °C")
    axes[1].set_ylabel("蒸汽指令")
    axes[1].set_xlabel("时间 / min")
    axes[0].legend()
    axes[0].set_title("")
    save(fig, "X_trace_cook.png")

    fig, ax = plt.subplots(figsize=(6.4, 3.7))
    ns = [r["n"] for r in extra["grid_rows"]]
    es = [r["e_alpha"] for r in extra["grid_rows"]]
    cores = [r["t_core_1680"] for r in extra["grid_rows"]]
    ax.plot(ns, es, label=r"$e_\alpha$", **line_kw(NAVY, ms=5.2, lw=1.45))
    ax2 = ax.twinx()
    ax2.spines["right"].set_visible(True)
    ax2.plot(ns, cores, color=HEAT, marker="s", ms=4.8, lw=1.4, ls="--",
             markerfacecolor=HEAT, markeredgecolor="white", markeredgewidth=0.7, label=r"1680 s 冷点")
    ax.set_xlabel("控制体条数")
    ax.set_ylabel(r"$e_\alpha$")
    ax2.set_ylabel("冷点 / °C")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="center right")
    ax.set_title("")
    save(fig, "X_grid_n.png")

    fig, ax = plt.subplots(figsize=(6.4, 3.7))
    h55 = extra["L50_55"]
    h70 = extra["L50_70"]
    ax.plot(col(h55, "time") / 60.0, col(h55, "alpha_m"), color=HEAT, lw=1.8, label="55 min")
    ax.plot(col(h70, "time") / 60.0, col(h70, "alpha_m"), color=STEAM, lw=1.8, label="70 min")
    ax.axhline(0.85, color=MUTED, ls="--", lw=0.8)
    ax.set_xlabel("时间 / min")
    ax.set_ylabel(r"$\alpha_m$")
    ax.legend(fontsize=8.4, loc="upper left")
    ax.set_title("")
    save(fig, "X_L50_horizon.png")


def draw_fields(extra):
    h = extra["pol_dual"]
    t = col(h, "time") / 60.0
    surf = col(h, "t_surf")
    core = col(h, "t_core")
    n = 16
    depth = np.linspace(0.0, 30.0, n)
    field = np.zeros((len(t), n))
    for i, (s, c) in enumerate(zip(surf, core)):
        field[i] = s + (c - s) * (depth / 30.0) ** 1.15
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    im = ax.pcolormesh(t, depth, field.T, shading="auto", cmap=HEATMAP, vmin=5, vmax=170)
    ax.axvspan(150 / 60, 190 / 60, color=INK, alpha=0.08, lw=0)
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("距表面 / mm")
    ax.invert_yaxis()
    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.set_label("温度 / °C")
    ax.set_title("种子 7：厚度–时间温度场（阴影为探针窗）")
    save(fig, "X_field_xt.png")

    moist = col(h, "m_mean")
    fig, ax = plt.subplots(figsize=(6.6, 3.4))
    ax.plot(t, moist, color=STEAM, lw=1.9)
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("平均含水")
    ax.set_title("种子 7：平均含水随时间")
    save(fig, "X_moist.png")

    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    ax.plot(t, col(h, "path_a"), color=HEAT, lw=1.6, label="A 潜热")
    ax.plot(t, col(h, "path_b"), color=STEAM, lw=1.6, label="B 蒸发")
    ax.plot(t, col(h, "path_c"), color=GOLD, lw=1.6, label="C 结壳")
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("通量代理")
    ax.legend()
    ax.set_title("种子 7：路径 A/B/C 的显示量")
    save(fig, "X_paths_time.png")

    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    ax.plot(t, col(h, "cav_t"), color=HEAT, lw=1.7, label="腔温")
    ax.plot(t, col(h, "heater"), color=INK, lw=1.3, ls=":", label="加热器")
    ax.axhline(230, color=MUTED, ls="--", lw=0.8, label="削减阈值")
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("温度 / °C")
    ax.legend()
    ax.set_title("种子 7：腔温与加热器（阈值从未触发）")
    save(fig, "X_heater_cav.png")

    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    gap = col(h, "t_surf") - col(h, "t_core")
    ax.plot(t, gap, color=HEAT, lw=1.8)
    ax.axvspan(150 / 60, 190 / 60, color=STEAM, alpha=0.12, lw=0)
    ax.set_xlabel("时间 / min")
    ax.set_ylabel(r"$T_s-T_{\mathrm{cold}}$ / K")
    ax.set_title("种子 7：表面–冷点温差")
    save(fig, "X_gap.png")

    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    ax.plot(t, col(h, "alpha_m"), color=STEAM, lw=1.8, label=r"$\alpha_m$")
    ax.plot(t, col(h, "alpha_b"), color=HEAT, lw=1.8, label=r"$\alpha_b$")
    ax.axhline(0.85, color=MUTED, ls="--", lw=0.8)
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("进度")
    ax.legend()
    ax.set_title("种子 7：致死当量与褐变进度")
    save(fig, "X_alpha_mb.png")

    # 3d field
    idx = np.linspace(0, len(t) - 1, 40).astype(int)
    tt = t[idx]
    ss = surf[idx]
    cc = core[idx]
    depth3 = np.linspace(0.0, 30.0, 20)
    T, D = np.meshgrid(tt, depth3)
    Z = np.zeros_like(T)
    for j, (s, c) in enumerate(zip(ss, cc)):
        Z[:, j] = s + (c - s) * (depth3 / 30.0) ** 1.15
    fig = plt.figure(figsize=(7.0, 4.6))
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("white")
    surf_plot = ax.plot_surface(
        T, D, Z, cmap=HEATMAP, linewidth=0, antialiased=True,
        rstride=1, cstride=1, vmin=5, vmax=170, alpha=0.97,
    )
    ax.view_init(elev=24, azim=-62)
    ax.set_xlabel("时间 / min", labelpad=10)
    ax.set_ylabel("深度 / mm", labelpad=10)
    ax.zaxis.set_rotate_label(False)
    ax.set_zlabel("温度 / °C", labelpad=2, rotation=90)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.fill = False
        axis.pane.set_edgecolor(LINE)
    ax.tick_params(axis="z", pad=2)
    cb = fig.colorbar(surf_plot, ax=ax, shrink=0.52, pad=0.12, fraction=0.035)
    cb.set_label("温度 / °C")
    ax.set_title("种子 7 温度场的时间展开", pad=8)
    fig.subplots_adjust(left=0.02, right=0.86, bottom=0.08, top=0.90)
    save(fig, "X_field_3d.png")


def draw_mpc_operator(mpc, op):
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    tau = mpc["tau_s"]
    ax.axhline(mpc["predicted_core"], color=STEAM, ls="--", lw=0.9, label=f"搜索点预测 {mpc['predicted_core']:.2f} °C")
    ax.scatter([mpc["searched_heat"]], [mpc["predicted_core"]], color=HEAT, s=70, zorder=3, label="记下的搜索点")
    ax.axvline(mpc["saturated_heat"], color=MUTED, ls=":", lw=0.9, label="饱和加热 1.0")
    ax.set_xlim(-0.05, 1.05)
    ax.set_xlabel("加热指令")
    ax.set_ylabel("60 s 预测冷点 / °C")
    ax.legend(fontsize=8, loc="lower right")
    ax.set_title(fr"两节点 60 s 搜索（$\tau={tau:.0f}$ s，单状态）")
    save(fig, "X_mpc_horizon.png")

    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    labs = ["主干+分支", "仅主干", "蒸汽阶跃"]
    vals = [op["holdout_mse_both"], op["holdout_mse_trunk"], op["steam_step_mse"]]
    ax.bar(labs, vals, color=[NAVY, STEAM, HEAT], edgecolor=INK, lw=0.5)
    ax.set_ylabel("留出均方误差")
    ax.set_title(f"两节点教师（训练 {op['train']}，留出 {op['holdout']}，{op['epochs']} 轮）")
    save(fig, "X_operator.png")


def draw_bi_fo(extra=None):
    L = 0.03
    alpha = 2.0e-7
    k = 0.68
    t = np.linspace(0.0, 3300.0, 400)
    Fo = alpha * t / (L ** 2)
    fan = np.linspace(0.0, 1.3, 80)
    hconv = 12.0 + 55.0 * fan
    Bi = hconv * L / k

    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.20))
    ax, axb = axes
    ax.plot(t / 60.0, Fo, color=NAVY, lw=1.55, solid_capstyle="round")
    ax.axvspan(150 / 60, 190 / 60, color=STEAM, alpha=0.16, lw=0)
    ax.scatter([40 / 60], [8.9e-3], color=STEAM, s=36, zorder=3)
    ax.scatter([1866 / 60], [alpha * 1866 / L**2], color=HEAT, s=36, zorder=3)
    ax.text(4.2, 0.06, "探针窗", color=STEAM, fontsize=8.4)
    ax.text(32.2, 0.46, "停机 1866 s", color=HEAT, fontsize=8.4)
    ax.set_xlabel("时间 / min")
    ax.set_ylabel(r"Fourier 数（$L=30\,\mathrm{mm}$）")
    ax.set_ylim(-0.02, 0.82)
    ax.set_title("")

    axb.plot(fan, Bi, color=HEAT, lw=1.55, solid_capstyle="round")
    for u, lab in ((0.4, "品质段 0.4"), (1.3, "探针段 1.3")):
        b = (12.0 + 55.0 * u) * L / k
        axb.scatter([u], [b], color=NAVY, s=38, zorder=3)
        axb.annotate(
            f"{lab}\nBi={b:.2f}",
            xy=(u, b),
            xytext=(u - 0.18, min(b + 0.55, 4.05)),
            fontsize=8.0,
            color=NAVY,
            ha="left",
        )
    axb.set_xlabel("风机指令")
    axb.set_ylabel("Biot 数")
    axb.set_xlim(-0.05, 1.4)
    axb.set_ylim(0.3, 4.4)
    axb.set_title("")
    save(fig, "X_fo_bi.png")


def draw_energy_stop(study):
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    rng = np.random.default_rng(3)
    for p in ("open", "pid", "mpc", "dual"):
        sub = [r for r in study if r["policy"] == p and r["cook"] == "combi"]
        idx = rng.choice(len(sub), size=min(500, len(sub)), replace=False)
        ax.scatter(
            [sub[i]["stop_s"] / 60.0 for i in idx],
            [sub[i]["energy"] for i in idx],
            s=10, alpha=0.3, color=POL_C[p], label=POL_N[p], linewidths=0,
        )
    ax.set_xlabel("停机 / min")
    ax.set_ylabel("累计加热")
    ax.legend(markerscale=2.2)
    ax.set_title("档位研究、组合档：停机时刻与能量")
    save(fig, "X_study_stop_energy.png")


def main():
    setup_style()
    print("loading logs")
    s1 = json.loads((LOG / "s1_summary.json").read_text(encoding="utf-8"))
    study = json.loads((LOG / "study.json").read_text(encoding="utf-8"))
    s0 = json.loads((LOG / "s0_summary.json").read_text(encoding="utf-8"))
    s2 = json.loads((LOG / "s2_summary.json").read_text(encoding="utf-8"))
    ens = json.loads((LOG / "ensemble.json").read_text(encoding="utf-8"))
    wide = [json.loads(line) for line in (LOG / "s1_wide.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    t2 = json.loads((LOG / "t2_section.json").read_text(encoding="utf-8"))
    t3 = json.loads((LOG / "t3_boundary.json").read_text(encoding="utf-8"))
    ant = json.loads((LOG / "antoine_pairs.json").read_text(encoding="utf-8"))
    shell = json.loads((LOG / "shell_scan.json").read_text(encoding="utf-8"))
    mpc = json.loads((LOG / "mpc_horizon.json").read_text(encoding="utf-8"))
    op = json.loads((LOG / "operators.json").read_text(encoding="utf-8"))

    extra = extra_rollouts()
    stats = dump_stats(s1, study, s0, s2, wide, ens, extra)
    print("stats written", LOG / "expansion_stats.json")
    print("grid", stats["grid_rows"])
    print("extra L50_70", stats["extra"].get("L50_70"))
    print("s2", json.dumps(stats["s2"], ensure_ascii=False)[:800])

    print("drawing")
    draw_s1_heatmap(s1)
    draw_s1_violin(s1)
    draw_s1_ecdf(s1)
    draw_s1_pareto(s1)
    draw_s1_factors(s1)
    draw_s1_hetero(s1)
    draw_s1_under_bars(s1)
    draw_study_facet(study)
    draw_study_t0_m0(study)
    draw_s0(s0)
    draw_s2(s2)
    draw_ensemble(ens)
    draw_wide(wide)
    draw_t2_t3(t2, t3)
    draw_antoine_shell(ant, shell)
    draw_extra_traces(extra)
    draw_fields(extra)
    draw_mpc_operator(mpc, op)
    draw_bi_fo(extra)
    draw_energy_stop(study)
    print("done", FIG)


def json_redraw():
    """Redraw campaign figures from logs; skip extra_rollouts()."""
    setup_style()
    s1 = json.loads((LOG / "s1_summary.json").read_text(encoding="utf-8"))
    s0 = json.loads((LOG / "s0_summary.json").read_text(encoding="utf-8"))
    s2 = json.loads((LOG / "s2_summary.json").read_text(encoding="utf-8"))
    wide = [json.loads(line) for line in (LOG / "s1_wide.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    ens = json.loads((LOG / "ensemble.json").read_text(encoding="utf-8"))
    ant = json.loads((LOG / "antoine_pairs.json").read_text(encoding="utf-8"))
    shell = json.loads((LOG / "shell_scan.json").read_text(encoding="utf-8"))
    draw_s1_heatmap(s1)
    draw_s1_violin(s1)
    draw_s1_ecdf(s1)
    draw_s1_pareto(s1)
    draw_s1_factors(s1)
    draw_s1_hetero(s1)
    draw_s1_under_bars(s1)
    draw_s0(s0)
    draw_s2(s2)
    draw_ensemble(ens)
    draw_wide(wide)
    draw_antoine_shell(ant, shell)
    draw_bi_fo()
    print("json redraw done", FIG)


if __name__ == "__main__":
    if "--fast" in sys.argv:
        setup_style()
        s2 = json.loads((LOG / "s2_summary.json").read_text(encoding="utf-8"))
        t2 = json.loads((LOG / "t2_section.json").read_text(encoding="utf-8"))
        t3 = json.loads((LOG / "t3_boundary.json").read_text(encoding="utf-8"))
        draw_s2(s2)
        draw_t2_t3(t2, t3)
        draw_bi_fo()
        print("fast redraw done", FIG)
    elif "--json" in sys.argv:
        json_redraw()
    else:
        main()
