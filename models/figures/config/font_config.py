"""
models/figures/config/font_config.py

Central font-size configuration for all manuscript figures.

Change ``BASE_SIZE`` to scale every figure's fonts proportionally.
All derived sizes are offsets from BASE_SIZE so the relative hierarchy
(titles > axis labels > ticks > annotations) is preserved at any scale.

Usage in a figure script::

    from models.figures.config.font_config import FONTS
    ax.set_title("…", fontsize=FONTS["title"])
    ax.tick_params(labelsize=FONTS["tick"])

Composite SVG figures use ``COMPOSITE`` instead (separate namespace
because SVG point sizing does not map 1:1 to matplotlib pt).

To change all figure fonts at once, edit only this file.
"""

# ═══════════════════════════════════════════════════════════
# Global base — change this one number to resize everything
# ═══════════════════════════════════════════════════════════
BASE_SIZE: int = 17

# ── Derived font sizes (offsets from BASE_SIZE) ───────────────
# Each key maps to the offset applied to BASE_SIZE.
# Titles are largest, contour/annotation labels smallest.

_FONT_OFFSETS = {
    "title":        +1,       # panel titles
    "axis_label":   +0,       # axis label text
    "tick":         -1,       # tick labels
    "colorbar":     -1,       # colorbar axis labels
    "annotation":   -2.5,     # callouts, markers, legends inside axes
    "reference":    -2.5,     # reference-line annotations
    "contour":      -3,       # contour label text
}

# ── Public API ────────────────────────────────────────────────

FONTS = {key: BASE_SIZE + offset for key, offset in _FONT_OFFSETS.items()}

COMPOSITE = {
    "panel_label":    8.0,
    "heading":        8.5,
    "text_min":       5.0,
    "text_max":       7.0,
}

__all__ = ["BASE_SIZE", "FONTS", "COMPOSITE"]
