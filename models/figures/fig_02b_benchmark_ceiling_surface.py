"""
models/figures/fig_02b_benchmark_ceiling_surface.py

Target: Fig. 2(a) — Benchmark ceiling surface for methane.

Shows Q_H,max / |ΔH°| as a filled-contour surface over source temperature
(T_cold) × delivery temperature (T_hot). Zoomed to the domestic-heating
interest zone. Pure Layer 2 — no cycle physics or process-simulator data.
The worked-case marker is the manuscript temperature point evaluated on the
Layer 2 benchmark surface.

Data provenance:
    models/independent/output/benchmark_surface.csv — computed via the
    entropy-balance theorem (SI Note 1 / Layer 2) for methane.

Caption (draft):
    "Reversible heating ceiling for methane across source and delivery
     temperatures. The dimensionless multiplier Q_H,max / |ΔH°| decreases
     with larger temperature lifts, ranging from ~3 at modest lifts to
     ~8–9 near small lifts around domestic hot-water conditions."
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".mplconfig"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ── Central palette + style system ───────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from models.figures.config import current_palette as _C
from models.figures.style import apply
apply()
from models.figures.config.font_config import FONTS

# This contour panel carries a colour bar and is exported on a wider canvas
# than the neighbouring Fig. 2 panel, so it is scaled down more in the
# composite SVG. Use a local font scale to keep the final panel typography
# visually aligned with the right-hand benchmark panel.
_FONT_SCALE = 1.2
_FONTS = {key: size * _FONT_SCALE for key, size in FONTS.items()}

# ── Figure-specific colormap: low red to high yellow
_cmap = mcolors.LinearSegmentedColormap.from_list(
    "benchmark_red_yellow",
    [
        (0.00, "#8b0000"),
        (0.05, "#a50f15"),
        (0.12, "#cb181d"),
        (0.22, "#ef3b2c"),
        (0.34, "#fb6a4a"),
        (0.48, "#fc9272"),
        (0.60, "#fdbb84"),
        (0.70, "#fec44f"),
        (0.80, "#fed976"),
        (0.90, "#fee89a"),
        (1.00, "#fff7bc"),
    ],
    N=256,
)
_cmap.set_over("#fff7bc")

_Z_MIN = 2.5
_Z_CAP = 16.0
_FILLED_LEVELS = np.array([2.5, 3.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, _Z_CAP])
_COLORBAR_TICKS = np.array([2.5, 3.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, _Z_CAP])
_CONTOUR_LEVELS = np.array([2.5, 3.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, _Z_CAP])
_CAP_LABEL = "16>="









_TXT = _C["text_primary"]
_MUTED = _C["text_secondary"]
_REFERENCE = _C["baseline_ref"]

WORKED_CASE_T_COLD_K = 283.15  # 10°C source
WORKED_CASE_T_HOT_K = 333.15   # 60°C delivery


# ── Output path ──────────────────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PREFIX = OUTPUT_DIR / "fig_02b_benchmark_ceiling_surface"


# ── Data loading ─────────────────────────────────────────────────────────────

def load_data():
    """Load benchmark surface from consolidated data/ directory.

    Returns a DataFrame with columns:
        t_cold_k, t_hot_k, multiplier
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    csv_path = project_root / "data" / "independent" / "benchmark_surface.csv"
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows from {csv_path.name} "
          f"(T_cold: {df['t_cold_k'].min():.0f}–{df['t_cold_k'].max():.0f} K, "
          f"T_hot: {df['t_hot_k'].min():.0f}–{df['t_hot_k'].max():.0f} K)")
    return df


# ── Figure generation ────────────────────────────────────────────────────────

def plot_surface(df):
    """Generate the benchmark ceiling contour surface."""
    fig, ax = plt.subplots(figsize=(7.5, 6.0))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # Pivot to grid
    pivot = df.pivot(index="t_hot_k", columns="t_cold_k", values="multiplier")
    y_vals = np.sort(pivot.index)
    x_vals = np.sort(pivot.columns)
    x_grid, y_grid = np.meshgrid(x_vals, y_vals)
    z_grid = pivot.values.astype(float)

    # Mask below the diagonal (T_H <= T_C → no heating possible).
    z_grid[y_grid <= x_grid] = np.nan

    # Axis limits matching Fig. 4c: −30 to 37 °C source, 10 to 80 °C delivery.
    x_min, x_max = 243.15, 310.15
    y_min, y_max = 283.15, 353.15
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

    # Clip to the axis limits for rendering.
    x_clip = (x_grid >= x_min) & (x_grid <= x_max)
    y_clip = (y_grid >= y_min) & (y_grid <= y_max)
    z_clip = np.where(x_clip & y_clip, z_grid, np.nan)

    # Filled field plus white contours: red at low benchmark multipliers
    # and yellow at high multipliers. A continuous power-law normalization
    # keeps the gradient smooth; values above 16 are grouped at the yellow
    # end of the colour scale.
    z_min = _Z_MIN
    z_max = _Z_CAP
    norm = mcolors.BoundaryNorm(_FILLED_LEVELS, _cmap.N, extend="max")
    ax.contourf(
        x_grid, y_grid, z_clip,
        levels=_FILLED_LEVELS,
        cmap=_cmap,
        norm=norm,
        extend="max",
        alpha=0.98,
    )
    cs = ax.contour(
        x_grid, y_grid, z_clip,
        levels=_CONTOUR_LEVELS,
        colors="white",
        linewidths=0.85,
        alpha=0.82,
    )
    contour_fmt = {level: (_CAP_LABEL if level == _Z_CAP else f"{level:.0f}")
                   for level in _CONTOUR_LEVELS}
    labels = ax.clabel(
        cs,
        inline=True,
        fontsize=_FONTS["contour"],
        fmt=contour_fmt,
        inline_spacing=8,
    )
    for label in labels:
        label.set_color(_TXT)
        label.set_fontweight("bold")
        label.set_path_effects([
            pe.Stroke(linewidth=2.0, foreground="white"),
            pe.Normal(),
        ])

    # Colour bar — dimensionless multiplier
    norm = mcolors.BoundaryNorm(_FILLED_LEVELS, _cmap.N, extend="max")
    sm = plt.cm.ScalarMappable(norm=norm, cmap=_cmap)
    sm.set_array([])
    cbar = fig.colorbar(
        sm,
        ax=ax,
        orientation="vertical",
        fraction=0.050,
        pad=0.085,
        ticks=_COLORBAR_TICKS,
        extend="max",
    )
    cbar.ax.set_yticklabels(
        [_CAP_LABEL if tick == _Z_CAP else f"{tick:.0f}" for tick in _COLORBAR_TICKS]
    )
    cbar.ax.tick_params(labelsize=_FONTS["tick"])
    cbar.set_label(
        r"$Q_{\mathrm{H}}^{\max} / |\Delta H^\circ_{\mathrm{rxn}}|$",
        fontsize=_FONTS["colorbar"],
        color=_TXT,
        labelpad=10,
    )
    cbar.outline.set_linewidth(0.6)

    # Diagonal reference: T_H = T_C (45° line) — physically unrealistic below.
    diag_x0 = max(x_min, y_min)  # 283.15 K
    diag_x1 = min(x_max, y_max)  # whichever bound is tighter
    ax.plot(
        [diag_x0, diag_x1],
        [diag_x0, diag_x1],
        color="black",
        linewidth=1.0,
        linestyle="--",
        zorder=3,
    )
    ax.annotate(
        "No heating for\n$T_H < T_C$",
        xy=(292, 285),
        ha="left",
        va="bottom",
        fontsize=_FONTS["reference"],
        color="black",
        style="italic",
        zorder=3,
    )

    # Look up the worked-case multiplier from the raw benchmark grid.
    cold_idx = np.argmin(np.abs(x_vals - WORKED_CASE_T_COLD_K))
    hot_idx = np.argmin(np.abs(y_vals - WORKED_CASE_T_HOT_K))
    worked_multiplier = float(z_grid[hot_idx, cold_idx])
    ax.scatter(
        [WORKED_CASE_T_COLD_K],
        [WORKED_CASE_T_HOT_K],
        marker="*",
        s=360,
        facecolor="#111111",
        edgecolor="white",
        linewidth=0.9,
        zorder=10,
    )
    ax.annotate(
        "Manuscript case\n"
        + r"$T_C = 10^\circ$C" + "\n"
        + r"$T_H = 60^\circ$C" + "\n"
        + rf"Ceiling $\approx {worked_multiplier:.1f}$",
        xy=(WORKED_CASE_T_COLD_K, WORKED_CASE_T_HOT_K),
        xytext=(WORKED_CASE_T_COLD_K - 12.0, WORKED_CASE_T_HOT_K - 8.0),
        ha="right",
        va="center",
        fontsize=_FONTS["annotation"],
        color=_TXT,
        bbox=dict(
            boxstyle="round,pad=0.42",
            facecolor="white",
            edgecolor="#777777",
            linewidth=0.7,
        ),
        arrowprops=dict(
            arrowstyle="-|>",
            color="#111111",
            linewidth=0.9,
            shrinkA=0,
            shrinkB=8,
        ),
        zorder=11,
    )

    # Axis formatting — Celsius for readability
    ax.set_xlabel(r"Source temperature $T_C$ ($^\circ$C)",
                  fontsize=_FONTS["axis_label"], color=_TXT)
    ax.set_ylabel(r"Sink temperature $T_H$ ($^\circ$C)",
                  fontsize=_FONTS["axis_label"], color=_TXT)

    # Convert axis ticks to Celsius for display
    x_ticks = np.array([243.15, 253.15, 263.15, 273.15, 283.15, 293.15, 303.15, 310.15])
    y_ticks = np.array([283.15, 293.15, 303.15, 313.15, 323.15, 333.15, 343.15, 353.15])
    ax.set_xticks(x_ticks)
    ax.set_xticklabels([f"{t - 273:.0f}" for t in x_ticks])
    ax.set_yticks(y_ticks)
    ax.set_yticklabels([f"{t - 273:.0f}" for t in y_ticks])
    ax.tick_params(axis="both", labelsize=_FONTS["tick"])

    # Title
    ax.set_title(
        r"Reversible heating ceiling $Q_H^{\max}/|\Delta H^\circ_{\mathrm{rxn}}|$ (–)",
        pad=12, fontsize=_FONTS["title"], fontweight="bold", color=_TXT,
    )

    # Grid and spines
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.6)

    fig.tight_layout()
    return fig


if __name__ == "__main__":
    df = load_data()
    fig = plot_surface(df)

    # ── Save ───────────────────────────────────────────────────────────────
    fig.savefig(OUTPUT_PREFIX.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"Figure saved to {OUTPUT_DIR}")
