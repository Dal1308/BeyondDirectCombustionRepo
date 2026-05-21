"""
models/figures — shared figure generation utilities for the manuscript.

Public entry points:
    from figures.config import current_palette as C          # colour dict
    from figures.config import STYLE_DEFAULTS                # mpl rcParams
    from figures.style      import apply_style               # one-liner rc update

Usage in any figure script:
    from models.figures.config import current_palette as C
    sns.barplot(..., color=C['work_path'])
    plt.rcParams.update(STYLE_DEFAULTS)
"""
