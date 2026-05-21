"""
models/figures/fig_04c_regime_overlay.py

Target: Fig. 4(c) — Regime markers on benchmark ceiling map (Layer 4 SI).

Shows the Layer 2 reversible methane benchmark surface in the same broad
visual style as Fig. 2b, with valid Layer 4 R134a architecture-space cases
overlaid as fuel-flow regime markers.

Data provenance:
    Layer 2: data/independent/benchmark_surface.csv — entropy-balance theorem
    Layer 4: data/brayton_heat_pump_architecture_space/efficiency_distribution.csv
             — R134a first-principles physics, full design-space sweep
             (Gate B compliant: valid rows only, out-of-envelope excluded).

Caption (draft):
    "Layer 4 R134a valid operating cases overlaid on the Layer 2 reversible
     methane benchmark map. The filled background is the reversible ceiling
     Q_H,max/|Delta H_rxn|; markers distinguish Low-, Medium-, and High-flow
     fuel regimes."
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".mplconfig"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.gridspec as gridspec
import matplotlib.colors as mcolors

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import numpy as np
import pandas as pd



# ── Central palette + style system ───────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from models.figures.config import current_palette as _C
from models.figures.style import apply
from models.figures.config.font_config import FONTS
apply()

# ── Fig. 2b-compatible benchmark colormap ───────────────────────────────────
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
_FILLED_LEVELS = np.linspace(_Z_MIN, _Z_CAP, 161)
_COLORBAR_TICKS = np.array([2.5, 3.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, _Z_CAP])
_CONTOUR_LEVELS = np.array([2.5, 3.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, _Z_CAP])
_CAP_LABEL = "16>="

_TXT = _C["text_primary"]
_MUTED = _C["text_secondary"]

_LOW_FLOW = "#0072B2"
_MEDIUM_FLOW = "#E69F00"
_HIGH_FLOW = "#FFFFFF"

WORKED_CASE_T_COLD_K = 283.15  # 10°C source
WORKED_CASE_T_HOT_K = 333.15   # 60°C delivery

def _lookup_worked_case_multiplier(benchmark_df):
    """Find the nearest benchmark multiplier for the worked-case temperatures."""
    # Find nearest t_cold_k row.
    cold_idx = (benchmark_df["t_cold_k"] - WORKED_CASE_T_COLD_K).abs().idxmin()
    cold_val = benchmark_df.loc[cold_idx, "t_cold_k"]
    # Among rows with that t_cold_k, find nearest t_hot_k.
    same_cold = benchmark_df[benchmark_df["t_cold_k"] == cold_val]
    hot_idx = (same_cold["t_hot_k"] - WORKED_CASE_T_HOT_K).abs().idxmin()
    return float(benchmark_df.loc[hot_idx, "multiplier"])


REGIME_ORDER = ["Low Flow", "Medium Flow", "High Flow"]
REGIME_STYLES = {
    "Low Flow": {"color": _LOW_FLOW, "marker": "o"},
    "Medium Flow": {"color": _MEDIUM_FLOW, "marker": "s"},
    "High Flow": {"color": _HIGH_FLOW, "marker": "o"},
}


# ── Output path ──────────────────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PREFIX = OUTPUT_DIR / "fig_04c_regime_overlay"


def load_architecture_space_data():
    """Load Layer 4 architecture-space data and assign fuel-flow regimes.

    Reads from efficiency_distribution.csv (full design-space sweep).
    Handles both column naming conventions:
        - Full run: fuel_flow, t_source, t_sink, cop_hp
        - Legacy multivariate: fuel_flow_kg_s, t_source_c, t_sink_c

    Returns a DataFrame with columns including:
        fuel_flow_kg_s, t_source_c, t_sink_c, eta_effective, cop_hp, fuel_regime
    Only status == valid rows are returned (Gate B compliance).

    For large datasets (>50k points), returns subsampled scatter data
    and a separate full_df for hull computation.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    data_path = (
        project_root
        / "data"
        / "brayton_heat_pump_architecture_space"
        / "efficiency_distribution.csv"
    )
    df = pd.read_csv(data_path)

    # Gate B: only valid rows.
    df = df[df["is_valid"] == True].copy()

    # Normalize column names for both full-run and legacy formats.
    if "fuel_flow_kg_s" not in df.columns:
        df = df.rename(columns={
            "fuel_flow": "fuel_flow_kg_s",
            "t_source": "t_source_c",
            "t_sink": "t_sink_c",
        })
    # Ensure t_sink_c exists (full run includes it; legacy may not).
    if "t_sink_c" not in df.columns:
        df["t_sink_c"] = np.nan
    # eta_sys -> eta_effective alias.
    if "eta_effective" not in df.columns and "eta_sys" in df.columns:
        df = df.rename(columns={"eta_sys": "eta_effective"})

    # Assign regimes by fuel-flow tertiles from the same valid rows.
    df["fuel_regime"] = pd.qcut(
        df["fuel_flow_kg_s"],
        q=3,
        labels=REGIME_ORDER,
    )
    df["t_source_k"] = df["t_source_c"] + 273.15
    df["t_sink_k"] = df["t_sink_c"] + 273.15

    # Low and Medium flow are zero/near-zero-flow boundary artefacts with no
    # meaningful heating; keep only High Flow for the figure overlay.
    df = df[df["fuel_regime"] == "High Flow"].copy()
    df["fuel_regime"] = df["fuel_regime"].cat.remove_unused_categories()
    df["t_source_k"] = df["t_source_c"] + 273.15
    df["t_sink_k"] = df["t_sink_c"] + 273.15

    # For large datasets, subsample scatter points for rendering performance.
    MAX_SCATTER_POINTS = 5000
    if len(df) > MAX_SCATTER_POINTS:
        n_scatter = min(MAX_SCATTER_POINTS, len(df))
        rng = np.random.RandomState(42)
        scatter_idx = rng.choice(len(df), size=n_scatter, replace=False)
        scatter_df = df.iloc[scatter_idx].copy()
    else:
        scatter_df = df.copy()

    print(f"Loaded {len(df)} Layer 4 valid High-Flow points ("
          f"{len(scatter_df):,} for rendering).")
    return df, scatter_df


def load_benchmark_surface():
    """Load Layer 2 reversible benchmark surface from consolidated data/."""
    project_root = Path(__file__).resolve().parent.parent.parent
    csv_path = project_root / "data" / "independent" / "benchmark_surface.csv"
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} Layer 2 benchmark surface points from {csv_path.name} "
          f"(T_cold: {df['t_cold_k'].min():.0f}–{df['t_cold_k'].max():.0f} K, "
          f"T_hot: {df['t_hot_k'].min():.0f}–{df['t_hot_k'].max():.0f} K)")
    return df


def build_benchmark_grid(benchmark_df):
    """Build a raw (no-interpolation) grid from the benchmark surface CSV.

    Pivots t_cold_k × t_hot_k → multiplier, then masks all cells below
    the T_H = T_C diagonal so they render as white.
    """
    pivot = benchmark_df.pivot(index="t_hot_k", columns="t_cold_k", values="multiplier")
    y_vals = np.sort(pivot.index)
    x_vals = np.sort(pivot.columns)
    x_grid, y_grid = np.meshgrid(x_vals, y_vals)
    z_grid = pivot.values.astype(float)

    # Mask below the diagonal (T_H <= T_C → no heating possible).
    z_grid[y_grid <= x_grid] = np.nan

    return x_vals, y_vals, z_grid


def plot_overlay(full_df, scatter_df, benchmark_df):
    """Generate the revised Fig. 4c regime-overlay benchmark map.

    Args:
        full_df: complete valid dataset (for hull computation)
        scatter_df: subsampled or full (for scatter rendering)
        benchmark_df: Layer 2 benchmark surface
    """
    fig = plt.figure(figsize=(8.6, 10.5))
    fig.patch.set_facecolor("white")

    # Square plot area (7.0 × 7.0 inches) centred horizontally,
    # with colourbar below.
    plot_w = 7.0
    plot_h = 7.0
    x0 = (8.6 - plot_w) / 2       # left edge in figure coords
    y0 = 2.5 / 10.5                # bottom edge of plot area (lifted for title)
    ax = fig.add_axes([x0 / 8.6, y0, plot_w / 8.6, plot_h / 10.5])
    cbar_ax = fig.add_axes([x0 / 8.6, 0.14, plot_w / 8.6, 0.04])

    x_vals, y_vals, z_grid = build_benchmark_grid(benchmark_df)
    x_zoom, y_zoom = np.meshgrid(x_vals, y_vals)
    z_min = _Z_MIN
    z_max = _Z_CAP
    norm = mcolors.PowerNorm(gamma=0.6, vmin=z_min, vmax=z_max)

    # ── Axis limits (must be set before diagonal-line computation) ─────
    x_min, x_max = 243.15, 310.15   # -30 to 37 °C
    y_min, y_max = 283.15, 353.15   # 10 to 80 °C
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

    # ── Annotated diagonal lines only (z = 2, 4, 6, …) ─────────────────
    _ANNOTATE_Z = [2, 4, 6, 8, 10, 12, 14, 18, 24]
    dy = y_max - y_min
    _ANNOTATED_X0 = []  # store for annotation pass below

    for z_target in _ANNOTATE_Z:
        best_x0 = None
        best_diff = float("inf")
        for x0 in np.arange(x_min - dy, x_max + dy, 6):
            xm = x0 + dy / 2
            mid_y = (y_min + y_max) / 2
            zi = np.searchsorted(x_vals, xm)
            yj = np.searchsorted(y_vals, mid_y)
            if 0 <= zi < len(x_vals) and 0 <= yj < len(z_grid):
                zval = z_grid[yj, zi]
                if not np.isnan(zval):
                    diff = abs(zval - z_target)
                    if diff < best_diff:
                        best_diff = diff
                        best_x0 = x0

        if best_x0 is not None and best_diff < 2.0:
            # Determine line colour from the midpoint z-value on the
            # benchmark surface (same logic as the old hatch function).
            xm = best_x0 + dy / 2
            ym = (y_min + y_max) / 2
            zi = np.searchsorted(x_vals, xm)
            yj = np.searchsorted(y_vals, ym)
            if 0 <= zi < len(x_vals) and 0 <= yj < len(y_vals):
                zval = z_grid[yj, zi]
                if not np.isnan(zval):
                    line_color = _cmap(float(np.clip((zval - z_min) / (z_max - z_min), 0, 1)))
                else:
                    line_color = "#cccccc"
            else:
                line_color = "#cccccc"
            _ANNOTATED_X0.append((best_x0, z_target, line_color))
            # Draw the diagonal line across the plot.
            ax.plot(
                [best_x0, best_x0 + dy],
                [y_min, y_max],
                color=line_color,
                linewidth=1.0,
                alpha=0.7,
                zorder=2,
            )



    # ── Annotate each diagonal line at its exit edge ───────────────────
    for best_x0, z_target, _line_color in _ANNOTATED_X0:
        # Trace the diagonal to the top-right plot edge.
        y_at_xmax = x_max - best_x0 + y_min
        if y_at_xmax <= y_max:
            # Exits at right edge
            lx, ly = x_max, y_at_xmax
        else:
            # Exits at top edge
            lx = best_x0 + y_max - y_min
            ly = y_max
        ax.annotate(
            f"{int(z_target)}",
            xy=(lx, ly),
            rotation=45,
            fontsize=FONTS["reference"],
            color="#333333",
            ha="left",
            va="bottom",
            zorder=3,
        )



    # ── Diagonal reference: T_H = T_C (45° line) ─────────────────────────
    # In Kelvin the diagonal is y = x. It enters at (283.15, 283.15) and
    # exits at whichever axis limit is hit first.
    diag_x0 = max(x_min, y_min)  # 283.15 K — bottom-left of valid heating zone
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
        "No heating below\n$T_H = T_C$",
        xy=(292, 287),
        ha="left",
        va="bottom",
        fontsize=FONTS["reference"],
        color="black",
        style="italic",
        zorder=3,
    )

    # Render High-Flow architecture cases as a hexbin density overlay.
    sub = scatter_df[scatter_df["fuel_regime"] == "High Flow"]
    hb = ax.hexbin(
        sub["t_source_k"],
        sub["t_sink_k"],
        gridsize=60,
        cmap="Reds",
        mincnt=1,
        edgecolors="#333333",
        linewidths=0.25,
        zorder=8,
    )
    # Hexbin density colourbar at the bottom.
    hb_cbar = fig.colorbar(hb, cax=cbar_ax, orientation="horizontal",
                           ticks=[1, 3, 5, 7, 9, 11])
    hb_cbar.set_label("Points per hexagon", fontsize=FONTS["colorbar"],
                      color=_TXT, labelpad=8)
    hb_cbar.outline.set_linewidth(0.6)

    # Look up the worked-case multiplier from the raw benchmark grid.
    worked_multiplier = _lookup_worked_case_multiplier(benchmark_df)
    ax.scatter(
        [WORKED_CASE_T_COLD_K],
        [WORKED_CASE_T_HOT_K],
        marker="*",
        s=350,
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
        xytext=(WORKED_CASE_T_COLD_K + 5.2, WORKED_CASE_T_HOT_K + 6.5),
        ha="left",
        va="center",
        fontsize=FONTS["annotation"],
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

    ax.set_xlabel(r"Source temperature $T_C$ ($^\circ$C)",
                  fontsize=FONTS["axis_label"], color=_TXT)
    ax.set_ylabel(r"Sink temperature $T_H$ ($^\circ$C)",
                  fontsize=FONTS["axis_label"], color=_TXT)

    x_ticks = np.array([243.15, 253.15, 263.15, 273.15, 283.15, 293.15, 303.15, 310.15])
    y_ticks = np.array([283.15, 293.15, 303.15, 313.15, 323.15, 333.15, 343.15, 353.15])
    ax.set_xticks(x_ticks)
    ax.set_xticklabels([f"{t - 273:.0f}" for t in x_ticks])
    ax.set_yticks(y_ticks)
    ax.set_yticklabels([f"{t - 273:.0f}" for t in y_ticks])
    ax.tick_params(axis="both", labelsize=FONTS["tick"])

    ax.set_title(
        r"High-flow R134a architecture cases on the reversible heating ceiling",
        pad=28,
        fontsize=FONTS["title"],
        fontweight="bold",
        color=_TXT,
    )

    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.6)


    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    return fig


if __name__ == "__main__":
    full_df, scatter_df = load_architecture_space_data()
    benchmark_df = load_benchmark_surface()
    fig = plot_overlay(full_df, scatter_df, benchmark_df)

    # ── Save ───────────────────────────────────────────────────────────────
    fig.savefig(OUTPUT_PREFIX.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"Figure saved to {OUTPUT_DIR}")

    # ── Data summary ───────────────────────────────────────────────────────
    print(f"\nLayer 4 High-Flow positions on T_C × T_H design map:")
    sub = full_df[full_df["fuel_regime"] == "High Flow"]
    print(f"  {'High Flow':11s} | n={len(sub):>6,} | "
          f"T_source={sub.t_source_c.min():.0f}–{sub.t_source_c.max():.0f} °C, "
          f"T_sink={sub.t_sink_c.min():.0f}–{sub.t_sink_c.max():.0f} °C")
