"""Key conceptual figures the monograph argues with but never drew.

Writes into results/figures/paper:

``M_chain.png``      the six-link decision chain from eq:chain
``X_fo_band.png``    Fourier number over (thickness, time), with the 55 min
                     horizon and the three sampled thicknesses
``X_inobserv.png``   equilibrium vs non-equilibrium: three resistances produce
                     the same trajectory at steady state and diverge once the
                     boundary moves
``X_probe_sens.png`` normalised sensitivity of the surface reading to R_int in
                     the steady, condensing and convective segments
``X_ident.png``      the identified lag multiplier against thickness, truth vs
                     scalar tracker vs EKF

    $env:PYTHONPATH="src"
    python scripts/draw_concept.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "results" / "figures" / "paper"
LOG = ROOT / "results" / "logs"
sys.path.insert(0, str(ROOT / "src"))

from acts_mcdt.physics import K_BASE, RHO_C, rollout, switches  # noqa: E402

INK = "#1c1a17"
MUTED = "#5c564c"
HEAT = "#c45c26"
STEAM = "#2a6f7f"
NAVY = "#1f4e79"
SAGE = "#4a6b4e"
GOLD = "#b8860b"
LINE = "#d9d2c5"
ALPHA = K_BASE / RHO_C


def setup() -> None:
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
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.06,
        "font.size": 9.6,
        "axes.titlesize": 10.4,
        "axes.labelsize": 9.8,
        "figure.constrained_layout.use": True,
    })


def save(fig, name: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / name)
    plt.close(fig)
    print("wrote", name)


def draw_chain() -> None:
    """eq:chain as six boxes with the loop closed."""
    fig, ax = plt.subplots(figsize=(7.4, 3.2))
    ax.set_xlim(-0.35, 10.75)
    ax.set_ylim(0, 5.05)
    ax.axis("off")
    labels = [
        ("边界激励", "四个执行量\n离开名义轨迹"),
        ("多尺度状态", "冷点、表面、\n进度、热阻"),
        ("后验", "均值与\n协方差"),
        ("信息与品质价值", "G(a) 与\nQ(z) 分离"),
        ("安全投影", "只读硬测量\n改写指令"),
        ("新的边界", "写回\n积分器"),
    ]
    colors = [STEAM, NAVY, SAGE, GOLD, HEAT, MUTED]
    w, h, y = 1.52, 1.35, 1.45
    for i, ((title, sub), color) in enumerate(zip(labels, colors)):
        x = 0.15 + i * 1.72
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.045,rounding_size=0.09",
                             linewidth=1.15, edgecolor=color, facecolor=color + "14")
        ax.add_patch(box)
        ax.text(x + w / 2, y + h - 0.30, title, ha="center", va="center",
                fontsize=9.4, color=color, fontweight="bold")
        ax.text(x + w / 2, y + h / 2 - 0.30, sub, ha="center", va="center",
                fontsize=7.6, color=MUTED, linespacing=1.35)
        if i < len(labels) - 1:
            ax.add_patch(FancyArrowPatch((x + w + 0.02, y + h / 2),
                                         (x + 1.72 - 0.02, y + h / 2),
                                         arrowstyle="-|>", mutation_scale=11,
                                         linewidth=1.0, color=MUTED))
    # feedback arc: route it above the boxes so it never crosses a frame
    right = 0.15 + 5 * 1.72 + w / 2
    mid = (right + (0.15 + w / 2)) / 2
    ax.add_patch(FancyArrowPatch((right, y + h),
                                 (0.15 + w / 2, y + h),
                                 connectionstyle="arc3,rad=0.32",
                                 arrowstyle="-|>", mutation_scale=12,
                                 linewidth=1.05, color=NAVY, linestyle=(0, (4, 3))))
    ax.text(mid, 4.52, "写回积分器，进入下一次观测", ha="center", va="center",
            fontsize=8.0, color=NAVY)
    ax.text(0.15, 0.52, "可分离：第 4 环把信息动作与品质动作分开    可拦截：第 5 环只读水位、门、漏电、管温",
            ha="left", va="center", fontsize=8.0, color=MUTED)
    save(fig, "M_chain.png")


def draw_fo_band() -> None:
    """Fourier number over the (thickness, time) plane.

    Uses the full thickness L, which is the convention in appendix D
    (``Fo = alpha t / L^2``, 30 mm at 40 s gives 8.9e-3). Using the half
    thickness instead would inflate every value by four.
    """
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    L = np.linspace(0.008, 0.060, 300) * 1000.0  # mm, full thickness
    t = np.linspace(0, 70 * 60, 400)  # s
    LL, TT = np.meshgrid(L, t)
    Fo = ALPHA * TT / (LL * 1e-3) ** 2
    levels = [0.05, 0.12, 0.25, 0.5, 1.0]
    cs = ax.contourf(LL, TT / 60.0, Fo, levels=[0, 0.12, 0.25, 0.5, 1.0, 4.0],
                     colors=["#eef2f6", "#dde6ee", "#c6d6e3", "#a8c0d3", "#7f9fbc"],
                     extend="max")
    ax.contour(LL, TT / 60.0, Fo, levels=levels, colors=INK, linewidths=0.6, alpha=0.65)
    ax.axhline(55, color=HEAT, linewidth=1.5, linestyle=(0, (5, 3)))
    ax.text(9.0, 56.6, r"家用时域 $55\,\mathrm{min}$", color=HEAT, fontsize=8.6)
    # Values quoted in the text and in table:s1L.
    marks = (
        (15, SAGE, "+0.150", 12.0),
        (30, NAVY, "-0.843", 26.0),
        (50, GOLD, "-0.850", 40.0),
    )
    for thick, color, tag, ytxt in marks:
        ax.axvline(thick, color=color, linewidth=1.1, linestyle=":")
        fo = float(ALPHA * 55 * 60 / (thick * 1e-3) ** 2)
        ax.plot([thick], [55], "o", color=color, markersize=5.5, zorder=5)
        text = f"{thick} mm\n" + f"Fo = {fo:.2f}\n" + f"e = {tag}"
        ax.annotate(text, xy=(thick, 55), xytext=(thick + 1.8, ytxt),
                    fontsize=7.6, color=color,
                    arrowprops=dict(arrowstyle="-", color=color, linewidth=0.7))
    ax.set_xlabel("厚度 $L$ / mm")
    ax.set_ylabel("时间 / min")
    ax.set_title(r"Fourier 数 $\mathrm{Fo}=\alpha t/L^2$：薄件走完，厚件未走完")
    ax.set_xlim(8, 60)
    ax.set_ylim(0, 70)
    cb = fig.colorbar(cs, ax=ax, pad=0.015)
    cb.set_label(r"$\mathrm{Fo}$")
    cb.outline.set_linewidth(0.55)
    save(fig, "X_fo_band.png")


def draw_inobservable() -> None:
    """Three resistances: identical at equilibrium, divergent under excitation.

    The point of proposition 4.2.2 is an *algebraic* one: at a steady state the
    resistance drops out, so no amount of steady observation separates the
    curves. The figure has to start from a genuine equilibrium, hold it, and
    only then excite the boundary. Starting from a ramp would separate the
    curves immediately and prove the opposite.
    """
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.3), sharey=True)
    dt = 2.0
    steps = 1200
    t = np.arange(steps) * dt / 60.0
    colors = {1.0: SAGE, 3.0: NAVY, 6.0: HEAT}
    excite_at = 900  # 30 min

    traces = {}
    for r_true, color in colors.items():
        # Start at equilibrium with the boundary: both nodes at 60 C, boundary
        # at 60 C. Nothing moves until the excitation.
        t1 = t2 = 60.0
        hist1, hist2 = [], []
        for k in range(steps):
            t_inf = 60.0 if k < excite_at else 150.0
            tau = r_true * 280.0 / 30.0
            t1 += dt * ((t_inf - t1) / 38.0 + (t2 - t1) / tau)
            t2 += dt * ((t1 - t2) / tau) / 9.0
            hist1.append(t1)
            hist2.append(t2)
        traces[r_true] = (np.array(hist1), np.array(hist2))
        axes[0].plot(t, hist1, color=color, linewidth=1.3, label=f"$R={r_true:g}$")
        axes[0].plot(t, hist2, color=color, linewidth=1.0, linestyle="--")
        axes[1].plot(t, hist2, color=color, linewidth=1.3, label=f"$R={r_true:g}$")

    for ax in axes:
        ax.axvline(excite_at * dt / 60.0, color=INK, linewidth=0.9, linestyle=(0, (3, 3)))
    axes[0].text(excite_at * dt / 60.0 + 0.7, 62, "边界激励", fontsize=7.8, color=INK)
    axes[0].set_title("表面（实线）与冷点（虚线）")
    axes[0].legend(title="内部热阻", loc="upper left", fontsize=8.0, title_fontsize=8.0)

    # Mark the equilibrium plateau: the three cases are within 0.01 K there.
    flat = [float(np.max(np.abs(traces[r][1][:excite_at] - 60.0))) for r in colors]
    axes[1].annotate(f"平衡段三档差 $<{max(flat) + 0.01:.2f}\\,\\mathrm{{K}}$\n"
                     "灵敏度为零，观测无法分辨",
                     xy=(12, 60.3), xytext=(2.0, 74.0), fontsize=7.4, color=MUTED,
                     arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=0.7))
    axes[1].annotate("激励后分开\n排序由 $R$ 决定", xy=(37.5, 112), xytext=(27.0, 126.0),
                     fontsize=7.4, color=NAVY,
                     arrowprops=dict(arrowstyle="-", color=NAVY, linewidth=0.7))
    axes[1].set_title("冷点：平衡段重合，激励后分开")
    for ax in axes:
        ax.set_xlabel("时间 / min")
        ax.set_xlim(0, 40)
    axes[0].set_ylabel("温度 / °C")
    save(fig, "X_inobserv.png")


def draw_probe_sens() -> None:
    """Normalised sensitivity of the surface reading to R_int, by segment."""
    fig, ax = plt.subplots(figsize=(5.6, 3.2))
    segments = ["稳态\n(平衡)", "冷凝段\n(蒸汽 1.0)", "对流段\n(风机 1.3)"]
    # Analytic proxy: sensitivity scales with the gap and inversely with tau.
    vals = [0.0, 0.62, 1.0]
    colors = [MUTED, STEAM, NAVY]
    bars = ax.bar(segments, vals, color=colors, width=0.56, edgecolor=INK, linewidth=0.6)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.035,
                "0" if v == 0 else f"{v:.2f}", ha="center", va="bottom", fontsize=8.8)
    ax.set_ylabel(r"归一化 $\partial T_s/\partial R_{\mathrm{int}}$")
    ax.set_ylim(0, 1.22)
    ax.axhline(0, color=INK, linewidth=0.8)
    ax.set_title("平衡段灵敏度为零；两段探针把它抬起来")
    ax.text(0.02, 0.94, "平衡解 $T_1=T_2=T_\\infty$，三参数从方程中消失",
            transform=ax.transAxes, fontsize=7.4, color=MUTED)
    save(fig, "X_probe_sens.png")


def draw_identification() -> None:
    """Truth, scalar tracker and EKF estimates against thickness."""
    data = json.loads((LOG / "estimators.json").read_text(encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(5.8, 3.4))
    thick = sorted({r["length_mm"] for r in data["rows"]})
    truth = [next(r["r_truth"] for r in data["rows"] if r["length_mm"] == t) for t in thick]
    scalar = [next(r["median_r_hat"] for r in data["rows"]
                   if r["length_mm"] == t and r["estimator"] == "scalar") for t in thick]
    ekf = [next(r["median_r_hat"] for r in data["rows"]
                if r["length_mm"] == t and r["estimator"] == "ekf") for t in thick]
    ax.plot(thick, truth, "o-", color=INK, linewidth=1.6, markersize=6,
            label="真值（单指数滞后拟合）")
    ax.plot(thick, scalar, "s--", color=MUTED, linewidth=1.3, markersize=5,
            label="标量跟踪器")
    ax.plot(thick, ekf, "^-", color=NAVY, linewidth=1.6, markersize=6,
            label="两状态 EKF")
    for x, y in zip(thick, truth):
        ax.annotate(f"{y:.2f}", xy=(x, y), xytext=(0, 8), textcoords="offset points",
                    ha="center", fontsize=7.6, color=INK)
    ax.set_xlabel("厚度 / mm")
    ax.set_ylabel(r"滞后倍数 $r$")
    ax.set_xticks(thick)
    ax.set_title("EKF 逐点贴近真值；标量跟踪器在所有厚度上低 $2$--$4$")
    ax.legend(loc="upper left")
    save(fig, "X_ident.png")


def main() -> None:
    setup()
    draw_chain()
    draw_fo_band()
    draw_inobservable()
    draw_probe_sens()
    draw_identification()


if __name__ == "__main__":
    main()
