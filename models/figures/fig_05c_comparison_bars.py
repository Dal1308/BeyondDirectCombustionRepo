"""
models/figures/fig_05c_comparison_bars.py

Target: Fig. 5(c) — Worked-case comparison bars (Aspen provenance only).

Bar chart with a true discontinuous y-axis (brokenaxes). The lower subplot
shows the three bars (90% comparator, 100% ceiling, worked case); the upper
subplot shows the reversible benchmark as a dashed reference line.

Data provenance:
  - Worked case + fuel input: assets/aspen/export/current_base_case_key_outputs.csv
    (Aspen Layer 3 — firm condenser-duty boundary)
  - Reversible benchmark: data/independent/benchmark_surface.csv
    (Layer 2 entropy-balance theorem, interpolated to Aspen operating point)

Caption (draft):
    "Heat delivered for a fixed fuel input: the worked case (condenser duty)
     relative to the 90% practical comparator, the 100% direct-combustion
     ceiling, and the reversible benchmark. The worked case yields a
     conventional thermal efficiency of about 200% on the condenser-duty
     basis, exceeding both comparators while remaining far below the
     reversible thermodynamic limit."
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

# ── Output path ──────────────────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PREFIX = OUTPUT_DIR / "fig_05c_comparison_bars"


# ── Data loading ─────────────────────────────────────────────────────────────

def load_aspen_data():
    """Load worked-case data from Aspen exports and Layer 2 benchmark surface.

    Returns a dict with:
        fuel_input_w         — methane LHV input (W)
        worked_case_w        — condenser duty, headline boundary (W)
        comparator_90_w      — equal-duty fuel for 90% boiler (W)
        comparator_100_w     — equal-duty fuel for 100% boiler (W)
        reversible_benchmark_w — theoretical ceiling (W)
    """
    project_root = Path(__file__).resolve().parent.parent.parent

    # ── Aspen export ─────────────────────────────────────────────────────
    aspen_csv = project_root / "assets" / "aspen" / "export" / "current_base_case_key_outputs.csv"
    aspen = pd.read_csv(aspen_csv)
    fuel_input_w = float(aspen.loc[aspen["quantity"] == "fuel_input_lhv_w", "value"].values[0])
    worked_case_w = float(
        aspen.loc[aspen["quantity"] == "condenser_heat_duty_w", "value"].values[0]
    )

    # ── Derived comparators (fixed-fuel heat-delivered basis) ──────────
    comparator_90_w = fuel_input_w * 0.90
    comparator_100_w = fuel_input_w * 1.00

    # ── Reversible benchmark from Layer 2 (benchmark_surface.csv) ────────
    # Aspen operating point: T_C = 298 K, T_H = 333 K
    # Interpolate multiplier from the benchmark surface
    bm = pd.read_csv(project_root / "data" / "independent" / "benchmark_surface.csv")
    pivot = bm.pivot(index="t_hot_k", columns="t_cold_k", values="multiplier")
    from scipy.interpolate import griddata

    mult = griddata(
        np.column_stack([bm["t_cold_k"].values, bm["t_hot_k"].values]),
        bm["multiplier"].values,
        [[298.0, 333.0]],
        method="linear",
    )[0]

    reversible_benchmark_w = fuel_input_w * mult

    return {
        "fuel_input_w": fuel_input_w,
        "worked_case_w": worked_case_w,
        "comparator_90_w": comparator_90_w,
        "comparator_100_w": comparator_100_w,
        "reversible_benchmark_w": reversible_benchmark_w,
    }


# ── Figure generation ────────────────────────────────────────────────────────

def plot_comparison_bars(data):
    """Generate the comparison-bar figure with discontinuous y-axis."""
    from brokenaxes import brokenaxes

    fig = plt.figure(figsize=(6.0, 5.0))
    fig.patch.set_facecolor(_BG)

    fuel = data["fuel_input_w"]
    wc = data["worked_case_w"]
    c90 = data["comparator_90_w"]
    c100 = data["comparator_100_w"]
    rb = data["reversible_benchmark_w"]

    # Labels and colours — ordered low-to-high for visual flow
    comparisons = [
        {"label": "90% comparator", "value": c90, "color": _C["mid"]},
        {"label": "100% ceiling",   "value": c100, "color": _C["peak"]},
        {"label": "Worked case",    "value": wc,   "color": _C["hot"]},
    ]

    # ── Discontinuous y-axis ─────────────────────────────────────────────
    # Lower range: 0 → ~120 kW (covers all three bars with headroom)
    # Upper range: ~350 kW → ~450 kW (reversible benchmark at top)
    lower_max = max(c90, c100, wc) * 1.15
    upper_min = rb * 0.85
    upper_max = rb * 1.15

    bax = brokenaxes(
        ylims=((lower_max, upper_max), (0, lower_max)),
        hspace=0.06,
    )

    labels = [c["label"] for c in comparisons]
    values = [c["value"] for c in comparisons]
    colors = [c["color"] for c in comparisons]

    x_pos = np.arange(len(labels))
    bar_width = 0.55

    # brokenaxes: axs[0] = upper range, axs[1] = lower range
    bax.axs[0].set_ylim(upper_max, upper_min)   # upper: inverted for brokenaxes
    bax.axs[1].set_ylim(0, lower_max)            # lower: normal (bars here)

    # ── Draw bars in lower subplot ───────────────────────────────────────
    bars = bax.axs[1].bar(x_pos, values, width=bar_width,
                          color=colors, edgecolor="white", linewidth=0.8)

    # Value labels on bars
    for i, val in enumerate(values):
        eff_pct = val / fuel * 100
        bax.axs[1].text(x_pos[i], val + (lower_max * 0.02),
                        f"{val:,.0f} W\n({eff_pct:.0f}% of fuel)",
                        ha="center", va="bottom", fontsize=FONTS["annotation"], color=_TXT, fontweight="bold")

    # ── Reversible benchmark in upper subplot (black, near top) ─────────
    bax.axs[0].axhline(y=rb, color=_TXT,
                       linestyle="--", linewidth=1.5, alpha=0.7)
    bax.axs[0].text(0.02, rb + (upper_max - upper_min) * 0.15,
                    f"Reversible benchmark: {rb:,.0f} W",
                    ha="left", va="bottom", fontsize=FONTS["annotation"], color=_TXT, fontweight="bold")

    # ── X-axis ticks and labels ──────────────────────────────────────────
    for ax in bax.axs:
        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, fontsize=FONTS["tick"], color=_TXT)

    # ── Y-axis label (figure-level, centred across both subplots) ────────
    fig.supylabel("Heat delivered for fixed fuel input (W)",
                  fontsize=FONTS["axis_label"], color=_TXT, x=0.01)

    # ── Title ────────────────────────────────────────────────────────────
    worked_case_eff = wc / fuel * 100
    fig.suptitle(
        f"Worked case delivers {worked_case_eff:.0f}% of fuel input "
        f"(condenser duty), far below the reversible benchmark",
        fontsize=FONTS["title"], fontweight="bold", color=_TXT, y=0.97,
    )

    # ── Grid lines ───────────────────────────────────────────────────────
    bax.axs[0].grid(True, axis="y", alpha=0.3, linestyle="--", color=_GRID)
    bax.axs[1].grid(True, axis="y", alpha=0.3, linestyle="--", color=_GRID)

    # ── Tick formatting ──────────────────────────────────────────────────
    bax.axs[1].tick_params(axis="y", which="both", labelsize=8.5)
    bax.axs[0].tick_params(axis="y", which="both", labelsize=8.5)

    # ── Clean spines ─────────────────────────────────────────────────────
    for ax in bax.axs:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_linewidth(0.8)
        ax.spines["bottom"].set_linewidth(0.8)

    plt.subplots_adjust(left=0.12, right=0.95, top=0.92, bottom=0.15)

    # ── Center break glyph in the gap between subplots ───────────────────
    lower_ymax = bax.axs[1].get_position().ymax
    upper_y0   = bax.axs[0].get_position().y0
    gap_center = (lower_ymax + upper_y0) / 2 + 0.005
    all_y = [y for line in bax.diag_handles for y in line.get_ydata()]
    current_center = sum(all_y) / len(all_y)
    shift = gap_center - current_center
    for line in bax.diag_handles:
        line.set_ydata(line.get_ydata() + shift)

    return fig


if __name__ == "__main__":
    data = load_aspen_data()
    fig = plot_comparison_bars(data)

    # ── Save ───────────────────────────────────────────────────────────────
    fig.savefig(OUTPUT_PREFIX.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)

    print(f"Figure saved to {OUTPUT_DIR}")

    # ── Data summary ───────────────────────────────────────────────────────
    fuel = data["fuel_input_w"]
    wc = data["worked_case_w"]
    rb = data["reversible_benchmark_w"]
    print(f"\nData summary (fixed-fuel basis):")
    print(f"  Fuel input (Aspen LHV):     {fuel:10,.0f} W")
    print(f"  90% comparator:             {data['comparator_90_w']:10,.0f} W ({data['comparator_90_w']/fuel*100:.0f}% of fuel)")
    print(f"  100% ceiling:               {data['comparator_100_w']:10,.0f} W ({data['comparator_100_w']/fuel*100:.0f}% of fuel)")
    print(f"  Worked case (condenser):    {wc:10,.0f} W ({wc/fuel*100:.1f}% of fuel)")
    print(f"  Reversible benchmark:       {rb:10,.0f} W ({rb/fuel:.1f}× fuel)")
