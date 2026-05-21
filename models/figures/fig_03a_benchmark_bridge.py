"""
models/figures/fig_03a_benchmark_bridge.py

Target: Fig. 3 — Distance-to-limit comparison (horizontal normalized lollipop scale).

Shows Q_H,max / |ΔH°| for 5 fuels, normalized to the reversible methane ceiling
at 1.0. Two reference markers indicate the practical comparators:
    - Direct combustion ceiling at y = 0.163 (~1.0/6.15 of methane ceiling)
    - 90% practical boiler comparator at y = 0.146 (~0.9/6.15 of methane ceiling)
An Aspen worked-case marker shows the process-specific result on the same scale.

Data provenance:
    Fuel multipliers: computed via models.independent.core.heating_multiplier()
        from the entropy-balance theorem (SI Note 1 / Layer 2).
    Aspen point: assets/aspen/export/current_base_case_key_outputs.csv
        (fuel_input_lhv_w, condenser_heat_duty_w → ratio = delivered/fuel)

Caption (draft):
    "Distance-to-limit comparison at T_C = 10°C, T_H = 60°C. The reversible
     benchmark ceilings for five fuels are shown normalized to the methane
     ceiling (set to 1.0). All fuels sit far above the practical comparators:
     the 90% boiler comparator and 100% direct-combustion ceiling. The Aspen
     worked case delivers ~2× fuel input, placing it between the practical
     comparators and the reversible ceilings."

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

OUTPUT_PREFIX = OUTPUT_DIR / "fig_03a_benchmark_bridge"


# ── Reference levels (fixed per AGENTS.md comparator framework) ──────────────
DIRECT_COMBUSTION_CEILING = 1.0
PRACTICAL_BOILER_COMPARATOR = 0.9


# ── Data loading ─────────────────────────────────────────────────────────────

def load_data():
    """Load benchmark multipliers for 5 fuels at T_C = 10°C, T_H = 60°C.

    Returns a DataFrame with columns:
        fuel, t_cold_k, t_hot_k, multiplier, aspen_ratio
    Uses heating_multiplier() from core.py — no manual sign handling.
    Aspen ratio computed from current_base_case_key_outputs.csv:
        condenser_heat_duty_w / fuel_input_lhv_w
    """
    import pandas as pd

    # Anchor temperatures (domestic hot-water condition)
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
            "aspen_ratio": float("nan"),  # placeholder — computed below
        })

    df = pd.DataFrame(rows)

    # ── Load Aspen worked-case ratio ───────────────────────────────────────
    aspen_path = Path(__file__).resolve().parent.parent.parent / \
                 "assets/aspen/export/current_base_case_key_outputs.csv"
    if aspen_path.exists():
        aspen_df = pd.read_csv(aspen_path)
        fuel_input = float(
            aspen_df.loc[
                aspen_df["quantity"] == "fuel_input_lhv_w", "value"
            ].values[0]
        )
        condenser_duty = float(
            aspen_df.loc[
                aspen_df["quantity"] == "condenser_heat_duty_w", "value"
            ].values[0]
        )
        if fuel_input > 0:
            aspen_ratio = condenser_duty / fuel_input
            df.loc[:, "aspen_ratio"] = aspen_ratio

    return df


# ── Figure generation ────────────────────────────────────────────────────────

def plot_bridge(df):
    """Generate the distance-to-limit comparison (horizontal lollipop scale).

    Shows fuel-specific reversible ceilings on the left and practical comparators
    (90% boiler, direct combustion, Aspen worked case) on the same absolute scale.
    The visual gap between ceilings (~6.1–6.9) and practical systems (<2.0)
    illustrates how far real heating approaches sit below the reversible limit.
    """
    fig, ax = plt.subplots(figsize=(8.0, 5.5))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)

    # ── Fuel ceilings (horizontal lollipops) ───────────────────────────────────
    fuel_order = ["methane", "hydrogen", "syngas", "carbon", "ammonia"]
    df = df.copy().set_index("fuel").loc[fuel_order].reset_index()
    df.rename(columns={"fuel": "fuel_key"}, inplace=True)

    y_pos = np.arange(len(df))

    fuel_labels = {
        "methane": "CH₄", "hydrogen": "H₂", "ammonia": "NH₃",
        "syngas": "Syngas", "carbon": "C(s)",
    }
    fuel_colours = {
        "methane": _C["mid"],       # electric blue — representative hydrocarbon
        "hydrogen": _C["cold"],     # deep violet — clean fuel
        "ammonia": _C["hot"],       # green/magenta — nitrogen-containing
        "syngas": _C["peak"],       # amber — coal-derived baseline
        "carbon": _C["loss"],       # vermilion — solid carbon
    }

    for i, (_, row) in enumerate(df.iterrows()):
        val = row["multiplier"]
        ax.plot(
            [0, val], [y_pos[i], y_pos[i]],
            color=fuel_colours[row["fuel_key"]],
            linewidth=1.8, alpha=0.5, zorder=2,
        )
        ax.scatter(
            val, y_pos[i],
            s=120, c=fuel_colours[row["fuel_key"]],
            edgecolor="white", linewidth=1.2, zorder=3,
        )

    # ── Practical comparator reference markers ─────────────────────────────────
    # Fixed reference lines at absolute values (same scale as fuel ceilings)
    ax.axvline(
        PRACTICAL_BOILER_COMPARATOR, color=_C["baseline_ref"], linestyle="-.",
        linewidth=1.2, alpha=0.6, zorder=1,
        label=f"90% boiler comparator ({PRACTICAL_BOILER_COMPARATOR})",
    )
    ax.axvline(
        DIRECT_COMBUSTION_CEILING, color=_C["baseline_ref"], linestyle="--",
        linewidth=1.4, alpha=0.7, zorder=1,
        label=f"Direct combustion ({DIRECT_COMBUSTION_CEILING})",
    )

    # ── Aspen worked-case marker (placed below all fuel rows) ───────────────
    aspen_ratio = df["aspen_ratio"].values[0]
    aspen_y = -1  # one row below methane (y=0)
    if not np.isnan(aspen_ratio):
        ax.scatter(
            aspen_ratio, aspen_y,
            s=200, c=_C["peak"], marker="D", zorder=4,
            edgecolor="white", linewidth=1.5,
            label=f"Aspen worked case ({aspen_ratio:.1f}× fuel)",
        )
        ax.plot(
            [0, aspen_ratio], [aspen_y, aspen_y],
            color=_C["peak"], linewidth=1.5, linestyle=(0, (3, 2)),
            alpha=0.6, zorder=2,
        )

    # ── Axis configuration ─────────────────────────────────────────────────────
    ax.set_yticks(y_pos)
    ax.set_yticklabels(
        [fuel_labels[k] for k in df["fuel_key"]],
        fontsize=FONTS["tick"], color=_TXT, fontweight="bold",
    )

    ax.set_xlabel(
        r"$Q_{\mathrm{H}}^{\max} / |\Delta H^\circ|$ (dimensionless)",
        fontsize=FONTS["axis_label"], color=_TXT,
    )

    fig.suptitle(
        "Distance-to-limit comparison — 10°C source, 60°C sink",
        fontsize=FONTS["title"], fontweight="bold", color=_TXT, y=0.98,
    )

    # Grid, legend, spines
    ax.grid(True, axis="x", alpha=0.3, linestyle="--", color=_GRID)
    fig.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 0.91),
        ncol=3,
        fontsize=FONTS["annotation"],
        frameon=False,
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.6)
    ax.spines["bottom"].set_linewidth(0.6)

    # Value labels on fuel dots
    for i, (_, row) in enumerate(df.iterrows()):
        ax.text(
            row["multiplier"] + 0.15, y_pos[i], f"{row['multiplier']:.2f}",
            ha="left", va="center", fontsize=FONTS["annotation"], color=_TXT,
        )

    # X-axis — start at 0, headroom above highest value
    x_max = max(df["multiplier"].max(), aspen_ratio if not np.isnan(aspen_ratio) else 0) * 1.35
    ax.set_xlim(0, x_max)

    # Y-axis — add padding for Aspen row below and methane above
    ax.set_ylim(-1.5, len(df) - 0.5)

    fig.subplots_adjust(left=0.13, right=0.97, top=0.80, bottom=0.14)
    return fig


if __name__ == "__main__":
    df = load_data()
    fig = plot_bridge(df)

    # ── Save ───────────────────────────────────────────────────────────────
    fig.savefig(OUTPUT_PREFIX.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"Figure saved to {OUTPUT_DIR}")

    # ── Data summary ───────────────────────────────────────────────────────
    methane_mult = df.loc[df["fuel"] == "methane", "multiplier"].values[0]
    print(f"\nData summary (normalized to methane ceiling = {methane_mult:.4f}):")
    for _, row in df.iterrows():
        norm = row["multiplier"] / methane_mult
        aspen_str = f" | aspen_ratio = {row['aspen_ratio']:.4f}" if not np.isnan(row["aspen_ratio"]) else ""
        print(f"  {row['fuel']:10s} | multiplier = {row['multiplier']:.4f} | normalized = {norm:.4f}{aspen_str}")
