"""
models/figures/fig_04b_operational_envelope.py

Target: Fig. 4(b) — Operational envelope scatter plot (Layer 4 SI).

Shows the valid thermodynamic operational envelope amid invalid parameter space
from the Layer 4 R134a architecture-space stress test (2,500 cases).

Data provenance:
    models/thermodynamic/brayton_heat_pump_architecture_space/output/
    stress_test_results.csv — R134a first-principles physics, 2,500-case sweep.

Caption (draft):
    "Operational envelope showing the valid-parameter wedge amid the invalid
     region in the Layer 4 R134a architecture-space stress test (2,500 cases).
     Only 383 cases (~15%) fall within the physically plausible envelope where
     R134a thermodynamics remain well-behaved. The valid region is bounded by
     fuel-flow limits (below ~3 g/s) and source-temperature limits (below
     ~33°C), consistent with the requirements for effective heat-pump coupling
     in a Brayton cycle configuration."
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
from models.figures.config import current_palette as _C
from models.figures.style import apply
apply()
from models.figures.config.font_config import FONTS

_BG = _C["background"]
_GRID = _C["grid"]
_TXT = _C["text_primary"]
_PEAK = "#8b0000"  # dark red — matches fig_02b benchmark ceiling

# ── Output path ──────────────────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PREFIX = OUTPUT_DIR / "fig_04b_operational_envelope"


def load_data():
    """Load stress test results from Layer 4 consolidated data/ directory.

    Returns a DataFrame with columns including:
        fuel_flow, t_source, status, t_sink, cop
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    data_path = project_root / "data" / "brayton_heat_pump_architecture_space" / "stress_test_results.csv"
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} stress test points from {data_path.name}: "
          f"{df['status'].value_counts().to_dict()}")
    return df


def plot_envelope(df):
    """Generate operational envelope scatter plot."""
    fig, ax = plt.subplots(figsize=(8.5, 8.5))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)

    # Separate valid and invalid points
    valid = df[df["status"] == "valid"]
    invalid = df[df["status"] != "valid"]

    # Valid regime: peak/amber as the "hero" data
    ax.scatter(
        valid["t_source"], valid["fuel_flow"],
        color=_PEAK, alpha=0.9, s=28,
        edgecolor="white", linewidth=0.3, zorder=2,
    )

    # Log scale on y-axis — simplify ticks
    ax.set_yscale("log")
    ax.tick_params(which="minor", left=False)
    ax.tick_params(which="major", left=True)

    # Tighten axis limits to reduce empty space
    ax.set_xlim(-25.0, 40.0)
    ax.set_ylim(5e-7, 2e-2)

    # Axis formatting
    ax.set_xlabel(
        r"Source temp. ($T_{\mathrm{source}}$, $^\circ$C)",
        fontsize=FONTS["axis_label"], color=_TXT,
    )
    ax.set_ylabel(r"Fuel flow (kg/s) [Log]", fontsize=FONTS["axis_label"], color=_TXT)
    fig.suptitle(
        "Thermodynamic operational envelope — "
        "Layer 4 R134a architecture sweep",
        fontsize=FONTS["title"], fontweight="bold", color=_TXT, y=0.98,
    )
    ax.grid(True, which="major", axis="x", alpha=0.25, linestyle="--", color=_GRID)
    ax.grid(True, which="both", axis="y", alpha=0.2, linestyle=":", color=_GRID)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=_PEAK, alpha=0.9, edgecolor="white", linewidth=0.3,
              label=f"Valid ({len(valid)} cases)"),
    ]
    fig.legend(handles=legend_elements, loc="upper center",
              bbox_to_anchor=(0.5, 0.91),
              ncol=1, fontsize=FONTS["annotation"],
              frameon=False)

    fig.subplots_adjust(left=0.12, right=0.97, top=0.80, bottom=0.13)
    return fig


if __name__ == "__main__":
    df = load_data()
    fig = plot_envelope(df)

    # ── Save ───────────────────────────────────────────────────────────────
    fig.savefig(OUTPUT_PREFIX.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"Figure saved to {OUTPUT_DIR}")

    # ── Data summary ───────────────────────────────────────────────────────
    valid = df[df["status"] == "valid"]
    invalid = df[df["status"] != "valid"]
    pct_valid = len(valid) / len(df) * 100
    print(f"\nData summary:")
    print(f"  Total cases:    {len(df):5d}")
    print(f"  Valid cases:    {len(valid):5d} ({pct_valid:.1f}%)")
    print(f"  Invalid cases:  {len(invalid):5d} (not plotted — outside R134a envelope)")
    print(f"  Valid range:")
    print(f"    t_source:    {valid['t_source'].min():.1f} – {valid['t_source'].max():.1f} °C")
    print(f"    fuel_flow:   {valid['fuel_flow'].min():.0e} – {valid['fuel_flow'].max():.0e} kg/s")
