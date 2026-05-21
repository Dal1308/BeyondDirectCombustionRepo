"""
models/figures/fig_06a_parameter_forest.py

Target: Fig. 6(a) — Parameter evidence forest plot (Layer 4 SI).

Shows literature ranges (horizontal lines) and chosen values (dots) for
the four Layer 4 model parameters, with source citations.

Data provenance:
    Parameters: docs/planning/registry/parameters.yaml
        - eta_engine: 0.30 [0.20–0.40] — baseline-backed
        - eta_heat_upgrade: 0.35 [0.20–0.50] — baseline-backed
        - recovered_heat_fraction: 0.55 [0.50–0.75] — range-backed
        - eta_iso: 0.75 [0.70–0.85] — range-backed
    Sources: docs/planning/registry/sources.yaml
        - Each parameter's source_keys mapped to admissible sources

Caption (draft):
    "Evidence ranges and literature anchors for the four Layer 4 model
     parameters. Horizontal lines show the literature-supported range
     for each parameter; dots mark the chosen values used in the
     architecture-space sweep. All parameters are baseline-backed or
     range-backed per the repo evidence hierarchy."
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".mplconfig"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml

# ── Central palette + style system ───────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from models.figures.config import current_palette as _C
from models.figures.style import apply
apply()
from models.figures.config.font_config import FONTS

_BG = _C["background"]
_GRID = _C["grid"]
_TXT = _C["text_primary"]
_TXT_SEC = _C["text_secondary"]

# ── Output path ──────────────────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PREFIX = OUTPUT_DIR / "fig_06a_parameter_forest_plot"

# ── Layer 4 parameter names (subset of registry) ─────────────────────────────
LAYER4_PARAM_NAMES = [
    "eta_engine",
    "eta_heat_upgrade",
    "recovered_heat_fraction",
    "eta_iso",
]


def _source_short_name(citation_key, source_dict):
    """Build a short "Author Year" citation from a sources.yaml entry.

    For academic papers (key ends with 4-digit year): extract author + year.
    For institutional/product sources: use a readable short label.
    """
    parts = citation_key.split("_")

    # Check if key ends with a 4-digit year (academic paper pattern)
    if len(parts) >= 2 and parts[-1].isdigit() and len(parts[-1]) == 4:
        author = parts[0].title()
        year = parts[-1]
        return f"{author} {year}"

    # Institutional/product source — derive a short label from the key
    if citation_key == "epa_methods_calculating_chp_efficiency":
        return "EPA Methods"
    if citation_key == "epa_catalog_chp_microturbines":
        return "EPA Catalog"
    if citation_key.startswith("capstone_"):
        return "Capstone C65"
    if citation_key.startswith("ansaldo_"):
        return "Ansaldo T100NG"
    # Fallback: use first word of key, title-cased
    return parts[0].title()


def load_parameters():
    """Load Layer 4 parameters from the YAML registry.

    Returns a list of dicts with keys:
        name, label, value, low, high, unit, sources (list of short names)
    Only the four Layer 4 model parameters are included.
    """
    project_root = Path(__file__).resolve().parent.parent.parent

    # Load parameters registry
    params_path = project_root / "docs" / "planning" / "registry" / "parameters.yaml"
    with open(params_path) as f:
        params_data = yaml.safe_load(f)

    # Load sources registry for citation lookup
    sources_path = project_root / "docs" / "planning" / "registry" / "sources.yaml"
    with open(sources_path) as f:
        sources_data = yaml.safe_load(f)
    sources_by_key = {s["citation_key"]: s for s in sources_data["sources"]}

    # Filter to Layer 4 parameters
    reg_params = {p["name"]: p for p in params_data["parameters"]
                  if p["state"] == "active"}

    result = []
    for name in LAYER4_PARAM_NAMES:
        p = reg_params[name]

        # Parse range
        range_str = p.get("sensitivity_range", "fixed")
        if range_str == "fixed":
            low = high = float(p["current_value"])
        else:
            low, high = [float(x) for x in range_str.split("-")]

        # Resolve source short names from registry
        source_keys = p.get("source_keys", [])
        source_names = []
        for key in source_keys:
            src = sources_by_key.get(key, {})
            short = _source_short_name(key, src)
            if short:
                source_names.append(short)

        # Build LaTeX label
        label_map = {
            "eta_engine": r"$\eta_{\mathrm{engine}}$",
            "eta_heat_upgrade": r"$\eta_{\mathrm{heat\_upgrade}}$",
            "recovered_heat_fraction": r"$f_{\mathrm{rec}}$",
            "eta_iso": r"$\eta_{\mathrm{iso}}$",
        }

        result.append({
            "name": name,
            "label": label_map.get(name, name),
            "value": float(p["current_value"]),
            "low": low,
            "high": high,
            "unit": p.get("unit", ""),
            "sources": source_names,
        })

    print(f"Loaded {len(result)} Layer 4 parameters from parameters.yaml")
    return result


def plot_forest(parameters):
    """Generate parameter evidence forest plot."""
    fig, ax = plt.subplots(figsize=(7.5, 6.0))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)

    n = len(parameters)
    y_pos = np.arange(n)
    row_height = 0.6

    # Determine x-axis range from all parameter ranges
    all_low = min(p["low"] for p in parameters)
    all_high = max(p["high"] for p in parameters)
    ax.set_xlim(all_low, all_high)

    # Draw each parameter row
    for i, param in enumerate(parameters):
        y = y_pos[i]

        # Literature range line
        ax.plot([param["low"], param["high"]], [y, y],
                color=_TXT_SEC, linewidth=2.0, alpha=0.6)

        # End caps on range line
        ax.plot([param["low"], param["low"]],
                [y - row_height * 0.35, y + row_height * 0.35],
                color=_TXT_SEC, linewidth=2.0, alpha=0.6)
        ax.plot([param["high"], param["high"]],
                [y - row_height * 0.35, y + row_height * 0.35],
                color=_TXT_SEC, linewidth=2.0, alpha=0.6)

        # Chosen value marker
        ax.plot(param["value"], y, "o", markersize=10,
                color=_C["mid"], markeredgecolor="white",
                markeredgewidth=1.5, zorder=5)
        ax.text(
            param["value"], y + row_height * 0.33, f"{param['value']:.2f}",
            ha="center", va="bottom", fontsize=FONTS["annotation"],
            color=_TXT, fontweight="bold",
        )

    # ── Y-axis labels ────────────────────────────────────────────────────
    ax.set_yticks(y_pos)
    ax.set_yticklabels([p["label"] for p in parameters],
                       fontsize=FONTS["tick"], color=_TXT)

    # Source annotations stacked vertically, centred on the parameter row
    right_margin = all_high + (all_high - all_low) * 0.05
    line_height = 0.25  # approximate height of one text line in axes coords
    for i, param in enumerate(parameters):
        sources = list(reversed(param["sources"]))  # first source at top
        if not sources:
            continue
        n_lines = len(sources)
        total_height = (n_lines - 1) * line_height
        y_start = y_pos[i] - total_height / 2
        for j, src in enumerate(sources):
            ax.text(right_margin, y_start + j * line_height, src,
                    ha="left", va="center", fontsize=FONTS["annotation"],
                    color=_TXT_SEC, clip_on=False)

    # ── X-axis ───────────────────────────────────────────────────────────
    ax.set_xlabel("Parameter value", fontsize=FONTS["axis_label"], color=_TXT)

    # Keep the compact composite panel readable: range endpoints plus midpoint.
    tick_vals = [all_low, (all_low + all_high) / 2, all_high]
    ax.set_xticks(tick_vals)
    ax.set_xticklabels([f"{t:.2f}" for t in tick_vals],
                       fontsize=FONTS["tick"], color=_TXT_SEC)

    # ── Title ────────────────────────────────────────────────────────────
    fig.suptitle(
        "Parameter evidence ranges and literature anchors — "
        "Layer 4 model",
        fontsize=FONTS["title"], fontweight="bold", color=_TXT, y=0.98,
    )

    # ── Formatting ───────────────────────────────────────────────────────
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.yaxis.set_ticks_position("none")
    ax.xaxis.set_ticks_position("bottom")
    ax.grid(True, axis="x", alpha=0.3, linestyle="--", color=_GRID)

    # ── Legend ───────────────────────────────────────────────────────────
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color=_TXT_SEC, linewidth=2.0,
               label="Literature range"),
        Line2D([0], [0], marker="o", color=_C["mid"], markersize=10,
               markeredgecolor="white", markeredgewidth=1.5, linestyle="None",
               label="Chosen value"),
    ]
    fig.legend(handles=legend_elements, loc="upper center",
              bbox_to_anchor=(0.5, 0.91),
              ncol=2, fontsize=FONTS["annotation"],
              frameon=False)

    # Adjust right margin to make room for source text
    fig.subplots_adjust(left=0.08, right=0.75, top=0.80, bottom=0.15)
    return fig


if __name__ == "__main__":
    params = load_parameters()
    fig = plot_forest(params)

    # ── Save ───────────────────────────────────────────────────────────────
    fig.savefig(OUTPUT_PREFIX.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"Figure saved to {OUTPUT_DIR}")

    # ── Data summary ───────────────────────────────────────────────────────
    print(f"\nParameter summary:")
    for p in params:
        print(f"  {p['name']:30s} | val={p['value']:.2f} | "
              f"range=[{p['low']:.2f}, {p['high']:.2f}]")
        if p["sources"]:
            for s in p["sources"][:2]:
                print(f"    → {s}")
