"""
models/figures/fig_06b_regime_validity.py

Target: Fig. 6(b) — Regime validity contour (Layer 4 SI).

Contour plot showing where R134a operation is valid vs. out-of-envelope
across η_engine × UA_condenser parameter space.

Demonstrates model transparency: how much of the design space the
Brayton heat-pump architecture-space model actually covers with
physically coherent operation.

Data provenance:
    regime_validity_sweep.csv — Layer 4 R134a first-principles physics,
    η_engine × UA_condenser sweep with status field (Gate B compliant).

Caption (draft):
    "R134a regime validity across the η_engine × UA_condenser design space.
     The valid region (green) occupies approximately 60% of the swept
     parameter space, bounded by sink-temperature constraints that push
     R134a beyond its critical point at high η_engine / low UA combinations.
     The baseline operating point (magenta dot) sits well within the valid
     region."
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

OUTPUT_PREFIX = OUTPUT_DIR / "fig_06b_regime_validity_contour"


def load_sweep_data():
    """Load regime validity sweep from Layer 4 consolidated data/.

    Returns a DataFrame with columns:
        eta_engine, ua_condenser, status, is_valid, status_msg
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    sweep_path = project_root / "data" / "brayton_heat_pump_architecture_space" / "regime_validity_sweep.csv"
    df = pd.read_csv(sweep_path)
    print(f"Loaded {len(df)} sweep points from {sweep_path.name}")
    valid_count = (df["status"] == "valid").sum()
    print(f"  Valid: {valid_count} ({valid_count/len(df)*100:.0f}%) | "
          f"Out-of-envelope: {len(df) - valid_count}")
    return df


def plot_contour(df):
    """Generate regime-validity contour plot."""
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)

    # Binary validity: 1 = valid, 0 = out-of-envelope
    df["valid"] = (df["status"] == "valid").astype(int)

    # Pivot to grid for contouring
    eta_unique = sorted(df["eta_engine"].unique())
    ua_unique = sorted(df["ua_condenser"].unique())
    validity_grid = df.pivot(
        index="ua_condenser", columns="eta_engine", values="valid"
    ).values

    # Interpolate for smoother contour
    from scipy.interpolate import griddata

    points = df[["eta_engine", "ua_condenser"]].values
    validity_flat = df["valid"].values

    # Fine grid for interpolation
    eta_fine = np.linspace(eta_unique[0], eta_unique[-1], 200)
    ua_fine = np.linspace(ua_unique[0], ua_unique[-1], 200)
    eta_fine_grid, ua_fine_grid = np.meshgrid(eta_fine, ua_fine)

    validity_interp = griddata(
        points, validity_flat,
        (eta_fine_grid, ua_fine_grid),
        method="linear", fill_value=0.5,
    )

    # Contour fill: valid (1) vs invalid (0)
    cf = ax.contourf(
        eta_fine_grid, ua_fine_grid, validity_interp,
        levels=[0, 0.5, 1],
        colors=[_C["hot"], _C["mid"]],
        alpha=0.6,
    )

    # Contour line at boundary (validity = 0.5)
    ax.contour(
        eta_fine_grid, ua_fine_grid, validity_interp,
        levels=[0.5], colors=_TXT, linewidths=1.5, linestyles="-",
    )

    # Plot actual sweep points
    valid_pts = df[df["valid"] == 1]
    invalid_pts = df[df["valid"] == 0]

    ax.scatter(
        valid_pts["eta_engine"], valid_pts["ua_condenser"],
        c=_C["mid"], s=60, edgecolors="white", linewidths=0.5,
        zorder=5, label="Valid R134a",
    )
    ax.scatter(
        invalid_pts["eta_engine"], invalid_pts["ua_condenser"],
        c=_C["hot"], s=60,
        zorder=5, marker="x", label="Out-of-envelope",
    )

    # ── Baseline point marker (from parameters.yaml) ─────────────────────
    # Read baseline from parameters registry
    import yaml
    project_root = Path(__file__).resolve().parent.parent.parent
    params_path = project_root / "docs" / "planning" / "registry" / "parameters.yaml"
    with open(params_path) as f:
        params_data = yaml.safe_load(f)
    reg_params = {p["name"]: p for p in params_data["parameters"]}
    baseline_eta = float(reg_params["eta_engine"]["current_value"])

    # UA baseline from sensitivity_data.csv (the baseline case used there)
    sens_path = project_root / "models" / "thermodynamic" / "brayton_heat_pump_architecture_space" / "output" / "sensitivity_data.csv"
    sens_df = pd.read_csv(sens_path)
    ua_row = sens_df[sens_df["parameter"] == "ua_condenser"].iloc[0]
    baseline_ua = (float(ua_row["low_val"]) + float(ua_row["high_val"])) / 2

    ax.plot(
        baseline_eta, baseline_ua, "o", markersize=12,
        color=_C["peak"], markeredgecolor="white", markeredgewidth=2,
        zorder=6,
    )

    # ── Axis formatting ──────────────────────────────────────────────────
    ax.set_xlabel(r"$\eta_{\mathrm{engine}}$", fontsize=FONTS["axis_label"], color=_TXT)
    ax.set_ylabel("UA_condenser (W/K)", fontsize=FONTS["axis_label"], color=_TXT)
    ax.set_xlim(0.18, 0.42)
    ax.set_ylim(800, 3200)

    # ── Title ────────────────────────────────────────────────────────────
    valid_pct = len(valid_pts) / len(df) * 100
    fig.suptitle(
        f"R134a regime validity — {valid_pct:.0f}% of "
        r"$\eta_{\mathrm{engine}} \times UA$" + " space covered",
        fontsize=FONTS["title"], fontweight="bold", color=_TXT, y=0.98,
    )

    # ── Formatting ───────────────────────────────────────────────────────
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.grid(True, alpha=0.3, linestyle="--", color=_GRID)

    # ── Legend ───────────────────────────────────────────────────────────
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    legend_elements = [
        Patch(facecolor=_C["mid"], alpha=0.6, edgecolor="white", linewidth=0.5,
              label="Valid R134a"),
        Patch(facecolor=_C["hot"], alpha=0.6, edgecolor="white", linewidth=0.5,
              label="Out-of-envelope"),
        Line2D([0], [0], color=_TXT, linewidth=1.5, linestyle="-",
               label="Validity boundary"),
        Line2D([0], [0], marker="o", color=_C["peak"], markersize=10,
               markeredgecolor="white", markeredgewidth=2, linestyle="None",
               label=f"Baseline\n(η={baseline_eta:.2f}, UA={baseline_ua:.0f})"),
    ]
    fig.legend(handles=legend_elements, loc="upper center",
              bbox_to_anchor=(0.5, 0.91),
              ncol=2, fontsize=FONTS["annotation"],
              frameon=False)
    fig.subplots_adjust(left=0.12, right=0.97, top=0.78, bottom=0.14)
    return fig


if __name__ == "__main__":
    df = load_sweep_data()
    fig = plot_contour(df)

    # ── Save ───────────────────────────────────────────────────────────────
    fig.savefig(OUTPUT_PREFIX.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(OUTPUT_PREFIX.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"Figure saved to {OUTPUT_DIR}")
