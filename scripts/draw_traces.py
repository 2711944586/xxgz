"""Redraw the seed-7 trajectory family and the remaining curve figures.

``T_policy.png``  four policies, cold spot and progress, one panel each axis
``T_thick.png``   three thicknesses, progress and heat
``T_cook.png``    three cook modes, progress and variance
``T_l50.png``     55 vs 70 min horizon on the 50 mm case
``T_ant.png``     Antoine on/off delta by thickness
``T_s2.png``      S2 boundary scan as a paired slope chart

    $env:PYTHONPATH="src"
    python scripts/draw_traces.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import figstyle as fs  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))
from acts_mcdt.physics import BASELINE, DISPLAY, rollout  # noqa: E402

LOG = ROOT / "results" / "logs"
POLICIES = ("open", "pid", "mpc", "dual")


def run(length=0.03, policy="dual", cook="combi", minutes=55.0, gen=DISPLAY):
    return rollout(length=np.array([length]), proto=np.array([0]), t0=np.array([8.0]),
                   m0=np.array([0.72]), hetero=np.array([0]), seed=np.array([7.0]),
                   policy=policy, cook=cook, minutes=minutes, record_every=4,
                   store_history=True, **gen)


def draw_policy() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.7))
    for policy in POLICIES:
        out = run(policy=policy)
        t = out["time"][:, 0] / 60
        axes[0].plot(t, out["t_core"][:, 0], color=fs.SERIES[policy],
                     linewidth=1.3, label=fs.SERIES_CN[policy])
        axes[1].plot(t, out["alpha_m"][:, 0], color=fs.SERIES[policy],
                     linewidth=1.3)
    axes[0].axhline(75.0, color=fs.MUTED, linewidth=0.6, linestyle=(0, (3, 3)))
    axes[0].set_xlabel("时间 / min")
    axes[0].set_ylabel("冷点温度 / °C")
    axes[0].legend(fontsize=6.4, loc="upper left", frameon=False, borderaxespad=0.6)
    axes[0].set_title("四条策略的冷点", fontsize=8.4)
    fs.panel_tag(axes[0], "a")
    axes[1].axhline(0.85, color=fs.HEAT, linewidth=0.8, linestyle=(0, (4, 3)))
    axes[1].text(1, 0.87, "设计线 $\\alpha_m=0.85$", fontsize=6.2, color=fs.HEAT)
    axes[1].set_xlabel("时间 / min")
    axes[1].set_ylabel("致死进度 $\\alpha_m$")
    axes[1].set_title("四条策略的进度", fontsize=8.4)
    fs.panel_tag(axes[1], "b")
    fs.save(fig, "T_policy")


def draw_thick() -> None:
    fig, ax = plt.subplots(figsize=(3.5, 2.7))
    for L, color in ((0.015, fs.SERIES["mpc"]), (0.030, fs.SERIES["dual"]),
                     (0.050, fs.ACCENT)):
        out = run(length=L)
        t = out["time"][:, 0] / 60
        ax.plot(t, out["alpha_m"][:, 0], color=color, linewidth=1.4,
                label=f"{int(L*1000)} mm")
    ax.axhline(0.85, color=fs.HEAT, linewidth=0.8, linestyle=(0, (4, 3)))
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("$\\alpha_m$")
    ax.legend(fontsize=6.6, loc="upper left", frameon=False, borderaxespad=0.6)
    ax.set_title("三种厚度的进度（对偶、组合）", fontsize=8.2)
    ax.annotate("50 mm 走不到设计线", xy=(52, 0.10), xytext=(28, 0.30),
                fontsize=6.0, color=fs.ACCENT,
                arrowprops=dict(arrowstyle="-", color=fs.ACCENT, linewidth=0.5))
    fs.save(fig, "T_thick")


def draw_cook() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.6))
    for cook, name, color in (("steam", "蒸", fs.SERIES["mpc"]),
                              ("bake", "烤", fs.ACCENT),
                              ("combi", "组合", fs.SERIES["dual"])):
        out = run(cook=cook)
        t = out["time"][:, 0] / 60
        axes[0].plot(t, out["alpha_m"][:, 0], color=color, linewidth=1.4,
                     label=name)
        axes[1].plot(t, out["heat"][:, 0], color=color, linewidth=1.1)
    axes[0].axhline(0.85, color=fs.HEAT, linewidth=0.8, linestyle=(0, (4, 3)))
    axes[0].set_xlabel("时间 / min")
    axes[0].set_ylabel("$\\alpha_m$")
    axes[0].legend(fontsize=6.6, loc="lower right")
    axes[0].set_title("三种档位的进度", fontsize=8.4)
    fs.panel_tag(axes[0], "a")
    axes[1].set_xlabel("时间 / min")
    axes[1].set_ylabel("加热指令")
    axes[1].set_title("三种档位的加热", fontsize=8.4)
    fs.panel_tag(axes[1], "b")
    fs.save(fig, "T_cook")


def draw_l50() -> None:
    fig, ax = plt.subplots(figsize=(3.4, 2.6))
    for minutes, color, lab in ((55.0, fs.SERIES["dual"], "55 min"),
                                (70.0, fs.ACCENT, "70 min")):
        out = run(length=0.050, minutes=minutes, gen=BASELINE)
        t = out["time"][:, 0] / 60
        ax.plot(t, out["alpha_m"][:, 0], color=color, linewidth=1.5, label=lab)
    ax.axhline(0.85, color=fs.HEAT, linewidth=0.8, linestyle=(0, (4, 3)))
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("$\\alpha_m$")
    ax.legend(fontsize=6.8, loc="lower right", frameon=False, borderaxespad=0.6)
    ax.set_title("50 mm：延长时域才到设计线", fontsize=8.2)
    ax.annotate("55 min 停在 0.068", xy=(54, 0.07), xytext=(26, 0.28),
                fontsize=6.0, color=fs.SERIES["dual"],
                arrowprops=dict(arrowstyle="-", color=fs.SERIES["dual"],
                                linewidth=0.5))
    fs.save(fig, "T_l50")


def draw_ant() -> None:
    pairs = json.loads((LOG / "antoine_pairs.json").read_text(encoding="utf-8"))
    thick = [15, 30, 50]
    med = []
    for L in thick:
        on = [r["e_alpha"] for r in pairs if r["length_mm"] == L and r["antoine"]]
        off = [r["e_alpha"] for r in pairs if r["length_mm"] == L and not r["antoine"]]
        med.append(float(np.median(np.array(on) - np.array(off))))
    fig, ax = plt.subplots(figsize=(3.3, 2.5))
    colors = [fs.SERIES["mpc"] if m > 0 else fs.HEAT for m in med]
    bars = ax.bar([str(t) for t in thick], med, color=colors, width=0.55,
                  edgecolor="none")
    ax.axhline(0.0, color=fs.INK, linewidth=0.8)
    for b, m in zip(bars, med):
        ax.text(b.get_x() + b.get_width() / 2,
                m + (0.03 if m > 0 else -0.06), f"{m:+.3f}",
                ha="center", va="bottom" if m > 0 else "top", fontsize=6.6)
    ax.set_xlabel("厚度 / mm")
    ax.set_ylabel("$\\Delta e_\\alpha$（打开 $-$ 关闭）")
    ax.set_ylim(-0.22, 0.78)
    ax.set_title("蒸汽压差项的符号随厚度翻转", fontsize=8.2)
    fs.save(fig, "T_ant")


def draw_s2() -> None:
    s2 = json.loads((LOG / "s2_summary.json").read_text(encoding="utf-8"))
    groups = [
        ("探针", [("对偶", "probe", "dual"), ("无探针", "probe", "mpc")]),
        ("读数保持", [("0 s", "occlude", "0"), ("60 s", "occlude", "60")]),
        ("边界", [("无夹层", "fat", "off"), ("有夹层", "fat", "on"),
                  ("开门", "door", "at300")]),
    ]
    fig, ax = plt.subplots(figsize=(3.6, 2.7))
    x = 0.0
    ticks, labels = [], []
    for name, items in groups:
        for lab, fac, lv in items:
            v = [r["e_alpha"] for r in s2 if r["factor"] == fac and r["level"] == lv]
            med = float(np.median(v))
            ax.scatter([x], [med], s=38, color=fs.SERIES["dual"], zorder=4,
                       edgecolor="white", linewidth=0.5)
            ax.plot([x - 0.12, x], [float(np.percentile(v, 10))] * 2,
                    color=fs.MUTED, linewidth=0.6)
            ax.plot([x - 0.12, x], [float(np.percentile(v, 90))] * 2,
                    color=fs.MUTED, linewidth=0.6)
            ax.plot([x - 0.12] * 2,
                    [float(np.percentile(v, 10)), float(np.percentile(v, 90))],
                    color=fs.MUTED, linewidth=0.6)
            ticks.append(x)
            labels.append(lab)
            x += 1.0
        x += 0.55
        ax.text(x - 0.55 - len(items) / 2, -0.86, name, ha="center",
                fontsize=6.6, color=fs.MUTED)
    ax.axhline(0.0, color=fs.INK, linewidth=0.7, linestyle=(0, (4, 3)))
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels, fontsize=6.2)
    ax.set_ylabel("$e_\\alpha$ 中位与十分位--九十分位")
    ax.set_ylim(-0.95, 0.10)
    ax.set_title("S2 边界扫描：每个因子相对基线", fontsize=8.2)
    fs.save(fig, "T_s2")


def main() -> None:
    fs.setup()
    draw_policy()
    draw_thick()
    draw_cook()
    draw_l50()
    draw_ant()
    draw_s2()


if __name__ == "__main__":
    main()
