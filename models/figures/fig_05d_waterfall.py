"""
models/figures/fig_05d_waterfall.py

Target: Fig. 5(d) — Waterfall breakdown of delivered heat (Aspen provenance only).

Energy-flow waterfall showing how delivered heat builds up from:
  1. Environmental heat uptake (evaporator)
  2. Work converted to heat (heat-pump lift)
Plus fuel input as context and reversible benchmark as ceiling.

Data provenance:
  - All energy flows: assets/aspen/export/current_base_case_key_outputs.csv
    (Aspen Layer 3 — firm condenser-duty boundary)
  - Reversible benchmark: data/independent/benchmark_surface.csv
    (Layer 2 entropy-balance theorem, interpolated to Aspen operating point)

Caption (draft):
    "Waterfall breakdown of delivered heat into environmental heat uptake
     and work-converted-to-heat contributions. The condenser duty of
     88.7 kW is assembled from 46.2 kW of environmental heat drawn through
     the evaporator and 42.5 kW of fuel-derived work upgraded by the
     heat-pump cycle. The reversible benchmark (dashed line) shows the
     thermodynamic ceiling at ~389 kW."
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
from brokenaxes import brokenaxes

# ── Central palette + style system ───────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from models.figures.config import current_palette as _C
from models.figures.style import apply
apply()
from models.figures.config.font_config import FONTS

_BG = _C["background"]
_GRID = _C["grid"]
_TXT = _C["text_primary"]
_ENV_HEAT = _C["hot"]

# ── Output path ──────────────────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PREFIX = OUTPUT_DIR / "fig_05d_waterfall"


# ── Data loading ─────────────────────────────────────────────────────────────

def load_aspen_data():
    """Load worked-case data from Aspen exports and Layer 2 benchmark surface.

    Returns a dict with:
        fuel_input_w               — methane LHV input (W)
        condenser_duty_w           — headline delivered heat (W)
        evaporator_uptake_w        — environmental heat drawn in (W)
        work_converted_w           — heat-pump lift (condenser − evaporator)
        reversible_benchmark_w     — theoretical ceiling (W)
    """
    project_root = Path(__file__).resolve().parent.parent.parent

    # ── Aspen export ─────────────────────────────────────────────────────
    aspen_csv = project_root / "assets" / "aspen" / "export" / "current_base_case_key_outputs.csv"
    aspen = pd.read_csv(aspen_csv)
    fuel_input_w = float(aspen.loc[aspen["quantity"] == "fuel_input_lhv_w", "value"].values[0])
    condenser_duty_w = float(
        aspen.loc[aspen["quantity"] == "condenser_heat_duty_w", "value"].values[0]
    )
    evaporator_uptake_w = float(
        aspen.loc[aspen["quantity"] == "evaporator_source_heat_uptake_w", "value"].values[0]
    )

    # ── Derived: work converted to heat (heat-pump lift) ─────────────────
    work_converted_w = condenser_duty_w - evaporator_uptake_w

    # ── Reversible benchmark from Layer 2 (benchmark_surface.csv) ────────
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
        "condenser_duty_w": condenser_duty_w,
        "evaporator_uptake_w": evaporator_uptake_w,
        "work_converted_w": work_converted_w,
        "reversible_benchmark_w": reversible_benchmark_w,
    }


# ── Figure generation ────────────────────────────────────────────────────────

def plot_waterfall(data):
    """Generate the energy-flow waterfall chart with broken y-axis."""
    fig = plt.figure(figsize=(8.5, 6.5))
    fig.patch.set_facecolor(_BG)

    fuel = data["fuel_input_w"]
    condenser = data["condenser_duty_w"]
    env_heat = data["evaporator_uptake_w"]
    work_conv = data["work_converted_w"]
    rb = data["reversible_benchmark_w"]

    # ── Broken y-axis ────────────────────────────────────────────────────
    # Lower range: 0 → ~120 kW (covers all bars with headroom)
    # Upper range: ~340 kW → ~420 kW (reversible benchmark)
    lower_max = condenser * 1.25
    upper_min = rb * 0.85
    upper_max = rb * 1.10

    bax = brokenaxes(
        ylims=((lower_max, upper_max), (0, lower_max)),
        hspace=0.04,
    )
    bax.axs[0].set_facecolor(_BG)
    bax.axs[1].set_facecolor(_BG)
    # Explicitly set y-limits after brokenaxes construction
    bax.axs[0].set_ylim(upper_max, upper_min)
    bax.axs[1].set_ylim(0, lower_max)

    # ── Waterfall bars in lower subplot ──────────────────────────────────
    labels = [
        "Fuel input\n(LHV)",
        "Environmental\nheat uptake",
        "Work →\nheat (HP lift)",
        "Total delivered\nheat",
    ]

    x_pos = np.arange(len(labels))
    bar_width = 0.55

    # Bar heights and bottoms
    bars_data = [
        {"height": fuel,   "bottom": 0, "color": _GRID},
        {"height": env_heat, "bottom": 0, "color": _ENV_HEAT},
        {"height": work_conv, "bottom": env_heat, "color": _C["mid"]},
        {"height": condenser, "bottom": 0, "color": _C["peak"]},
    ]

    # Draw bars in lower subplot (axs[1])
    for i, bar in enumerate(bars_data):
        bax.axs[1].bar(x_pos[i], bar["height"], width=bar_width, bottom=bar["bottom"],
                       color=bar["color"], edgecolor="white", linewidth=0.8, zorder=2)

        # Value label
        top = bar["bottom"] + bar["height"]
        bax.axs[1].text(x_pos[i], top + lower_max * 0.015,
                        f"{bar['height']:,.0f} W",
                        ha="center", va="bottom", fontsize=FONTS["annotation"], color=_TXT, fontweight="bold")

    # ── Dashed connector lines (waterfall effect) in lower subplot ───────
    bax.axs[1].plot([x_pos[1] + bar_width / 2, x_pos[2] - bar_width / 2],
                    [env_heat, env_heat],
                    color=_TXT, linestyle=":", linewidth=0.8, alpha=0.5, zorder=1)

    # ── Reversible benchmark in upper subplot ────────────────────────────
    bax.axs[0].set_ylim(upper_max, upper_min)   # upper: inverted for brokenaxes
    bax.axs[0].axhline(y=rb, color=_TXT, linestyle="--", linewidth=1.5, alpha=0.6)
    bax.axs[0].text(0.02, rb,
                    f"Reversible benchmark: {rb:,.0f} W",
                    ha="left", va="bottom", fontsize=FONTS["annotation"], color=_TXT, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor=_BG, edgecolor=_GRID, alpha=0.9))

    # ── X-axis ticks and labels (both subplots) ──────────────────────────
    for ax in bax.axs:
        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, fontsize=FONTS["tick"], color=_TXT)

    # ── Y-axis label (lower subplot only) ────────────────────────────────
    bax.axs[1].set_ylabel("Power (W)", fontsize=FONTS["axis_label"], color=_TXT)

    # ── Title ────────────────────────────────────────────────────────────
    env_pct = env_heat / condenser * 100
    work_pct = work_conv / condenser * 100
    fig.suptitle(
        f"Energy build-up to delivered heat: {env_pct:.0f}% environmental + "
        f"{work_pct:.0f}% work-converted",
        fontsize=FONTS["title"], fontweight="bold", color=_TXT, y=0.98,
    )

    # ── Grid lines (both subplots) ───────────────────────────────────────
    bax.axs[0].grid(True, axis="y", alpha=0.3, linestyle="--", color=_GRID)
    bax.axs[1].grid(True, axis="y", alpha=0.3, linestyle="--", color=_GRID)

    # ── Tick formatting ──────────────────────────────────────────────────
    bax.axs[0].tick_params(axis="y", which="both", labelsize=FONTS["tick"])
    bax.axs[1].tick_params(axis="y", which="both", labelsize=FONTS["tick"])

    # ── Clean spines (both subplots) ─────────────────────────────────────
    for ax in bax.axs:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_linewidth(0.8)
        ax.spines["bottom"].set_linewidth(0.8)

    plt.subplots_adjust(left=0.12, right=0.95, top=0.84, bottom=0.15)

    # ── Center break glyph in the gap between subplots ───────────────────
    lower_ymax = bax.axs[1].get_position().ymax
    upper_y0   = bax.axs[0].get_position().y0
    gap_center = (lower_ymax + upper_y0) / 2 + 0.005
    all_y = [y for line in bax.diag_handles for y in line.get_ydata()]
    current_center = sum(all_y) / len(all_y)
    shift = gap_center - current_center
    for line in bax.diag_handles:
        line.set_ydata(line.get_ydata() + shift)

    # ── Legend ───────────────────────────────────────────────────────────
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=_GRID, edgecolor="white", linewidth=0.8,
              label="Fuel input (context)"),
        Patch(facecolor=_ENV_HEAT, edgecolor="white", linewidth=0.8,
              label="Environmental heat uptake"),
        Patch(facecolor=_C["mid"], edgecolor="white", linewidth=0.8,
              label="Work → heat (HP lift)"),
        Patch(facecolor=_C["peak"], edgecolor="white", linewidth=0.8,
              label="Total delivered heat"),
    ]
    fig.legend(
        handles=legend_elements,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.935),
        ncol=4,
        fontsize=FONTS["annotation"],
        frameon=False,
        columnspacing=1.4,
        handlelength=1.6,
        handletextpad=0.45,
    )

    return fig


if __name__ == "__main__":
    data = load_aspen_data()
    fig = plot_waterfall(data)

    # ── Save ───────────────────────────────────────────────────────────────
    fig.savefig(OUTPUT_PREFIX.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)

    print(f"Figure saved to {OUTPUT_DIR}")

    # ── Data summary ───────────────────────────────────────────────────────
    fuel = data["fuel_input_w"]
    condenser = data["condenser_duty_w"]
    env = data["evaporator_uptake_w"]
    work = data["work_converted_w"]
    rb = data["reversible_benchmark_w"]

    print(f"\nData summary:")
    print(f"  Fuel input (LHV):         {fuel:10,.0f} W")
    print(f"  Environmental heat:       {env:10,.0f} W ({env/condenser*100:.1f}% of delivered)")
    print(f"  Work → heat (HP lift):    {work:10,.0f} W ({work/condenser*100:.1f}% of delivered)")
    print(f"  Total delivered heat:     {condenser:10,.0f} W")
    print(f"  Reversible benchmark:     {rb:10,.0f} W ({rb/fuel:.1f}× fuel)")
