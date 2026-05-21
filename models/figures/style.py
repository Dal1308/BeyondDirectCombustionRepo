"""
models/figures/style.py

Apply the active palette colours to matplotlib rcParams so that
grid, text, and background all match the chosen palette automatically.

Usage:
    from models.figures.style import apply
    apply()       # sets grid color, bg, axes colours from current palette
"""

import matplotlib.pyplot as plt
from .config import current_palette as _C
from .config import STYLE_DEFAULTS
from .config.font_config import FONTS


def apply():
    """
    Update matplotlib rcParams with STYLE_DEFAULTS + palette-specific
    colours + central font sizes. Call once at the top of every figure script.
    """
    plt.rcParams.update(STYLE_DEFAULTS)

    # Override style parameters that depend on the active palette
    overrides = {
        "axes.facecolor":     _C["background"],
        "figure.facecolor":   _C["background"],
        "grid.color":         _C["grid"],
        "xtick.color":        _C["text_secondary"],
        "ytick.color":        _C["text_secondary"],
        "axes.labelcolor":    _C["text_primary"],
        # Central font sizes (font_config.py)
        "axes.labelsize":     FONTS["axis_label"],
        "axes.titlesize":     FONTS["title"],
        "xtick.labelsize":    FONTS["tick"],
        "ytick.labelsize":    FONTS["tick"],
        "legend.fontsize":    FONTS["annotation"],
    }
    plt.rcParams.update(overrides)


def reset():
    """Restore matplotlib defaults (useful for testing)."""
    plt.rcParams.update(plt.rcParamsDefault)


__all__ = ["apply", "reset"]
