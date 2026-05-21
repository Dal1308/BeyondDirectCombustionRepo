"""
models/figures/config/style_config.py

Global style defaults for Nature Chemical Engineering manuscript figures.
These are applied once at module import — all figure scripts inherit them
unless they explicitly override individual parameters.

To use:
    from figures.config import STYLE_DEFAULTS
    import matplotlib.pyplot as plt
    plt.rcParams.update(STYLE_DEFAULTS)
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ── Default style dictionary (applied via plt.rcParams.update()) ───────────────

STYLE_DEFAULTS = {
    # Font family: DejaVu Sans for consistency, Helvetica fallback
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial", "sans-serif"],
    "pdf.fonttype": 42,           # embed TrueType fonts in exported PDFs
    "svg.fonttype": "none",       # keep text editable in SVGs

    # Panel sizing
    "figure.dpi": 300,
    "figure.figsize": (8.5, 6.0),
    "figure.facecolor": "#ffffff",

    # Axes
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": True,
    "axes.spines.bottom": True,
    "axes.grid.axis": "y",
    "grid.linestyle": "--",
    "grid.alpha": 0.4,
    "axes.labelsize": 12,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",

    # Ticks
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,

    # Legend
    "legend.fontsize": 9,
    "legend.frameon": True,
    "legend.edgecolor": "#cccccc",
    "legend.fancybox": False,
    "legend.loc": "best",

    # Bar / scatter styling
    "patch.linewidth": 0.5,
    "lines.linewidth": 1.5,
    "scatter.marker": "o",

    # Subplot spacing
    "figure.subplot.wspace": 0.3,
    "figure.subplot.hspace": 0.4,
}

# ── Convenience: apply defaults immediately when imported ──────────────────────
plt.rcParams.update(STYLE_DEFAULTS)
