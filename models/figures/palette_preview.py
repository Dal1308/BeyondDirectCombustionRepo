"""
models/figures/palette_preview.py

Render all named palettes side-by-side for visual comparison.
Run:
    cd <repo-root>
    .venv/bin/python models/figures/palette_preview.py

Outputs:
    outputs/colour_palette_comparison.png  (1600x2400, one palette per row)
"""

import sys
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

# Insert models/ at path root so relative imports resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from figures.config.palettes import PALETTES, SEMANTIC_ROLES


def render_single_palette(palette_name: str, colours: dict) -> plt.Figure:
    """Build one row: swatches + semantic labels for a single palette."""
    fig, ax = plt.subplots(figsize=(10, 0.6), dpi=200)
    n = len(colours)
    bar_w = 0.8 / n

    for i, role in enumerate(SEMANTIC_ROLES):
        x = i / n
        rect = Rectangle((x - bar_w/2, 0), bar_w, 1,
                         facecolor=colours[role],
                         edgecolor="#cccccc",
                         linewidth=0.5)
        ax.add_patch(rect)
        # Role name in small white-on-black label above/below
        offset = -0.08 if i % 2 == 0 else 1.04
        ha = "center"
        va = "top" if offset < 0 else "bottom"
        y_pos = offset
        ax.text(x, y_pos, role.replace("_", " ").title(),
                fontsize=7, color="#333333",
                ha=ha, va=va)

    ax.set_xlim(0, 1)
    ax.set_ylim(-0.25, 1.25)
    ax.axis("off")
    fig.subplots_adjust(left=0.05, right=0.95, top=1.05, bottom=0.15)
    return fig


def main():
    """Render all palettes in a single tall figure."""
    n_palettes = len(PALETTES)
    row_h = 1.2  # inches per palette row
    title_h = 0.8
    fig = plt.figure(figsize=(9, title_h + n_palettes * row_h), dpi=200)

    # Title
    fig.text(0.5, 0.96, "Colour Palette Comparison",
             ha="center", va="top", fontsize=14, fontweight="bold",
             family="DejaVu Sans")

    for i, (name, colours) in enumerate(sorted(PALETTES.items())):
        y_pos = 1.0 - (title_h + (i + 1) * row_h) / fig.get_size_inches()[1]
        # Row label
        fig.text(0.04, y_pos + 0.03, f"{name}",
                 ha="left", va="center", fontsize=9, fontweight="bold")
        # Render swatch row
        ax = fig.add_axes([0.12, y_pos, 0.82, 0.05])
        n = len(colours)
        bar_w = 0.7 / n
        for j, role in enumerate(SEMANTIC_ROLES):
            x = j / n
            rect = Rectangle((x - bar_w/2 + 0.01, 0), bar_w * 0.95, 1,
                             facecolor=colours[role],
                             edgecolor="#cccccc",
                             linewidth=0.3)
            ax.add_patch(rect)
        ax.set_xlim(0, 0.72)
        ax.set_ylim(0, 1)
        ax.axis("off")

    # Output
    out_dir = "models/figures/outputs"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "colour_palette_comparison.png")
    plt.savefig(path, dpi=300, bbox_inches="tight",
                facecolor=fig.get_facecolor(), edgecolor="none")
    print(f"Wrote {path}")
    print(f"  Palettes: {', '.join(sorted(PALETTES.keys()))}")


if __name__ == "__main__":
    main()
