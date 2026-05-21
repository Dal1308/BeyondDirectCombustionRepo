"""
models/figures/fig_02a_benchmark_bar_chart.py

Target: Fig. 2(a) — Benchmark bar chart comparing reversible Q_H,max across fuels.

Shows Q_H,max / |ΔH°| for 4 fuels at T_C = 10°C, T_H = 60°C
(domestic hot-water condition). A dashed reference line marks direct combustion
at y = 1.0.

Data provenance:
    Computed via models.independent.core.heating_multiplier() from the
    entropy-balance theorem (SI Note 1 / Layer 2).
    No cycle physics, no gas-savings, no Brayton+HP assumptions.

Caption (draft):
    "Reversible heating ceiling at T_C = 10°C, T_H = 60°C. The dimensionless
     multiplier Q_H,max / |ΔH°| ranges from ~6.1 (syngas) to ~6.9 (ammonia),
     with carbon at 6.25, all well above the direct-combustion ceiling at 1.0."
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".mplconfig"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
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

OUTPUT_PREFIX = OUTPUT_DIR / "fig_02a_benchmark_bar_chart"


# ── Data loading ─────────────────────────────────────────────────────────────

def load_data():
    """Load benchmark multipliers for 4 fuels at T_C = 10°C, T_H = 60°C.

    Returns a DataFrame with columns:
        fuel, t_cold_k, t_hot_k, multiplier
    Uses heating_multiplier() from core.py — no manual sign handling.
    """
    # Planned anchor temperatures (domestic hot-water condition)
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

def plot_bars(df):
    """Generate the benchmark bar chart with direct-combustion reference."""
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
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

    x_pos = np.arange(len(df))
    bar_width = 0.55

    bars = ax.bar(
        x_pos, df["multiplier"], width=bar_width,
        color=[fuel_colours[f] for f in df["fuel"]],
        edgecolor="white", linewidth=0.8,
    )

    # Direct-combustion reference line at y = 1.0 (with legend handle)
    ax.axhline(
        1.0, color=_C["baseline_ref"], linestyle="--", linewidth=1.2,
        alpha=0.6, zorder=3, label="Direct combustion",
    )
    fig.suptitle(
        "Reversible heating ceiling — 10°C source, 60°C sink",
        fontsize=FONTS["title"], fontweight="bold", color=_TXT, y=0.98,
    )
    fig.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 0.91),
        ncol=1,
        fontsize=FONTS["annotation"],
        frameon=False,
    )

    # Fuel labels on x-axis
    fuel_labels = {
        "methane": "CH₄",
        "hydrogen": "H₂",
        "ammonia": "NH₃",
        "syngas": "Syngas",
        "carbon": "C(s)",
    }
    ax.set_xticks(x_pos)
    ax.set_xticklabels([fuel_labels[f] for f in df["fuel"]],
                        fontsize=FONTS["tick"], color=_TXT, fontweight="bold")

    # Y-axis label — dimensionless multiplier
    ax.set_ylabel(r"$Q_{\mathrm{H}}^{\max} / |\Delta H^\circ|$ (dimensionless)",
                  fontsize=FONTS["axis_label"], color=_TXT)

    # Grid and spines
    ax.grid(True, axis="y", alpha=0.3, linestyle="--", color=_GRID)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.6)
    ax.spines["bottom"].set_linewidth(0.6)

    # Value labels on bars
    for i, (_, row) in enumerate(df.iterrows()):
        ax.text(
            x_pos[i], row["multiplier"] + 0.15, f"{row['multiplier']:.2f}",
            ha="center", va="bottom", fontsize=FONTS["annotation"], color=_TXT, fontweight="bold",
        )

    # Y-axis — start at 0, 20% headroom above highest bar
    y_max = df["multiplier"].max() * 1.20
    ax.set_ylim(0, y_max)

    fig.subplots_adjust(left=0.14, right=0.97, top=0.80, bottom=0.16)
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
