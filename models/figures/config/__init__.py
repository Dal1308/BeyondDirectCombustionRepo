# models/figures/config/__init__.py
# Central palette entry-point for all figure generation scripts.
#
# Usage:
#   from figures.config import current_palette as C
#   from figures.config import sequential_colormap
#   sns.barplot(..., color=C['work_path'])
#   ax.contourf(..., cmap=sequential_colormap(['cold', 'mid', 'hot', 'peak']))
#
# Hot-swap: edit PALETTE_NAME or set FIGURE_PALETTE env var before import.

import os
from .palettes import PALETTES, SEMANTIC_ROLES
from .style_config import STYLE_DEFAULTS

# Select palette — env var overrides default
PALETTE_NAME = os.environ.get("FIGURE_PALETTE", "nature").lower()

if PALETTE_NAME not in PALETTES:
    available = ", ".join(sorted(PALETTES.keys()))
    raise ValueError(f"Unknown palette '{PALETTE_NAME}'. Available: {available}")

current_palette = PALETTES[PALETTE_NAME]

# Semantic roles (order matters — controls legend order)
semantics = SEMANTIC_ROLES

# ── Sequential colormap helper ───────────────────────────────────────────────
# Builds a perceptually-ordered sequential colormap from palette colour slots,
# sorted by relative luminance so the gradient flows coherently.

def _hex_to_luminance(hex_color):
    """Compute relative luminance (perceptual brightness) of a hex colour."""
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    # sRGB to linear
    def linear(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b)


def sequential_colormap(slots, N=256):
    """Build a sequential colormap from palette slots sorted by luminance.

    Parameters
    ----------
    slots : list of str
        Semantic role keys to include (e.g. ['cold', 'mid', 'hot', 'peak']).
    N : int
        Number of colormap samples.

    Returns
    -------
    matplotlib.colors.LinearSegmentedColormap
        Colormap with colours ordered by perceptual luminance (dark → light).
    """
    import matplotlib.colors as mcolors
    colours = [current_palette[s] for s in slots]
    lum = [_hex_to_luminance(c) for c in colours]
    # Sort colours by luminance (ascending: dark → light)
    sorted_colours = [c for _, c in sorted(zip(lum, colours))]
    return mcolors.LinearSegmentedColormap.from_list(
        f"sequential_{PALETTE_NAME}", sorted_colours, N=N
    )


def diverging_colormap(slots, N=256):
    """Build a diverging colormap from palette slots in the given order.

    Unlike sequential_colormap, this preserves the slot order exactly —
    useful for maps where low→mid→high has a natural direction that does
    not follow luminance (e.g. cold → background → hot for fraction maps).

    Parameters
    ----------
    slots : list of str
        Semantic role keys in desired order (e.g. ['cold', 'background', 'hot']).
    N : int
        Number of colormap samples.

    Returns
    -------
    matplotlib.colors.LinearSegmentedColormap
        Colormap with colours in the specified slot order.
    """
    import matplotlib.colors as mcolors
    colours = [current_palette[s] for s in slots]
    return mcolors.LinearSegmentedColormap.from_list(
        f"diverging_{PALETTE_NAME}", colours, N=N
    )
