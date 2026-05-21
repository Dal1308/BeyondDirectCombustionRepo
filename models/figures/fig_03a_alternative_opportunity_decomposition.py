"""
models/figures/fig_03a_alternative_opportunity_decomposition.py

Target: Alternative to Fig. 3a — Horizontal stacked-bar opportunity decomposition.

Shows the reversible benchmark ceiling as a single horizontal bar decomposed
into additive segments relative to direct combustion:

    Direct combustion (1.0x) → Practical comparator (+0.9x) →
    Worked architecture gain (+~1.1x) → Remaining headroom (~5.7x)
    Total ceiling ≈ 8.7x

Data provenance:
    Reversible ceiling: models.independent.core.heating_multiplier()
        — entropy-balance theorem (SI Note 1 / Layer 2), methane at T_C=298 K,
          T_H=333 K.
    Aspen worked case: assets/aspen/export/current_base_case_key_outputs.csv
        — fuel_input_lhv_w and condenser_heat_duty_w.
    Practical comparators: fixed per AGENTS.md comparator framework
        — 90% boiler at 0.9x, direct combustion at 1.0x.

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
_TXT = _C["text_primary"]
_TXT_SEC = _C["text_secondary"]

# ── Output path ──────────────────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PREFIX = OUTPUT_DIR / "fig_03a_alternative_opportunity_decomposition"

# ── Thermodynamic data ───────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "independent"))
from models.independent.core import get_fuel, heating_multiplier

T_COLD_K = 298.0   # 25 °C — ambient source
T_HOT_K = 333.0    # 60 °C — domestic hot water delivery

# ── Load reversible ceiling ──────────────────────────────────────────────────
methane = get_fuel("methane")
reversible_ceiling = heating_multiplier(methane, T_COLD_K, T_HOT_K)

# ── Load Aspen worked case ratio ─────────────────────────────────────────────
aspen_path = Path(__file__).resolve().parent.parent.parent / \
             "assets/aspen/export/current_base_case_key_outputs.csv"
if aspen_path.exists():
    aspen_df = __import__("pandas").read_csv(aspen_path)
    fuel_input = float(
        aspen_df.loc[aspen_df["quantity"] == "fuel_input_lhv_w", "value"].values[0]
    )
    condenser_duty = float(
        aspen_df.loc[aspen_df["quantity"] == "condenser_heat_duty_w", "value"].values[0]
    )
    aspen_ratio = condenser_duty / fuel_input if fuel_input > 0 else None
else:
    aspen_ratio = None

# ── Fixed comparators (AGENTS.md) ────────────────────────────────────────────
DIRECT_COMBUSTION = 1.0
PRACTICAL_BOILER = 0.9

# ── Compute segment widths and positions ─────────────────────────────────────
# Segments are additive contributions stacked sequentially:
#   grey  = direct combustion baseline (1.0)
#   orange = practical comparator contribution (0.9)
#   blue  = additional gain from worked architecture + heat recovery (~1.1)
#   pink  = remaining headroom to reversible ceiling (fills to ceiling exactly)

if aspen_ratio is not None:
    practical_width = PRACTICAL_BOILER  # absolute level of practical boiler
    architecture_width = aspen_ratio - PRACTICAL_BOILER  # HP above practical baseline
else:
    practical_width = 0.0
    architecture_width = 0.0

remaining_headroom = reversible_ceiling - DIRECT_COMBUSTION - practical_width - architecture_width

segments = [
    ("Direct combustion\n(reference)",      DIRECT_COMBUSTION,   "#8a8a8a", "#555555", "#333333"),
    ("Practical comparator\n(90% boiler)",  practical_width,     "#D4913E", "#B87A2D", "#6B4410"),
    ("HP architecture\n+ heat recovery",    architecture_width,  "#3A86C8", "#2A6AA8", "#0E3D5F"),
    ("Remaining headroom to\nreversible limit", remaining_headroom, "#E87D7D", "#C95050", "#9A2E2E"),
]

# Cumulative positions for bar placement
cumulative = [0.0]
for _, width, *_ in segments:
    cumulative.append(cumulative[-1] + width)

# ── Figure ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(28.0, 3.5))
fig.patch.set_facecolor(_BG)
ax.set_facecolor(_BG)

# ── Title ────────────────────────────────────────────────────────────────────
ax.set_title(
    "Decomposition of the opportunity (relative to direct combustion)",
    fontsize=FONTS["title"], fontweight="bold", color=_TXT, pad=16,
)

# ── Total opportunity arrow ──────────────────────────────────────────────────
arrow_y = 0.85
total_opportunity = reversible_ceiling - DIRECT_COMBUSTION
ax.annotate(
    "",
    xy=(DIRECT_COMBUSTION, arrow_y),
    xytext=(reversible_ceiling, arrow_y),
    arrowprops=dict(arrowstyle="<->", color=_TXT_SEC, lw=1.2),
)
ax.text(
    (DIRECT_COMBUSTION + reversible_ceiling) / 2, arrow_y + 0.07,
    f"Total opportunity above direct combustion (≈ {total_opportunity:.1f}×)",
    ha="center", va="bottom", fontsize=FONTS["annotation"], color=_TXT_SEC,
)

# ── Draw stacked bar segments ────────────────────────────────────────────────
bar_height = 0.45
bar_y = 0.2
for i, (label, width, fill_color, border_color, label_color) in enumerate(segments):
    x0 = cumulative[i]
    # Segment block
    rect = plt.Rectangle(
        (x0, bar_y - bar_height / 2), width, bar_height,
        facecolor=fill_color, edgecolor=label_color, linewidth=0.8, zorder=2,
    )
    ax.add_patch(rect)

    # Value label inside segment (or to the right for narrow segments)
    if width > 0.5:
        cx = x0 + width / 2
        ax.text(
            cx, bar_y, f"{width:.1f}×",
            ha="center", va="center",
            fontsize=18, fontweight="bold", color=label_color, zorder=3,
        )
    else:
        ax.text(
            x0 + width + 0.05, bar_y, f"{width:.1f}×",
            ha="left", va="center",
            fontsize=15, fontweight="bold", color=label_color, zorder=3,
        )

# ── Reversible ceiling dashed line (compact, above bar) ──────────────────────
line_y_min = bar_y - bar_height / 2 - 0.1
line_y_max = bar_y + bar_height / 2 + 0.1
ax.vlines(
    reversible_ceiling, line_y_min, line_y_max,
    color="#C95050", linestyle="--", linewidth=1.2,
    alpha=0.7, zorder=1,
)
ax.text(
    reversible_ceiling + 0.15, (line_y_min + line_y_max) / 2,
    "Reversible limit\n(~{:.1f}×)".format(reversible_ceiling),
    ha="left", va="center", fontsize=FONTS["annotation"], color="#C95050",
    fontweight="bold",
)
ax.set_ylim(-0.3, 0.95)

# ── Axis configuration ───────────────────────────────────────────────────────
ax.set_xlim(0, reversible_ceiling + 1.2)

ax.set_xticks([])
ax.set_yticks([])
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.spines["left"].set_visible(False)

# ── Save ─────────────────────────────────────────────────────────────────────
fig.savefig(OUTPUT_PREFIX.with_suffix(".png"), dpi=300, bbox_inches="tight")
fig.savefig(OUTPUT_PREFIX.with_suffix(".pdf"), bbox_inches="tight")
fig.savefig(OUTPUT_PREFIX.with_suffix(".svg"), bbox_inches="tight")
plt.close(fig)

# ── Data summary ─────────────────────────────────────────────────────────────
print(f"Figure saved to {OUTPUT_DIR}")
print(f"\nData summary (T_C = {T_COLD_K:.0f} K, T_H = {T_HOT_K:.0f} K):")
print(f"  Reversible ceiling (methane): {reversible_ceiling:.2f}×")
if aspen_ratio is not None:
    print(f"  Aspen worked case:          {aspen_ratio:.2f}×")
    print(f"  Gap to limit:               {remaining_headroom:.1f}×")
print(f"  Total opportunity above direct combustion: {total_opportunity:.1f}×")
