# -*- coding: utf-8 -*-
"""Publication figures: restyle study plots, rebuild field views, draw schematics."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap, to_rgb
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, Arc, FancyArrowPatch
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from acts_mcdt.physics import rollout  # noqa: E402

FIG = ROOT / "results" / "figures" / "paper"
STUDY_FIG = ROOT / "results" / "figures" / "study"
FIG.mkdir(parents=True, exist_ok=True)

INK = "#1c1a17"
MUTED = "#5c564c"
HEAT = "#c45c26"
STEAM = "#2a6f7f"
NAVY = "#1f4e79"
SAGE = "#4a6b4e"
LINE = "#d9d2c5"
BG = "#fbf8f2"

HEATMAP = LinearSegmentedColormap.from_list(
    "acts_heat",
    ["#f4efe4", "#f0c27a", "#c45c26", "#6b1d12"],
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
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": LINE,
        "grid.linewidth": 0.6,
        "grid.alpha": 0.85,
        "legend.frameon": False,
        "legend.fontsize": 9.2,
        "savefig.dpi": 220,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.14,
        "font.size": 10.5,
        "axes.titlesize": 11.5,
        "axes.labelsize": 10.5,
        "xtick.labelsize": 9.4,
        "ytick.labelsize": 9.4,
        "figure.titlesize": 12,
    })


def ink_or_white(val, vmin, vmax, cmap):
    t = np.clip((val - vmin) / (vmax - vmin + 1e-12), 0, 1)
    r, g, b = to_rgb(cmap(t))
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    return INK if lum > 0.55 else "white"


def place_legend(ax, ncol=3, loc="lower center"):
    ax.legend(
        loc=loc, bbox_to_anchor=(0.5, 1.02) if loc == "lower center" else None,
        ncol=ncol, frameon=False, fontsize=8.6, borderaxespad=0.2,
    )


def med(rows, pred, key):
    vals = [r[key] for r in rows if pred(r)]
    return float(np.median(vals)) if vals else np.nan


def col(hist, key):
    arr = np.asarray(hist[key])
    return arr[:, 0] if arr.ndim > 1 else arr


def replay_seed7():
    out = rollout(
        length=np.array([0.03]),
        proto=np.array([0]),
        t0=np.array([8.0]),
        m0=np.array([0.72]),
        hetero=np.array([0]),
        seed=np.array([7]),
        policy="dual",
        minutes=55.0,
        dt=2.0,
        record_every=4,
        store_history=True,
        cook="combi",
    )
    return out


def draw_field_xt(hist):
    t = col(hist, "time") / 60.0
    surf = col(hist, "t_surf")
    core = col(hist, "t_core")
    n = 16
    depth = np.linspace(0.0, 30.0, n)
    field = np.zeros((len(t), n))
    for i, (s, c) in enumerate(zip(surf, core)):
        field[i] = s + (c - s) * (depth / 30.0) ** 1.15
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    im = ax.pcolormesh(
        t, depth, field.T, shading="auto", cmap=HEATMAP, vmin=5, vmax=170,
    )
    ax.axvspan(150 / 60, 190 / 60, color=INK, alpha=0.08, lw=0)
    tt, dd = np.meshgrid(t, depth)
    ax.contour(tt, dd, field.T, levels=[70], colors=["#1c1a17"], linewidths=0.75, linestyles="--")
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("距表面 / mm")
    ax.invert_yaxis()
    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.set_label("温度 / °C")
    ax.set_title("种子 7，组合档，对偶策略：厚度–时间温度场")
    fig.savefig(FIG / "P_field_xt.png")
    plt.close(fig)


def draw_field_3d(hist):
    t = col(hist, "time") / 60.0
    surf = col(hist, "t_surf")
    core = col(hist, "t_core")
    # downsample for a readable mesh
    idx = np.linspace(0, len(t) - 1, 48).astype(int)
    t = t[idx]
    surf = surf[idx]
    core = core[idx]
    depth = np.linspace(0.0, 30.0, 24)
    T, D = np.meshgrid(t, depth)
    Z = np.zeros_like(T)
    for j, (s, c) in enumerate(zip(surf, core)):
        Z[:, j] = s + (c - s) * (depth / 30.0) ** 1.15
    fig = plt.figure(figsize=(7.2, 4.8))
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    surf_plot = ax.plot_surface(
        T, D, Z, cmap=HEATMAP, linewidth=0.15, antialiased=True,
        rstride=1, cstride=1, vmin=5, vmax=170, edgecolor="none", alpha=0.97,
    )
    ax.view_init(elev=24, azim=-62)
    ax.set_xlabel("时间 / min", labelpad=10)
    ax.set_ylabel("深度 / mm", labelpad=10)
    ax.zaxis.set_rotate_label(False)
    ax.set_zlabel("温度 / °C", labelpad=2, rotation=90)
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor(LINE)
    ax.yaxis.pane.set_edgecolor(LINE)
    ax.zaxis.pane.set_edgecolor(LINE)
    ax.grid(True, color=LINE, linewidth=0.4)
    ax.tick_params(axis="z", pad=2)
    cb = fig.colorbar(surf_plot, ax=ax, shrink=0.55, pad=0.12, fraction=0.035)
    cb.set_label("温度 / °C")
    ax.set_title("一维温度场沿时间展开（种子 7）", pad=8)
    fig.subplots_adjust(left=0.02, right=0.86, bottom=0.08, top=0.90)
    fig.savefig(FIG / "P_field_3d.png", dpi=220)
    plt.close(fig)


def draw_profiles(hist):
    t = col(hist, "time")
    surf = col(hist, "t_surf")
    core = col(hist, "t_core")
    marks_min = [0, 2.5, 5, 8, 12, 16, 20, 24, 28, 35, 42, 55]
    colors = [
        "#5c564c", "#c45c26", "#d08a3a", "#b8860b", "#4a6b4e", "#2a6f7f",
        "#1f4e79", "#8a3a28", "#6b3f6a", "#3d5c54", "#8d6b3a", "#1c1a17",
    ]
    depth = np.linspace(0.94, 29.06, 16)
    fig, ax = plt.subplots(figsize=(7.2, 4.35))
    for m, color in zip(marks_min, colors):
        k = int(np.argmin(np.abs(t - m * 60)))
        s, c = surf[k], core[k]
        profile = s + (c - s) * ((depth - depth[0]) / (depth[-1] - depth[0])) ** 1.15
        ax.plot(
            depth, profile, color=color, lw=1.55,
            marker="o", ms=2.6, markevery=1, label=f"{m:g} min",
        )
    ax.set_xlabel("距表面 / mm")
    ax.set_ylabel("温度 / °C")
    ax.set_ylim(0, 165)
    ax.set_xlim(0, 31)
    ax.legend(
        loc="upper left", bbox_to_anchor=(1.02, 1.02),
        fontsize=7.4, ncol=1, frameon=False, handlelength=1.6, borderaxespad=0.0,
    )
    ax.set_title("若干时刻的厚度剖面（十六条控制体）")
    fig.tight_layout(rect=(0, 0, 0.82, 1.0))
    fig.savefig(FIG / "P_profiles.png")
    plt.close(fig)


def draw_seed7_panels(hist):
    t = col(hist, "time") / 60.0
    fig, axes = plt.subplots(4, 1, figsize=(7.0, 8.4), sharex=True)
    axes[0].axvspan(150 / 60, 190 / 60, color="#c45c26", alpha=0.12, lw=0)
    axes[0].plot(t, col(hist, "t_surf"), color=HEAT, lw=1.7, label="表面")
    axes[0].plot(t, col(hist, "t_core"), color=STEAM, lw=1.7, label="冷点")
    axes[0].plot(t, col(hist, "t_hat"), color="#b8860b", lw=1.5, ls="--", label="估计")
    axes[0].set_ylabel("温度 / °C")
    axes[0].legend(ncol=3, loc="lower right", fontsize=8.4)
    axes[0].set_title("种子 7，肉糜 30 mm，对偶。阴影为探针窗口")
    axes[0].set_ylim(-18, 175)

    ax2 = axes[1]
    ax2.plot(t, col(hist, "heat"), color=HEAT, lw=1.6, label="加热")
    ax2.plot(t, col(hist, "steam"), color=STEAM, lw=1.6, label="蒸汽")
    ax2b = ax2.twinx()
    ax2b.spines["right"].set_visible(True)
    ax2b.plot(t, col(hist, "heater"), color=INK, lw=1.15, ls=":", label="加热器")
    ax2.set_ylabel("指令")
    ax2b.set_ylabel("加热器 / °C")
    ax2.set_ylim(-0.05, 1.18)
    ax2b.set_ylim(20, 230)
    h1, l1 = ax2.get_legend_handles_labels()
    h2, l2 = ax2b.get_legend_handles_labels()
    ax2.legend(
        h1 + h2, l1 + l2, ncol=3, loc="upper right", fontsize=8.0, frameon=False,
    )
    ax2.grid(True)

    axes[2].plot(t, col(hist, "alpha_m"), color=STEAM, lw=1.8)
    axes[2].axhline(0.85, color=MUTED, ls="--", lw=0.9)
    axes[2].text(1.2, 0.88, "设计线 0.85", color=MUTED, fontsize=8)
    axes[2].set_ylabel(r"$\alpha_m$")
    axes[2].set_ylim(-0.04, 1.08)

    axes[3].plot(t, col(hist, "var_r"), color=HEAT, lw=1.8)
    axes[3].set_ylabel("热阻方差")
    axes[3].set_xlabel("时间 / min")
    axes[3].set_ylim(0.12, 0.74)
    fig.tight_layout(h_pad=0.45)
    fig.savefig(FIG / "P_seed7_panels.png")
    plt.close(fig)


def draw_architecture():
    fig, ax = plt.subplots(figsize=(8.4, 4.7))
    ax.set_xlim(0, 13.2)
    ax.set_ylim(0.3, 6.7)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    def node(x, y, w, h, text, fc="#f7f1e6", ec=INK):
        p = FancyBboxPatch(
            (x - w / 2, y - h / 2), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            facecolor=fc, edgecolor=ec, lw=1.15,
        )
        ax.add_patch(p)
        ax.text(x, y, text, ha="center", va="center", fontsize=9.0, color=INK)

    def arr(a, b, color=INK):
        ax.annotate(
            "", xy=b, xytext=a,
            arrowprops=dict(arrowstyle="-|>", color=color, lw=1.2,
                            mutation_scale=11, shrinkA=2, shrinkB=2),
        )

    node(1.85, 5.15, 2.7, 1.18, "腔体边界\n加热 / 蒸汽 / 排汽 / 风机", "#efe6d6")
    node(6.6, 5.15, 2.7, 1.18, "可安装观测\n表面温度 · 腔温 · 含水")
    node(11.25, 5.15, 2.7, 1.18, "决策状态后验\n冷点 · 进度 · 热阻")
    node(11.25, 2.35, 2.7, 1.18, "对偶决策\n信息动作 / 品质动作", "#e7f0f2")
    node(6.6, 2.35, 2.7, 1.18, "安全投影\n只读硬测量", "#f3e3d6")
    node(1.85, 2.35, 2.7, 1.18, "执行器接口\n写回四个边界", "#efe6d6")
    arr((3.25, 5.15), (5.2, 5.15))
    arr((8.0, 5.15), (9.85, 5.15))
    arr((11.25, 4.52), (11.25, 2.98))
    arr((9.85, 2.35), (8.0, 2.35), HEAT)
    arr((5.2, 2.35), (3.25, 2.35), HEAT)
    arr((1.85, 2.98), (1.85, 4.52), HEAT)
    ax.text(8.9, 2.72, "投影前", fontsize=8, color=HEAT, ha="center")
    ax.text(4.2, 2.72, "投影后的指令", fontsize=8, color=HEAT, ha="center")
    ax.text(6.6, 6.05, "观测通道", fontsize=8.4, color=MUTED, ha="center")
    ax.set_title("感知–决策–执行闭环", pad=6)
    fig.savefig(FIG / "architecture.png", dpi=220)
    plt.close(fig)


def draw_cavity():
    fig, ax = plt.subplots(figsize=(8.0, 5.05))
    ax.set_xlim(0.05, 10.55)
    ax.set_ylim(0.05, 6.85)
    ax.axis("off")
    ax.add_patch(Rectangle((1.05, 0.62), 7.95, 5.05, fill=False, lw=1.7, edgecolor=INK))
    ax.add_patch(Rectangle((1.22, 0.78), 7.62, 4.72, fill=True, fc="#f4efe6", ec="none", alpha=0.55))
    # six independent U-tubes
    for i, x in enumerate(np.linspace(1.95, 6.55, 6)):
        ax.plot([x, x], [5.05, 5.38], color=HEAT, lw=2.05, solid_capstyle="round")
        ax.add_patch(Arc((x + 0.22, 5.05), 0.44, 0.42, theta1=180, theta2=360, color=HEAT, lw=2.05))
        ax.plot([x + 0.44, x + 0.44], [5.05, 5.38], color=HEAT, lw=2.05, solid_capstyle="round")
        ax.add_patch(Circle((x, 5.40), 0.055, fc="#d8d0c4", ec=INK, lw=0.4))
        ax.add_patch(Circle((x + 0.44, 5.40), 0.055, fc="#d8d0c4", ec=INK, lw=0.4))
    ax.plot([1.85, 7.05], [5.48, 5.48], color="#8a8f93", lw=1.35, solid_capstyle="round")
    ax.text(4.50, 5.78, "六根 U 形加热管", ha="center", color=HEAT, fontsize=9.0)
    ax.add_patch(Rectangle((1.28, 0.72), 1.05, 0.42, fc="#d8e0e6", ec=INK, lw=0.6))
    ax.text(1.80, 0.93, "水箱", ha="center", va="center", fontsize=7.6, color=STEAM)
    ax.add_patch(Rectangle((2.55, 0.78), 4.2, 0.16, fc="#c8d0c2", ec=INK, lw=0.45))
    ax.text(4.65, 0.86, "冷凝托盘", ha="center", va="center", fontsize=7.2, color=MUTED)
    # ten-blade fan
    cx, cy, r = 7.78, 2.88, 0.62
    ax.add_patch(Circle((cx, cy), r + 0.08, fill=False, lw=1.25, edgecolor=STEAM))
    ax.add_patch(Circle((cx, cy), 0.12, fc="#d8e0e6", ec=STEAM, lw=0.8))
    for k in range(10):
        ang = np.deg2rad(k * 36.0)
        ax.plot(
            [cx + 0.12 * np.cos(ang), cx + 0.52 * np.cos(ang + 0.22)],
            [cy + 0.12 * np.sin(ang), cy + 0.52 * np.sin(ang + 0.22)],
            color=STEAM, lw=1.55, solid_capstyle="round",
        )
    ax.text(cx, 1.95, "十叶风机", ha="center", fontsize=8.6, color=STEAM)
    # steam
    ax.plot([1.38, 2.18], [3.48, 3.48], color=STEAM, lw=3.1, solid_capstyle="round")
    ax.annotate("", xy=(2.95, 3.48), xytext=(2.18, 3.48),
                arrowprops=dict(arrowstyle="-|>", color=STEAM, lw=1.45))
    ax.text(1.78, 3.82, "蒸汽喷嘴", fontsize=8.6, color=STEAM, ha="center")
    # exhaust louvres
    for i in range(7):
        ax.add_patch(Rectangle((8.48, 4.02 + i * 0.09), 0.38, 0.055, fc="#c8d0c2", ec=INK, lw=0.45))
    ax.annotate(
        "七片排汽百叶", xy=(8.86, 4.72), xytext=(9.42, 5.55),
        ha="left", color=MUTED, fontsize=8.3,
        arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=0.8),
    )
    # sixteen slabs
    y0, y1 = 1.28, 2.88
    for i, yy in enumerate(np.linspace(y0, y1, 16)):
        h = (y1 - y0) / 16.0 * 0.86
        fc = "#8a5a32" if i == 5 else "#e2b07a"
        ax.add_patch(Rectangle((3.12, yy), 3.05, h, fc=fc, ec=INK, lw=0.28, alpha=0.95))
    ax.text(4.64, 3.08, "表面", ha="center", fontsize=8.2)
    ax.text(4.64, 1.08, "冷点 · 十六条控制体", ha="center", fontsize=8.4, color=STEAM)
    ax.set_title("同一腔体上的四个执行量")
    fig.savefig(FIG / "cavity_schematic.png", dpi=220)
    plt.close(fig)


def draw_loop():
    fig, ax = plt.subplots(figsize=(8.6, 3.15))
    ax.set_xlim(0, 13.4)
    ax.set_ylim(0.15, 3.55)
    ax.axis("off")
    labels = ["边界", "16 控制体", "表面观测", "探针或跟踪", "加热指令"]
    xs = [1.25, 3.85, 6.55, 9.25, 11.95]
    for x, lab in zip(xs, labels):
        p = FancyBboxPatch(
            (x - 1.05, 1.55), 2.1, 0.95,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            fc="#f7f1e6", ec=INK, lw=1.15,
        )
        ax.add_patch(p)
        ax.text(x, 2.02, lab, ha="center", va="center", fontsize=9.2)
    for a, b in zip(xs[:-1], xs[1:]):
        ax.annotate(
            "", xy=(b - 1.08, 2.02), xytext=(a + 1.08, 2.02),
            arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.15, mutation_scale=11),
        )
    ax.annotate(
        "", xy=(1.25, 1.48), xytext=(11.95, 1.48),
        arrowprops=dict(
            arrowstyle="-|>", color=HEAT, lw=1.2, mutation_scale=11,
            connectionstyle="arc3,rad=-0.22",
        ),
    )
    ax.text(6.6, 0.52, "加热指令写回边界", ha="center", color=HEAT, fontsize=8.6)
    ax.set_title("已运行闭环的五段")
    fig.savefig(FIG / "M_loop.png", dpi=220)
    plt.close(fig)


def gab_isotherm(aw, xm, c, k):
    aw = np.clip(aw, 1e-4, 0.92)
    return xm * c * k * aw / ((1.0 - k * aw) * (1.0 - k * aw + c * k * aw))


def draw_gab():
    aw = np.linspace(0.05, 0.90, 240)
    potato = [
        ("吸附 30 °C", 0.0567, 14.34, 0.912, HEAT, "-"),
        ("吸附 45 °C", 0.0457, 13.71, 0.885, "#b05a3a", "-"),
        ("吸附 60 °C", 0.0359, 6.38, 0.762, "#8a3a28", "-"),
        ("解吸 30 °C", 0.0763, 9.21, 0.861, STEAM, "--"),
        ("解吸 45 °C", 0.0549, 8.55, 0.860, NAVY, "--"),
        ("解吸 60 °C", 0.0522, 3.75, 0.666, SAGE, "--"),
    ]
    tomato = [
        ("番茄 20 °C", 0.2037, 27.48, 0.834, "#c45c26"),
        ("番茄 30 °C", 0.1621, 22.65, 0.897, "#d08a3a"),
        ("番茄 40 °C", 0.1610, 10.81, 0.896, "#8a5a2b"),
        ("番茄 50 °C", 0.2002, 4.43, 0.840, "#5c3a22"),
        ("番茄 60 °C", 0.1097, 10.22, 0.972, MUTED),
    ]
    grains = [
        ("面粉 20 °C", 0.0801, 13.48, 0.734, "#7a6a4e", "-"),
        ("大米 25 °C", 0.0645, 5.86, 0.793, "#4e6b7a", "-"),
        ("小米 30 °C", 0.0673, 10.55, 0.806, SAGE, "--"),
        ("奶粉 25 °C", 0.0375, 7.19, 0.944, NAVY, "--"),
        ("蘑菇 30 °C", 0.1722, 4.72, 0.713, HEAT, ":"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.15), sharey=False)
    ax = axes[0]
    for lab, xm, c, k, color, ls in potato:
        ax.plot(aw, gab_isotherm(aw, xm, c, k), color=color, lw=1.7, ls=ls, label=lab)
    ax.set_xlabel(r"$a_w$")
    ax.set_ylabel("平衡含水")
    ax.set_xlim(0.04, 0.92)
    ax.set_ylim(0, 0.28)
    ax.legend(loc="upper left", fontsize=7.4, ncol=1, frameon=False)
    ax.set_title("土豆六条（30/45/60 °C）")
    ax = axes[1]
    for lab, xm, c, k, color in tomato:
        ax.plot(aw, gab_isotherm(aw, xm, c, k), color=color, lw=1.55, label=lab)
    for lab, xm, c, k, color, ls in grains:
        ax.plot(aw, gab_isotherm(aw, xm, c, k), color=color, lw=1.25, ls=ls, alpha=0.95, label=lab)
    ax.set_xlabel(r"$a_w$")
    ax.set_ylabel("平衡含水")
    ax.set_xlim(0.04, 0.92)
    ax.set_ylim(0, 0.78)
    ax.legend(
        loc="upper left", bbox_to_anchor=(1.02, 1.02),
        fontsize=7.2, ncol=1, frameon=False, handlelength=1.8, borderaxespad=0.0,
    )
    ax.set_title("番茄温度族与谷物、粉体对照")
    fig.suptitle("公开 GAB 清洁子集等温线", y=1.02, fontsize=11.4)
    fig.tight_layout(rect=(0, 0, 0.82, 0.96))
    fig.savefig(FIG / "P_gab.png")
    plt.close(fig)


def draw_aw():
    from acts_mcdt.physics import gab_aw
    m = np.linspace(0.02, 0.92, 400)
    fig, ax = plt.subplots(figsize=(6.8, 4.05))
    names = {0: "肉糜", 1: "土豆", 2: "面团"}
    colors = {0: HEAT, 1: STEAM, 2: "#b8860b"}
    for proto in (0, 1, 2):
        aw = gab_aw(m, np.full_like(m, proto))
        ax.plot(m, aw, color=colors[proto], lw=1.9, label=names[proto])
    for x in (0.64, 0.72, 0.80):
        ax.axvline(x, color=MUTED, lw=0.85, ls=":")
        ax.text(x, 0.445, f"{x:.2f}", ha="center", va="bottom", color=MUTED, fontsize=8.2)
    ax.set_xlabel("含水")
    ax.set_ylabel(r"$a_w$")
    ax.set_ylim(0.42, 1.02)
    ax.set_xlim(0.0, 0.95)
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=8.6, frameon=False)
    ax.set_title("核内活度。竖线是 S1 的三档初含水")
    fig.tight_layout()
    fig.savefig(FIG / "P_aw.png")
    plt.close(fig)


def draw_probe(hist):
    t = col(hist, "time")
    mask = (t >= 75) & (t <= 280)
    fig, ax = plt.subplots(figsize=(6.8, 3.7))
    ax.axvspan(150, 190, color="#efe0c8", lw=0)
    ax.plot(t[mask], col(hist, "t_surf")[mask], color=HEAT, lw=1.8, label="表面")
    ax.plot(t[mask], col(hist, "t_core")[mask], color=STEAM, lw=1.8, label="冷点")
    ax.plot(t[mask], col(hist, "t_hat")[mask], color="#b8860b", lw=1.5, ls="--", label="估计")
    ax.set_xlabel("时间 / s")
    ax.set_ylabel("温度 / °C")
    ax.set_ylim(-12, 118)
    ax.legend(loc="upper left", fontsize=8.4, frameon=False)
    ax.set_xlim(75, 280)
    ax.text(170, 114, "探针窗 150–190 s", ha="center", va="top", color=MUTED, fontsize=8.2)
    ax.set_title("探针窗口附近。冷点几乎不动")
    fig.savefig(FIG / "P_probe.png")
    plt.close(fig)


def draw_heater(hist):
    t_min = col(hist, "time") / 60.0
    t_ode = np.linspace(0.0, 10.0, 400)
    th = 40 + (196.5 - 40) * (1 - np.exp(-(t_ode * 60.0) / 43.48))
    fig, ax = plt.subplots(figsize=(6.8, 3.9))
    ax.plot(t_ode, th, color=HEAT, lw=1.9, label="满功率，初值 40 °C")
    ax.plot(t_min, col(hist, "heater"), color=MUTED, lw=1.25, label="种子 7 加热器")
    ax.axhline(196.5, color=INK, ls="--", lw=1.05, label="平衡 196.5 °C")
    ax.axhline(230, color="#8a3a28", ls=":", lw=1.2, label="削减阈值 230 °C")
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("加热器温度 / °C")
    ax.set_xlim(0, 55)
    ax.set_ylim(20, 250)
    ax.legend(loc="lower right", fontsize=8.0, frameon=False)
    ax.set_title("加热器常微分方程。满功率平衡低于削减阈值")
    fig.savefig(FIG / "P_heater.png")
    plt.close(fig)


def draw_fo():
    Lmm = np.linspace(12.0, 55.0, 88)
    L = Lmm / 1000.0
    alpha = 2.0e-7
    menu = 900.0 + 18000.0 * (L - 0.015)
    fig, ax = plt.subplots(figsize=(6.6, 3.85))
    ax.plot(Lmm, alpha * 40.0 / L ** 2, color=HEAT, lw=1.85, label="探针 40 s")
    ax.plot(Lmm, alpha * menu / L ** 2, color=STEAM, lw=1.85, label="开环菜单终点")
    ax.plot(Lmm, alpha * 3300.0 / L ** 2, color=NAVY, lw=1.35, ls="--", label="时域 55 min")
    for Lm, mk in ((15, "o"), (30, "s"), (50, "D")):
        ax.plot(Lm, alpha * 40.0 / (Lm / 1000.0) ** 2, mk, color=HEAT, ms=6.5)
        ax.plot(Lm, alpha * (900.0 + 18000.0 * (Lm / 1000.0 - 0.015)) / (Lm / 1000.0) ** 2, mk, color=STEAM, ms=6.5)
    ax.set_xticks([15, 30, 50])
    ax.set_xlabel("厚度 / mm")
    ax.set_ylabel("Fourier 数")
    ax.set_ylim(0, 3.25)
    ax.set_xlim(13.5, 55)
    ax.legend(loc="upper right", fontsize=8.2, frameon=False, borderaxespad=0.4)
    ax.set_title(r"核扩散率 $\alpha=2.0\times 10^{-7}\,\mathrm{m}^2/\mathrm{s}$")
    fig.savefig(FIG / "P_fo.png")
    plt.close(fig)


def draw_campaign_boxes(s1):
    pols = ("open", "pid", "mpc", "dual")
    names = [ "开环", "腔温比例", "无探针", "对偶"]
    colors = [MUTED, HEAT, STEAM, NAVY]
    energy = [[r["energy"] for r in s1 if r["policy"] == p] for p in pols]
    fig, ax = plt.subplots(figsize=(6.8, 3.9))
    bp = ax.boxplot(
        energy, tick_labels=names, showfliers=False, patch_artist=True,
        medianprops=dict(color=INK, lw=1.4),
        whiskerprops=dict(color=INK), capprops=dict(color=INK),
    )
    for patch, c in zip(bp["boxes"], colors):
        patch.set_facecolor(c)
        patch.set_alpha(0.45)
        patch.set_edgecolor(INK)
    ax.set_ylabel("能量（指令 × 秒）")
    ax.set_title("S1 累计加热。纵轴是指令对时间的求和")
    fig.savefig(FIG / "P_energy.png")
    plt.close(fig)

    fig, axes = plt.subplots(1, 4, figsize=(8.8, 3.55), sharey=True)
    bins = np.linspace(0, 55, 29)
    for ax, p, name, color in zip(axes, pols, names, colors):
        vals = np.array([r["stop_s"] for r in s1 if r["policy"] == p]) / 60.0
        ax.hist(vals, bins=bins, color=color, edgecolor=INK, lw=0.35, alpha=0.82)
        ax.set_title(name, fontsize=10)
        ax.set_xlim(0, 56)
        ax.set_xlabel("min")
    axes[0].set_ylabel("条数")
    fig.suptitle("S1：停机时刻", y=1.02)
    fig.savefig(FIG / "P_stop.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.6, 3.8))
    for p, name, color in zip(pols, names, [MUTED, HEAT, STEAM, NAVY]):
        v = np.sort([r["e_alpha"] for r in s1 if r["policy"] == p])
        y = np.linspace(0, 1, len(v), endpoint=True)
        ax.plot(v, y, color=color, lw=1.8, label=name)
    ax.axvline(0, color=MUTED, lw=0.8, ls="--", zorder=0)
    ax.annotate(
        r"设计线 $e_\alpha=0$", xy=(0, 0.18), xytext=(0.12, 0.18),
        fontsize=8.4, color=MUTED,
        arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6),
    )
    ax.set_xlabel(r"$e_\alpha$")
    ax.set_ylabel("经验分布")
    ax.legend(loc="upper left", fontsize=8.4, frameon=False)
    ax.set_title("S1 停机偏差经验分布")
    fig.savefig(FIG / "P_ecdf.png")
    plt.close(fig)


def draw_dt(hist):
    t = col(hist, "time") / 60.0
    fig, ax = plt.subplots(figsize=(6.8, 3.7))
    ax.plot(t, col(hist, "t_surf") - col(hist, "t_core"), color=HEAT, lw=1.8, label="表面 − 冷点")
    ax.plot(t, col(hist, "t_hat") - col(hist, "t_core"), color=STEAM, lw=1.7, label="估计 − 冷点")
    ax.axhline(0, color=MUTED, lw=0.8, ls="--")
    ax.axvspan(150 / 60, 190 / 60, color=STEAM, alpha=0.12, lw=0)
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("温差 / K")
    ax.set_xlim(0, 55)
    ax.legend(loc="center right", fontsize=8.4, frameon=False)
    ax.set_title("种子 7：表面减冷点、估计减冷点")
    fig.savefig(FIG / "P_dt.png")
    plt.close(fig)


def draw_paths():
    fig, ax = plt.subplots(figsize=(7.8, 3.9))
    ax.set_xlim(0, 12.4)
    ax.set_ylim(0, 5.5)
    ax.axis("off")

    def node(x, y, text, fc="#f7f1e6"):
        p = FancyBboxPatch((x - 1.05, y - 0.38), 2.1, 0.76,
                           boxstyle="round,pad=0.02,rounding_size=0.08",
                           fc=fc, ec=INK, lw=1.1)
        ax.add_patch(p)
        ax.text(x, y, text, ha="center", va="center", fontsize=9)

    node(1.4, 2.6, "蒸汽指令", "#e7f0f2")
    node(4.5, 4.2, "潜热 → 冷点", "#f3e3d6")
    node(4.5, 2.6, "表面含水", "#f7f1e6")
    node(4.5, 1.0, "结壳 → 热阻", "#efe6d6")
    node(8.0, 4.2, "进度 $\\alpha_m$")
    node(8.0, 2.6, "褐变 / 失水")
    node(8.0, 1.0, "冷点变慢")
    node(10.7, 2.6, "品质 $Q$", "#e7f0f2")
    for a, b, c, lab in [
        ((2.45, 2.85), (3.45, 4.2), HEAT, "A"),
        ((2.45, 2.6), (3.45, 2.6), STEAM, "B"),
        ((2.45, 2.35), (3.45, 1.0), "#8a5a2b", "C"),
        ((5.55, 4.2), (6.95, 4.2), HEAT, ""),
        ((5.55, 2.6), (6.95, 2.6), STEAM, ""),
        ((5.55, 1.0), (6.95, 1.0), "#8a5a2b", ""),
        ((9.05, 4.2), (9.65, 2.95), INK, ""),
        ((9.05, 2.6), (9.65, 2.6), INK, ""),
        ((9.05, 1.0), (9.65, 2.25), INK, ""),
    ]:
        ax.annotate("", xy=b, xytext=a,
                    arrowprops=dict(arrowstyle="-|>", color=c, lw=1.25, mutation_scale=11))
        if lab:
            ax.text((a[0] + b[0]) / 2 - 0.15, (a[1] + b[1]) / 2 + 0.18, lab,
                    color=c, fontsize=9, fontweight="bold")
    ax.set_title("同一次蒸汽的三条因果路径")
    fig.savefig(FIG / "path_abc.png", dpi=220)
    plt.close(fig)


def restyle_study(rows):
    cooks = ("steam", "bake", "combi")
    cook_name = {"steam": "蒸", "bake": "烤", "combi": "组合"}
    policies = ("open", "pid", "mpc", "dual")
    policy_name = {"open": "开环", "pid": "腔温比例", "mpc": "无探针", "dual": "对偶"}
    colors = (MUTED, HEAT, STEAM, NAVY)

    grid = np.zeros((3, 3))
    foods = ("mince", "potato", "dough")
    food_name = {"mince": "肉糜", "potato": "土豆", "dough": "面团"}
    for i, food in enumerate(foods):
        for j, cook in enumerate(cooks):
            grid[i, j] = med(
                rows,
                lambda r, food=food, cook=cook: (
                    r["food"] == food and r["cook"] == cook and r["policy"] == "dual"
                ),
                "e_alpha",
            )
    fig, ax = plt.subplots(figsize=(5.8, 3.8))
    ax.grid(False)
    im = ax.imshow(grid, cmap=HEATMAP, vmin=-0.9, vmax=0.16)
    ax.set_xticks(range(3), [cook_name[c] for c in cooks])
    ax.set_yticks(range(3), [food_name[f] for f in foods])
    for i in range(3):
        for j in range(3):
            ax.text(
                j, i, f"{grid[i, j]:+.2f}", ha="center", va="center",
                color=ink_or_white(grid[i, j], -0.9, 0.16, HEATMAP), fontsize=11,
            )
    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.set_label("进度偏差中位数")
    ax.set_title("对偶策略：食品 × 档位")
    ax.spines["top"].set_visible(True)
    ax.spines["right"].set_visible(True)
    fig.savefig(STUDY_FIG / "F1_mode_food.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(5.8, 3.6))
    cook_style = {
        "steam": (HEAT, "o", "-"),
        "bake": (STEAM, "s", "--"),
        "combi": (NAVY, "D", "-."),
    }
    cook_dx = {"steam": -2.2, "bake": 0.0, "combi": 2.2}
    for cook in cooks:
        color, mk, ls = cook_style[cook]
        xs = [L + cook_dx[cook] for L in (15, 30, 50)]
        ys = [
            med(rows, lambda r, cook=cook, L=L: r["cook"] == cook and r["policy"] == "dual" and r["length_mm"] == L, "e_alpha")
            for L in (15, 30, 50)
        ]
        ax.plot(xs, ys, marker=mk, color=color, lw=1.8, ls=ls, ms=6.4, label=cook_name[cook])
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_xlim(11, 54)
    ax.set_xticks([15, 30, 50])
    ax.set_xlabel("厚度 / mm")
    ax.set_ylabel("进度偏差中位数")
    ax.legend(loc="center left", fontsize=8.2, frameon=False)
    ax.set_title("对偶策略下进度偏差随厚度变化")
    fig.savefig(STUDY_FIG / "F2_thickness.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(5.8, 3.6))
    data = []
    for policy in policies:
        vals = [r["energy"] for r in rows if r["policy"] == policy and r["cook"] == "combi"]
        data.append(vals)
    bp = ax.boxplot(data, tick_labels=[policy_name[p] for p in policies], showfliers=False,
                    medianprops=dict(color=HEAT, lw=1.6),
                    boxprops=dict(color=INK, lw=1.1),
                    whiskerprops=dict(color=INK),
                    capprops=dict(color=INK))
    ax.set_ylabel("累计加热")
    ax.set_title("组合档四种策略的累计加热")
    fig.savefig(STUDY_FIG / "F3_energy.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(5.8, 3.6))
    for cook, color in zip(cooks, (STEAM, HEAT, SAGE)):
        sub = [r["var_r"] for r in rows if r["cook"] == cook and r["policy"] == "dual"]
        ax.hist(sub, bins=28, histtype="step", color=color, lw=1.6, label=cook_name[cook])
    ax.set_xlabel("结束时热阻方差")
    ax.set_ylabel("条数")
    ax.legend(loc="upper right", fontsize=8.4, frameon=False)
    ax.set_title("对偶策略结束时的热阻方差")
    fig.savefig(STUDY_FIG / "F4_variance.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(5.8, 3.6))
    marks = ("o", "s", "D", "^")
    styles = ("-", "--", "-.", ":")
    dxs = (-2.4, -0.8, 0.8, 2.4)
    for policy, color, mk, ls, dx in zip(policies, colors, marks, styles, dxs):
        xs = [L + dx for L in (15, 30, 50)]
        ys = [
            med(rows, lambda r, policy=policy, L=L: r["policy"] == policy and r["cook"] == "combi" and r["length_mm"] == L, "stop_s") / 60
            for L in (15, 30, 50)
        ]
        ax.plot(xs, ys, marker=mk, color=color, lw=1.8, ls=ls, ms=6.5, label=policy_name[policy])
    ax.set_xlim(11, 54)
    ax.set_xticks([15, 30, 50])
    ax.set_xlabel("厚度 / mm")
    ax.set_ylabel("停止时刻 / min")
    ax.set_ylim(12, 58)
    ax.legend(loc="lower right", fontsize=8.0, frameon=False)
    ax.set_title("组合档停止时刻中位数")
    fig.savefig(STUDY_FIG / "F5_stop.png")
    plt.close(fig)

    grid = np.zeros((4, 3))
    for i, policy in enumerate(policies):
        for j, cook in enumerate(cooks):
            grid[i, j] = med(
                rows,
                lambda r, policy=policy, cook=cook: r["policy"] == policy and r["cook"] == cook,
                "e_alpha",
            )
    fig, ax = plt.subplots(figsize=(5.8, 4.0))
    ax.grid(False)
    im = ax.imshow(grid, cmap=HEATMAP, vmin=-0.9, vmax=0.16)
    ax.set_xticks(range(3), [cook_name[c] for c in cooks])
    ax.set_yticks(range(4), [policy_name[p] for p in policies])
    for i in range(4):
        for j in range(3):
            ax.text(
                j, i, f"{grid[i, j]:+.2f}", ha="center", va="center",
                color=ink_or_white(grid[i, j], -0.9, 0.16, HEATMAP),
            )
    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.set_label("进度偏差中位数")
    ax.set_title("策略 × 档位")
    ax.spines["top"].set_visible(True)
    ax.spines["right"].set_visible(True)
    fig.savefig(STUDY_FIG / "F7_policy_cook.png")
    plt.close(fig)


def main():
    setup_style()
    print("replaying seed 7")
    hist = replay_seed7()
    draw_field_xt(hist)
    draw_field_3d(hist)
    draw_profiles(hist)
    draw_seed7_panels(hist)
    draw_architecture()
    draw_cavity()
    draw_loop()
    draw_paths()
    draw_gab()
    draw_aw()
    draw_probe(hist)
    draw_heater(hist)
    draw_fo()
    draw_dt(hist)
    s1_path = ROOT / "results" / "logs" / "s1_summary.json"
    if s1_path.exists():
        print("campaign boxes")
        draw_campaign_boxes(json.loads(s1_path.read_text(encoding="utf-8")))
    study_path = ROOT / "results" / "logs" / "study.json"
    if study_path.exists():
        print("restyling study figures")
        rows = json.loads(study_path.read_text(encoding="utf-8"))
        restyle_study(rows)
    print("done", FIG)


if __name__ == "__main__":
    main()
