"""
models/figures/fig_04a_efficiency_violin.py

Target: Fig. 4(a) — Efficiency distribution violin plot (Layer 4 SI).

Shows η_effective distribution across Low/Med/High fuel-flow regimes
in the Brayton heat-pump architecture-space model sweep.

Data provenance:
    models/thermodynamic/brayton_heat_pump_architecture_space/output/
    multivariate_design_space.csv — Layer 4 R134a first-principles physics.
    Only status == valid rows are plotted (Gate B: out-of-envelope nulling).

Caption (draft):
    "Distribution of effective efficiency η_effective across three
     fuel-flow regimes in the Layer 4 architecture-space sweep.
     Lower fuel flows achieve higher effective efficiency, reflecting
     the sensitivity of the Brayton heat-pump cycle to source/sink
     temperature pairing within the R134a operating envelope."
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

OUTPUT_PREFIX = OUTPUT_DIR / "fig_04a_efficiency_violin"


def load_data():
    """Load multivariate design space from Layer 4 consolidated data/ and assign flow regimes.

    Returns a DataFrame with columns including:
        fuel_flow_kg_s, eta_effective, cop_hp, fuel_regime
    Only status == valid rows are returned (Gate B compliance).
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    data_path = project_root / "data" / "brayton_heat_pump_architecture_space" / "multivariate_design_space.csv"
    df = pd.read_csv(data_path)

    # Gate B: only valid rows (out-of-envelope cases have null performance fields)
    df = df[df["status"] == "valid"].copy()

    # Assign regimes by qcut on fuel flow
    df["fuel_regime"] = pd.qcut(
        df["fuel_flow_kg_s"], q=3,
        labels=["Low Flow", "Med Flow", "High Flow"]
    )

    print(f"Loaded {len(df)} valid rows from {data_path.name}. "
          f"Regimes: {df['fuel_regime'].value_counts().sort_index().to_dict()}")
    return df


def plot_violin(df):
    """Generate efficiency distribution violin plot across flow regimes."""
    fig, ax = plt.subplots(figsize=(8.5, 6.0))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)

    order = ["Low Flow", "Med Flow", "High Flow"]
    # Energy chain: low flow (cold/violet), med (mid/blue), high (hot/magenta)
    regime_colors = [_C["cold"], _C["mid"], _C["hot"]]

    # Build violin data
    regimes = df["fuel_regime"].astype("category")
    regimes = regimes.cat.reorder_categories(order)
    eta_vals = df["eta_effective"]

    parts = ax.violinplot(
        [eta_vals[regimes == r].values for r in order],
        positions=np.arange(len(order)),
        widths=0.45,
        showmeans=False,
        showmedians=False,
        showextrema=False,
    )

    # Color each violin body
    for i, pc in enumerate(parts["bodies"]):
        pc.set_facecolor(regime_colors[i])
        pc.set_alpha(0.7)
        pc.set_edgecolor("white")
        pc.set_linewidth(1.2)

    # Draw median lines (thick, white)
    for i, r in enumerate(order):
        median_val = eta_vals[regimes == r].median()
        ax.hlines(median_val, i - 0.25, i + 0.25, color="white", linewidth=2.0, zorder=10)

    # Draw quartile lines (thinner, white)
    for i, r in enumerate(order):
        vals = eta_vals[regimes == r].values
        q1, q3 = np.percentile(vals, [25, 75])
        ax.hlines(q1, i - 0.12, i + 0.12, color="white", linewidth=0.8, alpha=0.5, zorder=10)
        ax.hlines(q3, i - 0.12, i + 0.12, color="white", linewidth=0.8, alpha=0.5, zorder=10)

    # Axis formatting
    ax.set_xticks(np.arange(len(order)))
    ax.set_xticklabels(order, fontsize=FONTS["tick"], color=_TXT)
    ax.set_ylabel(r"Effective efficiency $\eta_{\mathrm{eff}}$", fontsize=FONTS["axis_label"], color=_TXT)
    ax.set_title(
        "Effective efficiency distribution by fuel-flow regime — "
        "Layer 4 architecture-space sweep",
        pad=12, fontsize=FONTS["title"], fontweight="bold", color=_TXT,
    )
    ax.grid(True, axis="y", alpha=0.4, linestyle="--", color=_GRID)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)

    # Y-axis: keep the new net-useful accounting visible even when eta_eff < 1
    lower = min(0.0, eta_vals.min() * 0.95)
    upper = max(eta_vals.max() * 1.08, 1.2)
    ax.set_ylim(lower, upper)

    fig.tight_layout()
    return fig


if __name__ == "__main__":
    df = load_data()
    fig = plot_violin(df)

    # ── Save ───────────────────────────────────────────────────────────────
    fig.savefig(OUTPUT_PREFIX.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"Figure saved to {OUTPUT_DIR}")

    # ── Data summary ───────────────────────────────────────────────────────
    regime_order = ["Low Flow", "Med Flow", "High Flow"]
    print(f"\nData summary:")
    for regime in regime_order:
        vals = df[df["fuel_regime"] == regime]["eta_effective"]
        print(f"  {regime:12s} | n={len(vals):3d} | "
              f"mean={vals.mean():.3f} | median={vals.median():.3f} | "
              f"range=[{vals.min():.2f}, {vals.max():.2f}]")
