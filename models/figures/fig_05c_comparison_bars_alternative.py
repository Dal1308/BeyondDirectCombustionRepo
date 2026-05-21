"""
models/figures/fig_05c_comparison_bars_alternative.py

Alternative Fig. 5(c) comparison bars.

Horizontal four-bar version of ``fig_05c_comparison_bars.py``. It preserves
the same Aspen + Layer 2 provenance and shared manuscript style, but presents
the comparison directly as Q / |Delta H_rxn| with the direct-combustion
reference, practical comparator, Aspen worked case, and reversible ceiling.
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".mplconfig"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np

# -- Central palette + style system ------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from models.figures.config import current_palette as _C
from models.figures.fig_05c_comparison_bars import load_aspen_data
from models.figures.style import apply

apply()

_BG = _C["background"]
_GRID = _C["grid"]
_TXT = _C["text_primary"]
_SUBTXT = _C["text_secondary"]

# -- Output path --------------------------------------------------------------
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PREFIX = OUTPUT_DIR / "fig_05c_comparison_bars_alternative"

# Explicit colours from the requested alternative mock-up.
_COL_DIRECT = "#BDBDBD"
_COL_PRACTICAL = "#E6B54A"
_COL_WORKED = "#3F6FB5"
_COL_REVERSIBLE = "#D73027"


def _comparison_rows(data):
    """Return ordered row metadata on a fixed-fuel, dimensionless basis."""
    fuel = data["fuel_input_w"]
    return [
        {
            "label": "Direct combustion\n(reference)",
            "value": data["comparator_100_w"] / fuel,
            "text": "1.0x",
            "color": _COL_DIRECT,
        },
        {
            "label": "Practical comparator\n(~90% efficient boiler)",
            "value": data["comparator_90_w"] / fuel,
            "text": "~0.9x",
            "color": _COL_PRACTICAL,
        },
        {
            "label": "Aspen worked case\n(this study)",
            "value": data["worked_case_w"] / fuel,
            "text": f"~{data['worked_case_w'] / fuel:.1f}x",
            "color": _COL_WORKED,
        },
        {
            "label": "Reversible ceiling\n($T_C$ = 25$^\\circ$C, $T_H$ = 60$^\\circ$C)",
            "value": data["reversible_benchmark_w"] / fuel,
            "text": f"~{data['reversible_benchmark_w'] / fuel:.1f}x",
            "color": _COL_REVERSIBLE,
        },
    ]


def plot_comparison_bars_alternative(data):
    """Generate the horizontal four-bar comparison figure."""
    rows = _comparison_rows(data)

    fig, ax = plt.subplots(figsize=(6.6, 4.4))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)

    y_pos = np.arange(len(rows))
    values = [row["value"] for row in rows]
    colors = [row["color"] for row in rows]

    bars = ax.barh(
        y_pos,
        values,
        height=0.56,
        color=colors,
        edgecolor=[_SUBTXT, _COL_PRACTICAL, _COL_WORKED, _COL_REVERSIBLE],
        linewidth=0.9,
        alpha=0.95,
        zorder=3,
    )

    # Subtle print-friendly lift without departing from the house style.
    for bar in bars:
        bar.set_path_effects(
            [
                pe.SimplePatchShadow(offset=(1.0, -1.0), alpha=0.12, rho=0.9),
                pe.Normal(),
            ]
        )

    ax.axvline(
        1.0,
        color=_SUBTXT,
        linestyle=(0, (3, 3)),
        linewidth=1.25,
        alpha=0.75,
        zorder=2,
    )

    ax.set_xlim(0, 10)
    ax.set_ylim(-0.55, len(rows) - 0.45)
    ax.invert_yaxis()
    ax.set_xticks(np.arange(0, 11, 2))
    ax.set_xlabel(
        r"$Q\,/\,|\Delta H^\circ_{\mathrm{rxn}}|$  (-)",
        color=_TXT,
        fontsize=13.5,
        labelpad=8,
    )

    ax.set_yticks(y_pos)
    ax.set_yticklabels([row["label"] for row in rows], fontweight="bold", fontsize=10.8)
    ax.tick_params(axis="y", length=4, width=1.0, pad=6, colors=_TXT)
    ax.tick_params(axis="x", length=5, width=1.0, colors=_TXT, labelsize=11.3)

    for tick, row in zip(ax.get_yticklabels(), rows):
        tick.set_color(row["color"] if row["color"] != _COL_DIRECT else _TXT)

    for idx, row in enumerate(rows):
        ax.text(
            row["value"] + 0.22,
            idx,
            row["text"],
            va="center",
            ha="left",
            fontsize=13.0,
            fontweight="bold",
            color=row["color"] if row["color"] != _COL_DIRECT else _TXT,
        )

    fig.text(
        0.57,
        0.90,
        "Performance relative to direct combustion",
        ha="center",
        va="bottom",
        fontsize=10.2,
        fontweight="bold",
        color=_TXT,
    )

    ax.grid(False)
    ax.grid(True, axis="x", alpha=0.16, linestyle="-", color=_GRID, zorder=1)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.9)
    ax.spines["bottom"].set_linewidth(0.9)
    ax.spines["left"].set_color(_SUBTXT)
    ax.spines["bottom"].set_color(_SUBTXT)

    fig.subplots_adjust(left=0.34, right=0.96, top=0.84, bottom=0.18)
    return fig


if __name__ == "__main__":
    data = load_aspen_data()
    fig = plot_comparison_bars_alternative(data)

    fig.savefig(OUTPUT_PREFIX.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)

    fuel = data["fuel_input_w"]
    print(f"Figure saved to {OUTPUT_DIR}")
    print("\nData summary (Q / |Delta H_rxn| basis):")
    print(f"  Direct combustion reference: {data['comparator_100_w'] / fuel:.1f}x")
    print(f"  Practical comparator:        {data['comparator_90_w'] / fuel:.1f}x")
    print(f"  Aspen worked case:           {data['worked_case_w'] / fuel:.1f}x")
    print(f"  Reversible ceiling:          {data['reversible_benchmark_w'] / fuel:.1f}x")
