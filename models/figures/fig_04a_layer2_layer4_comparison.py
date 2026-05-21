"""
models/figures/fig_04a_layer2_layer4_comparison.py

Target: Fig. 4(a) — Layer 2 reversible benchmark vs Layer 4 architecture-space
        comparison (compact contour panel with valid-region boundary).

Phase: DRAFT -> ITERATION 1 -> MANUSCRIPT-READY
Status: DRAFT

Shows the Brayton heat-pump architecture-space occupation of the
reversible methane benchmark space as a filled-contour plot with labelled
iso-fraction lines and overlay of valid operating points.

Layer 2 (reversible benchmark): Q_H,max / |ΔH°| from entropy-balance theorem.
Layer 4 (Brayton heat-pump): R134a cycle physics with explicit efficiency parameters.

Data provenance:
    Source: models/thermodynamic/brayton_heat_pump_architecture_space/output/layer2_layer4_comparison.csv
    Filtered to status == valid rows only.
    Methane basis, predictive mode, source-temperature × fuel-flow scale sweep.
    Normalisation: Layer 4 delivered heat / Layer 2 reversible ceiling at matching
    source and emergent sink temperatures.

Caption (draft):
    "Brayton heat-pump architecture-space occupation of the reversible methane
     benchmark. Contours show the ratio of whole-system useful delivery
     (Layer 4) to the reversible ceiling (Layer 2) across source temperature
     and fuel-flow scale. White contour lines are labelled; grey dots mark
     valid R134a operating points. The triangular valid-region boundary
     reflects R134a envelope constraints. The architecture occupies a bounded
     subset (0.248–0.263) of the reversible ceiling, with higher fractions
     at low source temperature and high fuel-flow scale."
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".mplconfig"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ── Central palette + style system ───────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from models.figures.config import current_palette as _C, sequential_colormap
from models.figures.style import apply
apply()
from models.figures.config.font_config import FONTS

_BG = _C["background"]
_GRID = _C["grid"]
_TXT = _C["text_primary"]
_TXT_SEC = _C["text_secondary"]
_FRACTION_CMAP = sequential_colormap(["cold", "hot", "peak"], N=256)


# ── Output path ──────────────────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PREFIX = OUTPUT_DIR / "fig_04a_layer2_layer4_comparison"


# ── Data loading ─────────────────────────────────────────────────────────────

def load_data():
    """Load Layer 2/4 comparison from consolidated data/ and filter to valid rows."""
    project_root = Path(__file__).resolve().parent.parent.parent
    data_path = project_root / "data" / "brayton_heat_pump_architecture_space" / "layer2_layer4_comparison.csv"
    df = pd.read_csv(data_path)

    # Enforce valid-row filter
    valid = df[df["status"] == "valid"].copy()

    print(f"Loaded {len(df)} total rows from {data_path.name}.")
    print(f"Filtered to {len(valid)} valid rows for plotting.")
    print(f"Fuel flow range: {valid['fuel_flow_kg_s'].min():.4f}–{valid['fuel_flow_kg_s'].max():.4f} kg/s")
    print(f"Source temp range: {valid['t_source_c'].min():.1f}–{valid['t_source_c'].max():.1f} °C")
    print(f"Total fraction range: {valid['layer4_total_fraction_of_layer2'].min():.4f}–{valid['layer4_total_fraction_of_layer2'].max():.4f}")

    return valid


def build_grid(df, n_levels=50):
    """Build a regular grid for contour interpolation from scattered valid data."""
    # Extract unique sorted coordinates
    fuel_flows = np.sort(df["fuel_flow_kg_s"].unique())
    source_temps = np.sort(df["t_source_c"].unique())

    # Create mesh grid
    FF, ST = np.meshgrid(fuel_flows, source_temps)

    # Build lookup from (fuel_flow, t_source) -> fraction
    lookup = {}
    for _, row in df.iterrows():
        key = (row["fuel_flow_kg_s"], row["t_source_c"])
        lookup[key] = row["layer4_total_fraction_of_layer2"]

    # Fill grid — use NaN for missing cells, then interpolate
    Z = np.full_like(FF, np.nan)
    for i in range(len(source_temps)):
        for j in range(len(fuel_flows)):
            key = (fuel_flows[j], source_temps[i])
            if key in lookup:
                Z[i, j] = lookup[key]

    # Linear interpolation for any missing cells within the convex hull
    mask = np.isnan(Z)
    if mask.any():
        from scipy.interpolate import griddata
        points = np.column_stack([FF[~mask].ravel(), ST[~mask].ravel()])
        values = Z[~mask].ravel()
        missing_pts = np.column_stack([FF[mask].ravel(), ST[mask].ravel()])
        Z[mask] = griddata(
            points, values,
            missing_pts,
            method="linear",
        )

    return FF, ST, Z, fuel_flows, source_temps


# ── Figure generation ────────────────────────────────────────────────────────

def plot_contour(df):
    """Generate compact Layer 2/4 comparison contour plot."""
    fig, ax = plt.subplots(figsize=(6.5, 5.0))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)

    # Build grid
    FF, ST, Z, fuel_flows, source_temps = build_grid(df)

    # Contour levels — evenly spaced across the narrow fraction range
    frac_min = df["layer4_total_fraction_of_layer2"].min()
    frac_max = df["layer4_total_fraction_of_layer2"].max()
    n_levels = 15
    levels = np.linspace(frac_min, frac_max, n_levels)

    # Filled contours use the active palette, so palette changes are visible
    # in this panel as well as in categorical plots.
    cf = ax.contourf(
        FF, ST, Z,
        levels=levels,
        cmap=_FRACTION_CMAP,
        extend="both",
    )

    # Contour lines — white outline + dark inner line for readability
    cs = ax.contour(
        FF, ST, Z,
        levels=levels[::3],  # every 3rd level for line labels
        colors="white",
        linewidths=1.2,
        alpha=0.7,
    )
    # Dark inner lines on top of white outline — slightly thicker for visual weight
    ax.contour(
        FF, ST, Z,
        levels=levels[::3],  # every 3rd level for line labels
        colors=_TXT_SEC,
        linewidths=0.8,
        alpha=0.8,
    )

    # Add contour line labels — bold text with thin white outline
    try:
        import matplotlib.patheffects as path_effects
        clabels = ax.clabel(cs, inline=True, fontsize=FONTS["contour"], fmt="%.3f",
                            inline_spacing=8, colors=_TXT_SEC)
        for t in clabels:
            t.set_fontweight("bold")
            t.set_path_effects([
                path_effects.withStroke(linewidth=0.6, foreground="white"),
                path_effects.Normal(),  # draw bold text on top of thin white stroke
            ])
    except Exception:
        pass

    # Colour bar — fraction of reversible ceiling
    cbar = fig.colorbar(cf, ax=ax, shrink=0.75, pad=0.02)
    cbar.set_label(
        r"$Q_{\mathrm{out}}^{\mathrm{total}} / Q_H^{\max}$",
        fontsize=FONTS["colorbar"],
        color=_TXT,
    )
    # Apply path effects to colour bar label
    cbar_label_text = cbar.ax.yaxis.get_label()
    cbar_label_text.set_path_effects([
        path_effects.withStroke(linewidth=0.5, foreground="white"),
        path_effects.Normal(),
    ])
    cbar.ax.yaxis.set_tick_params(color=_TXT_SEC)
    plt.setp(cbar.ax.get_yticklabels(), color=_TXT_SEC)
    plt.setp(cbar.ax.get_xticklabels(), color=_TXT_SEC)

    # Overlay valid data points — subtle dots with very slight white outline
    ax.scatter(
        df["fuel_flow_kg_s"],
        df["t_source_c"],
        s=12,
        color=_TXT_SEC,
        alpha=0.3,
        edgecolors="white",
        linewidths=0.3,
        zorder=5,
    )

    # Axis formatting — axis labels with thin white outline
    import matplotlib.patheffects as path_effects
    xlabel = ax.set_xlabel(r"Fuel flow, $\dot{m}_{\mathrm{CH_4}}$ (kg/s)", fontsize=FONTS["axis_label"], color=_TXT)
    xlabel.set_path_effects([
        path_effects.withStroke(linewidth=0.5, foreground="white"),
        path_effects.Normal(),
    ])
    ylabel = ax.set_ylabel(r"Source temperature, $T_{\mathrm{source}}$ ($^\circ$C)", fontsize=FONTS["axis_label"], color=_TXT)
    ylabel.set_path_effects([
        path_effects.withStroke(linewidth=0.5, foreground="white"),
        path_effects.Normal(),
    ])

    # Title — compact, descriptive, with thin white outline
    title = ax.set_title(
        "Brayton heat-pump architecture-space vs reversible methane benchmark",
        pad=10,
        fontsize=FONTS["title"],
        fontweight="bold",
        color=_TXT,
    )
    title.set_path_effects([
        path_effects.withStroke(linewidth=0.5, foreground="white"),
        path_effects.Normal(),
    ])

    # Grid and spines
    ax.grid(True, axis="both", alpha=0.25, linestyle="--", color=_GRID)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.6)
    ax.spines["bottom"].set_linewidth(0.6)

    # Axis limits — tight around data
    ax.set_xlim(
        fuel_flows.min() * 0.95,
        fuel_flows.max() * 1.02,
    )
    ax.set_ylim(
        source_temps.min() - 0.5,
        source_temps.max() + 0.5,
    )

    # Annotation — fraction range, top right, with thin white outline
    frac_min = df["layer4_total_fraction_of_layer2"].min()
    frac_max = df["layer4_total_fraction_of_layer2"].max()
    ann = ax.annotate(
        f"Valid points: {len(df)}\nFraction of ceiling: {frac_min:.3f}–{frac_max:.3f}",
        xy=(0.99, 0.98),
        xycoords="axes fraction",
        fontsize=FONTS["annotation"],
        color=_TXT_SEC,
        va="top",
        ha="right",
        bbox=dict(
            boxstyle="round,pad=0.3",
            facecolor=_BG,
            edgecolor=_GRID,
            alpha=0.9,
        ),
    )
    ann.set_path_effects([
        path_effects.withStroke(linewidth=0.5, foreground="white"),
        path_effects.Normal(),
    ])

    fig.tight_layout()
    return fig


if __name__ == "__main__":
    df = load_data()
    fig = plot_contour(df)

    # ── Save ───────────────────────────────────────────────────────────────
    fig.savefig(OUTPUT_PREFIX.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"Figure saved to {OUTPUT_DIR}")
