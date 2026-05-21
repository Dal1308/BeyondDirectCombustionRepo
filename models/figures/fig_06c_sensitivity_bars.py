"""
models/figures/fig_06c_sensitivity_bars.py

Target: Fig. 6(c) — Parameter sensitivity bars (Layer 4 SI).

Grouped bar chart showing how % change in delivered heat varies when
each Layer 4 model parameter is set to its literature range bounds.
Reads from pre-computed sensitivity_data.csv (Gate B compliant).

Complements Fig. 6(a) forest plot by showing *impact* rather than
just *evidence*.

Data provenance:
    sensitivity_data.csv — Layer 4 R134a architecture-space model,
    pre-computed at fuel_flow=1e-3 kg/s, t_source=15°C, mode=predictive.
    Out-of-envelope cases marked with status fields; pct_change is NaN.

Caption (draft):
    "Sensitivity of delivered heat to parameter bounds. Each pair of
     bars shows the % change when a parameter is set to its low or
     high literature bound relative to the chosen value. η_engine
     has the largest impact: lowering it by 10 percentage points
     reduces delivered heat by ~10%. Higher recovery effectiveness
     (f_rec) and UA_condenser both increase delivered heat, while
     η_iso and η_engine (at high bound) are out-of-envelope for
     this operating point."
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
_TXT_SEC = _C["text_secondary"]

# ── Output path ──────────────────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PREFIX = OUTPUT_DIR / "fig_06c_sensitivity_bars"

# ── Parameter display labels (LaTeX notation) ────────────────────────────────
PARAM_LABELS = {
    "eta_engine": r"$\eta_{\mathrm{engine}}$",
    "eta_iso": r"$\eta_{\mathrm{iso}}$",
    "recovery_effectiveness": r"$f_{\mathrm{rec}}$",
    "ua_condenser": r"$UA_{\mathrm{cond}}$",
}


def load_sensitivity_data():
    """Load pre-computed sensitivity analysis from Layer 4 output.

    Returns a DataFrame with columns:
        parameter, label, low_val, high_val, low_status, high_status,
        pct_change_low, pct_change_high
    Out-of-envelope cases have NaN pct_change values.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    data_path = project_root / "models" / "thermodynamic" / "brayton_heat_pump_architecture_space" / "output" / "sensitivity_data.csv"
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} parameters from {data_path.name}")
    for _, row in df.iterrows():
        status_parts = []
        if pd.notna(row["pct_change_low"]):
            status_parts.append(f"low={row['pct_change_low']:+.1f}%")
        else:
            status_parts.append(f"low=OOE ({row.get('low_status_msg', '')[:30]})")
        if pd.notna(row["pct_change_high"]):
            status_parts.append(f"high={row['pct_change_high']:+.1f}%")
        else:
            status_parts.append(f"high=OOE ({row.get('high_status_msg', '')[:30]})")
        print(f"  {row['parameter']:25s} | {', '.join(status_parts)}")
    return df


def plot_sensitivity(df):
    """Generate grouped bar chart of parameter sensitivity."""
    fig, ax = plt.subplots(figsize=(7.5, 6.0))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)

    # Sort parameters in a logical order
    param_order = ["eta_engine", "eta_iso", "recovery_effectiveness", "ua_condenser"]
    df = df[df["parameter"].isin(param_order)].sort_values(
        by="parameter", key=lambda x: x.map({p: i for i, p in enumerate(param_order)})
    ).reset_index(drop=True)

    n_params = len(df)
    x_pos = np.arange(n_params)
    bar_width = 0.35

    # Collect valid values for y-axis limits
    all_changes = []
    for _, row in df.iterrows():
        if pd.notna(row["pct_change_low"]):
            all_changes.append(row["pct_change_low"])
        if pd.notna(row["pct_change_high"]):
            all_changes.append(row["pct_change_high"])

    y_max = max(abs(c) for c in all_changes) * 1.3 if all_changes else 10
    ax.set_ylim(-y_max, y_max)

    # Draw bars
    for i, (_, row) in enumerate(df.iterrows()):
        x = x_pos[i]

        # Low bound bar
        if pd.notna(row["pct_change_low"]):
            bar = ax.bar(x - bar_width / 2, row["pct_change_low"], bar_width,
                         label="Low bound" if i == 0 else "",
                         color=_C["mid"], edgecolor="white", linewidth=0.5)
            # Value label
            h = row["pct_change_low"]
            ax.text(x - bar_width / 2, h, f"{h:+.1f}%",
                    ha="center", va="bottom" if h > 0 else "top",
                    fontsize=FONTS["annotation"], color=_TXT)
        else:
            # OOE marker
            ax.text(x - bar_width / 2, 0, "OOE",
                    ha="center", va="center",
                    fontsize=FONTS["annotation"], color=_TXT_SEC, alpha=0.5)

        # High bound bar
        if pd.notna(row["pct_change_high"]):
            bar = ax.bar(x + bar_width / 2, row["pct_change_high"], bar_width,
                         label="High bound" if i == 0 else "",
                         color=_C["hot"], edgecolor="white", linewidth=0.5)
            # Value label
            h = row["pct_change_high"]
            ax.text(x + bar_width / 2, h, f"{h:+.1f}%",
                    ha="center", va="bottom" if h > 0 else "top",
                    fontsize=FONTS["annotation"], color=_TXT)
        else:
            # OOE marker
            ax.text(x + bar_width / 2, 0, "OOE",
                    ha="center", va="center",
                    fontsize=FONTS["annotation"], color=_TXT_SEC, alpha=0.5)

    # Baseline reference line
    ax.axhline(y=0, color=_GRID, linewidth=1.0, linestyle="--", alpha=0.6)

    # ── Axis formatting ──────────────────────────────────────────────────
    ax.set_xticks(x_pos)
    ax.set_xticklabels([PARAM_LABELS.get(p, p) for p in df["parameter"]],
                       fontsize=FONTS["tick"], color=_TXT)
    ax.set_ylabel("Change in delivered heat (%)", fontsize=FONTS["axis_label"], color=_TXT)

    # ── Title ────────────────────────────────────────────────────────────
    fig.suptitle(
        "Delivered-heat sensitivity — Layer 4 parameter bounds",
        fontsize=FONTS["title"], fontweight="bold", color=_TXT, y=0.98,
    )

    # ── Formatting ───────────────────────────────────────────────────────
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.yaxis.set_ticks_position("none")
    ax.xaxis.set_ticks_position("bottom")
    ax.grid(True, axis="y", alpha=0.3, linestyle="--", color=_GRID)

    # ── Legend ───────────────────────────────────────────────────────────
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=_C["mid"], edgecolor="white", linewidth=0.5,
              label="Low bound"),
        Patch(facecolor=_C["hot"], edgecolor="white", linewidth=0.5,
              label="High bound"),
    ]
    fig.legend(handles=legend_elements, loc="upper center",
              bbox_to_anchor=(0.5, 0.91),
              ncol=2, fontsize=FONTS["annotation"],
              frameon=False)

    fig.subplots_adjust(left=0.13, right=0.97, top=0.80, bottom=0.14)
    return fig


if __name__ == "__main__":
    df = load_sensitivity_data()
    fig = plot_sensitivity(df)

    # ── Save ───────────────────────────────────────────────────────────────
    fig.savefig(OUTPUT_PREFIX.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"Figure saved to {OUTPUT_DIR}")
