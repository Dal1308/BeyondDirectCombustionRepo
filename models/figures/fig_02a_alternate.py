"""
models/figures/fig_02a_alternate.py

Target: Fig. 2(a) alternate — Dot chart version of the benchmark chart.

Shows Q_H,max / |ΔH°| for 5 fuels at T_C = 10°C, T_H = 60°C
(domestic hot-water condition) as dot arrays with partial fills.
Designed for Inkscape editing — generous left margin for molecular
illustrations and annotations.

Data provenance:
    Computed via models.independent.core.heating_multiplier() from the
    entropy-balance theorem (SI Note 1 / Layer 2).
    No cycle physics, no gas-savings, no Brayton+HP assumptions.

"""

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".mplconfig"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge
import numpy as np

# ── Central palette + style system ───────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from models.figures.config import current_palette as _C
from models.figures.style import apply
apply()
from models.figures.config.font_config import FONTS

_BG = _C["background"]
_GRID = _C["grid"]
_TXT = _C["text_primary"]

# ── Independent model import ─────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "independent"))
from models.independent.core import get_fuel, heating_multiplier


# ── Output path ──────────────────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PREFIX = OUTPUT_DIR / "fig_02a_alternate"


# ── Data loading ─────────────────────────────────────────────────────────────

def load_data():
    """Load benchmark multipliers for 5 fuels at T_C = 10°C, T_H = 60°C.

    Returns a DataFrame with columns:
        fuel, t_cold_k, t_hot_k, multiplier
    """
    T_COLD_K = 283.15   # 10°C
    T_HOT_K = 333.15    # 60°C

    fuels = ["methane", "hydrogen", "ammonia", "syngas", "carbon"]

    rows = []
    for fuel_key in fuels:
        fuel = get_fuel(fuel_key)
        mult = heating_multiplier(fuel, T_COLD_K, T_HOT_K)
        rows.append({
            "fuel": fuel_key,
            "t_cold_k": T_COLD_K,
            "t_hot_k": T_HOT_K,
            "multiplier": mult,
        })

    return __import__("pandas").DataFrame(rows)


# ── Figure generation ────────────────────────────────────────────────────────

def _draw_dot(ax, x, y, radius, colour):
    """Draw a single filled circle (dot)."""
    ax.add_patch(plt.Circle((x, y), radius, facecolor=colour,
                            edgecolor="white", linewidth=0.5, zorder=5))


def _draw_partial_dot(ax, x, y, radius, fraction, colour):
    """Draw a circle partially filled to the given fraction (0–1).

    The dot is drawn as a full background-coloured circle with a Wedge
    overlay for the filled portion — matching the reference style where
    the unfilled remainder appears as an outline.
    """
    # Background (unfilled) ring
    ax.add_patch(plt.Circle((x, y), radius, facecolor=_BG,
                            edgecolor=colour, linewidth=1.5, zorder=5))
    # Filled wedge — start from the right (0°) and sweep anticlockwise
    angle = fraction * 360.0
    if angle > 0.1:
        ax.add_patch(Wedge((x, y), radius, 0, angle,
                           facecolor=colour, zorder=6))


def plot_bars(df):
    """Generate dot chart with direct-combustion reference."""
    fig, ax = plt.subplots(figsize=(7.5, 5.0))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)

    # Colour mapping — semantic roles from palette
    fuel_colours = {
        "methane": _C["mid"],       # electric blue — representative hydrocarbon
        "hydrogen": _C["cold"],     # deep violet — clean fuel
        "ammonia": _C["hot"],       # magenta — nitrogen-containing
        "syngas": _C["peak"],       # amber — coal-derived baseline
        "carbon": _C["loss"],       # vermilion — solid carbon
    }

    # Dot layout
    dot_radius = 0.18
    dot_spacing = 1.0
    y_pos = np.arange(len(df))

    # Set axes limits first so aspect ratio applies to circles
    x_max = df["multiplier"].max() + 1.5
    ax.set_xlim(0, x_max)
    ax.set_ylim(-0.8, len(df) - 0.2)
    ax.set_aspect("equal", adjustable="box")

    # Draw dots for each fuel row
    for i, (_, row) in enumerate(df.iterrows()):
        value = row["multiplier"]
        colour = fuel_colours[row["fuel"]]
        n_full = int(value)
        fraction = value - n_full

        # Full dots — start at x=1.0 so first dot is not clipped by spine
        for j in range(n_full):
            _draw_dot(ax, 1.0 + j * dot_spacing, y_pos[i],
                      dot_radius, colour)

        # Partial dot (only if fractional part is significant)
        if fraction > 0.01:
            _draw_partial_dot(ax, 1.0 + n_full * dot_spacing,
                              y_pos[i], dot_radius, fraction, colour)

    # Direct-combustion reference line at x = 1.0
    ax.axvline(
        1.0, color=_C["baseline_ref"], linestyle="--", linewidth=1.2,
        alpha=0.6, zorder=3,
    )
    # Position "Direct combustion" above the dashed line at x=1
    x_frac = 1.0 / ax.get_xlim()[1]  # data x=1 as axes-fraction of xlim
    ax.text(
        x_frac, 1.02, "Direct combustion",
        ha="center", va="bottom",
        fontsize=FONTS["annotation"], color=_C["baseline_ref"],
        fontweight="bold",
        transform=ax.transAxes,
    )
    fig.suptitle(
        "Reversible heating ceiling — 10°C source, 60°C sink",
        fontsize=FONTS["title"], fontweight="bold", color=_TXT, y=0.96,
    )

    # Fuel labels on y-axis
    fuel_labels = {
        "methane": "CH₄",
        "hydrogen": "H₂",
        "ammonia": "NH₃",
        "syngas": "Syngas",
        "carbon": "C(s)",
    }
    ax.set_yticks(y_pos)
    ax.set_yticklabels([fuel_labels[f] for f in df["fuel"]],
                       fontsize=FONTS["tick"], color=_TXT, fontweight="bold")
    # Flip so methane (highest value) is on top
    ax.invert_yaxis()

    # X-axis label — dimensionless multiplier
    ax.set_xlabel(r"$Q_{\mathrm{H}}^{\max} / |\Delta H^\circ|$ (dimensionless)",
                  fontsize=FONTS["axis_label"], color=_TXT)

    # Grid and spines
    ax.grid(True, axis="x", alpha=0.3, linestyle="--", color=_GRID)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.6)
    ax.spines["bottom"].set_linewidth(0.6)

    # Value labels (to the right of each row's last dot)
    for i, (_, row) in enumerate(df.iterrows()):
        value = row["multiplier"]
        n_full = int(value)
        fraction = value - n_full
        if fraction > 0.01:
            last_x = 1.0 + n_full * dot_spacing
        else:
            last_x = 1.0 + (n_full - 1) * dot_spacing
        ax.text(
            last_x + dot_radius + 0.2, y_pos[i],
            f"{value:.2f}",
            ha="left", va="center",
            fontsize=FONTS["annotation"],
            color=fuel_colours[row["fuel"]], fontweight="bold",
        )

    # X-axis — start at 0
    x_max = df["multiplier"].max() + 1.5
    ax.set_xlim(0, x_max)

    # Tight layout with generous left margin for Inkscape additions
    fig.subplots_adjust(left=0.28, right=0.95, top=0.86, bottom=0.14)
    return fig


if __name__ == "__main__":
    df = load_data()
    fig = plot_bars(df)

    # ── Save ───────────────────────────────────────────────────────────────
    fig.savefig(OUTPUT_PREFIX.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"Figure saved to {OUTPUT_DIR}")

    # ── Data summary ───────────────────────────────────────────────────────
    print("\nData summary:")
    for _, row in df.iterrows():
        print(f"  {row['fuel']:10s} | multiplier = {row['multiplier']:.4f}")
