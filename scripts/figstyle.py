"""Publication-grade figure style for the monograph.

Every figure in the paper goes through this module so the typography, colour,
spacing and annotation conventions are shared. It exists because the previous
figures were drawn ad hoc: heatmaps came out as 4x3 blocks of flat colour,
violin plots collapsed into threads, and no two figures agreed on a palette.

Conventions:

* one palette, one ink, one muted grey, two accents;
* no chartjunk: no top/right spines, no grid behind data-dense panels;
* every panel carries units, every axis a readable label at 8.6 pt;
* contour/phase panels get thin isolines and inline labels, not colour blocks;
* uncertainty is drawn (bands, error bars), never implied by a point.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.ticker import MaxNLocator

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "results" / "figures" / "paper"
LOG = ROOT / "results" / "logs"

# -- palette ---------------------------------------------------------------
INK = "#171717"
MUTED = "#6b6b6b"
FAINT = "#b9b9b9"
GRID = "#e2e2e2"
PAPER = "#ffffff"

SERIES = {
    "open": "#8a8a8a",
    "pid": "#c96a3f",
    "mpc": "#3f7a8c",
    "dual": "#1f4e79",
}
SERIES_CN = {"open": "开环", "pid": "腔温比例", "mpc": "无探针", "dual": "对偶"}
ACCENT = "#b8860b"
HEAT = "#c0502a"
COLD = "#2b5f80"

# Sequential: paper-white through sand to deep blue. Reads well in print and
# in greyscale, because lightness is monotone.
SEQ = LinearSegmentedColormap.from_list(
    "acts_seq", ["#f7f5f0", "#e8ddca", "#c9b48c", "#8f9c9e", "#4b6e83", "#1f3f58"]
)
# Diverging around zero (the design line), so a zero crossing is visible.
DIV = LinearSegmentedColormap.from_list(
    "acts_div", ["#8c2f1f", "#c26a4a", "#e6bfa8", "#f4f1ea", "#a9c3d0", "#4a7fa0", "#173f63"]
)
# Phase: four distinguishable hues for policy panels.
PHASE = LinearSegmentedColormap.from_list(
    "acts_phase", ["#f4f1ea", "#d9c9a8", "#9fb0a6", "#5f8496", "#2c5673"]
)


def setup() -> None:
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
        "mathtext.fontset": "dejavusans",
        "axes.unicode_minus": False,
        "figure.facecolor": PAPER,
        "savefig.facecolor": PAPER,
        "axes.facecolor": PAPER,
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "text.color": INK,
        "axes.linewidth": 0.7,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "grid.color": GRID,
        "grid.linewidth": 0.5,
        "legend.frameon": False,
        "legend.fontsize": 7.6,
        "legend.handlelength": 1.6,
        "savefig.dpi": 400,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.04,
        "font.size": 8.6,
        "axes.titlesize": 9.0,
        "axes.labelsize": 8.6,
        "xtick.labelsize": 7.6,
        "ytick.labelsize": 7.6,
        "figure.constrained_layout.use": True,
        "figure.constrained_layout.h_pad": 0.05,
        "figure.constrained_layout.w_pad": 0.05,
        "lines.linewidth": 1.3,
        "lines.solid_capstyle": "round",
        "lines.solid_joinstyle": "round",
        "patch.linewidth": 0.6,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.width": 0.7,
        "ytick.major.width": 0.7,
        "xtick.major.size": 2.4,
        "ytick.major.size": 2.4,
    })


def save(fig, name: str, vector: bool = True) -> None:
    """Write one figure as PDF (for LaTeX) and PNG (for quick inspection)."""
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / f"{name}.pdf")
    fig.savefig(FIG / f"{name}.png", dpi=400)
    plt.close(fig)
    print("  wrote", name)


def panel_tag(ax, tag: str) -> None:
    """Panel letter outside the axes, top-left, so it never collides with the title."""
    ax.text(-0.085, 1.03, tag, transform=ax.transAxes, ha="left", va="bottom",
            fontsize=9.2, fontweight="bold", color=INK, clip_on=False)


def zero_line(ax, horizontal: bool = True, label: str | None = None) -> None:
    if horizontal:
        ax.axhline(0.0, color=INK, linewidth=0.7, linestyle=(0, (4, 3)), zorder=0.5)
        if label:
            ax.text(ax.get_xlim()[1], 0.0, " " + label, ha="right", va="bottom",
                    fontsize=7.0, color=MUTED)
    else:
        ax.axvline(0.0, color=INK, linewidth=0.7, linestyle=(0, (4, 3)), zorder=0.5)


def isoline_panel(ax, x, y, z, *, levels: int = 9, cmap=SEQ, fmt="%+.2f",
                  cbar: bool = True, label_step: int = 2, vmin=None, vmax=None,
                  extend: str = "both"):
    """A contour panel with thin isolines and inline labels.

    This is the replacement for the imshow heatmaps: filled contour with a
    controlled number of levels, isolines drawn on top, and values written
    along the lines so the reader can actually read the field without a
    legend lookup.
    """
    vmin = float(np.nanmin(z)) if vmin is None else vmin
    vmax = float(np.nanmax(z)) if vmax is None else vmax
    lv = np.linspace(vmin, vmax, levels)
    cf = ax.contourf(x, y, z, levels=lv, cmap=cmap, extend=extend,
                     antialiased=True, alpha=0.95)
    cs = ax.contour(x, y, z, levels=lv[::label_step], colors=INK,
                    linewidths=0.45, alpha=0.55)
    ax.clabel(cs, inline=True, fontsize=6.2, fmt=fmt, colors=INK)
    ax.set_xticks(x) if len(x) <= 8 else ax.xaxis.set_major_locator(MaxNLocator(6))
    ax.set_yticks(y) if len(y) <= 8 else ax.yaxis.set_major_locator(MaxNLocator(6))
    if cbar:
        cb = ax.figure.colorbar(cf, ax=ax, pad=0.015, fraction=0.046)
        cb.outline.set_linewidth(0.45)
        cb.ax.tick_params(labelsize=6.8, width=0.5, length=2)
        return cf, cs, cb
    return cf, cs, None


def band(ax, x, lo, hi, color, alpha: float = 0.16, label: str | None = None):
    """A fill_between band used for credible intervals."""
    ax.fill_between(x, lo, hi, color=color, alpha=alpha, linewidth=0,
                    label=label, zorder=1)


def grid_data(rows):
    """Turn a list of dicts with length_mm, t0, e_p50 into an (y, x, z) grid."""
    xs = sorted({r["length_mm"] for r in rows})
    ys = sorted({r["t0"] for r in rows})
    z = np.full((len(ys), len(xs)), np.nan)
    xi = {v: i for i, v in enumerate(xs)}
    yi = {v: i for i, v in enumerate(ys)}
    for r in rows:
        z[yi[r["t0"]], xi[r["length_mm"]]] = r["e_p50"]
    return np.array(xs), np.array(ys), z


def mechanism_box(ax, xy, w, h, title, body, color, *, title_size=8.6,
                  body_size=7.0):
    """A rounded box used by the mechanism diagrams."""
    x, y = xy
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.018,rounding_size=0.06",
        linewidth=0.9, edgecolor=color, facecolor=color + "12", zorder=2,
    ))
    ax.text(x + w / 2, y + h - 0.115, title, ha="center", va="center",
            fontsize=title_size, color=color, fontweight="bold", zorder=3)
    ax.text(x + w / 2, y + h / 2 - 0.085, body, ha="center", va="center",
            fontsize=body_size, color=MUTED, linespacing=1.5, zorder=3)


def arrow(ax, start, end, color=MUTED, *, rad=0.0, lw=0.8, ls="-", head=7):
    ax.add_patch(FancyArrowPatch(
        start, end, arrowstyle="-|>", mutation_scale=head, linewidth=lw,
        color=color, linestyle=ls, zorder=1.5,
        connectionstyle=f"arc3,rad={rad}",
    ))
