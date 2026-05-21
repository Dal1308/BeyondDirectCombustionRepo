"""
models/figures/config/palettes.py

Named colour palettes for Nature Chemical Engineering manuscript figures.
Each palette maps SEMANTIC_ROLES to hex colours so every figure script
uses the same visual language regardless of which palette is active.

Hot-swap: export FIGURE_PALETTE=nature  # or any key below
          then import from figures.config
"""

# ── Semantic roles (fixed — never change the keys) ─────────────────────────────
# These names are used consistently across all figure scripts.
# The mapping between role -> visual meaning is defined here and governed by
# `docs/planning/registry/outputs.yaml` for manuscript-facing figure use.

SEMANTIC_ROLES = [
    "cold",            # Ambient / low-temperature source (env. heat, ASHP lift)
    "mid",             # Work paths (turbine work, HP compression, conversion)
    "hot",             # Heat upgrade (condenser duty, useful heat out)
    "peak",            # Direct combustion / peak energy density
    "loss",            # System losses / irreversibility / dissipation
    "baseline_ref",    # Boiler baselines, 90%/100% reference lines
    "excluded",        # Flows outside reporting boundary
    "text_primary",    # Labels, titles, axis text
    "text_secondary",  # Tick labels, annotations
    "grid",            # Gridlines, subtle separators
    "background",      # Plot / panel background
]

# ── Palette definitions ───────────────────────────────────────────────────────

PALETTES = {

    # ═══════════════════════════════════════════════════════════════
    # energy_chain  ← Custom thermodynamic sequential palette
    # Thermodynamic cold → hot mapping, plus neutrals for structure
    # ═══════════════════════════════════════════════════════════════
    "energy_chain": {
        "cold":      "#3A0CA3",   # deep violet — ambient source
        "mid":       "#4361EE",   # electric blue  — work paths
        "hot":       "#F72585",   # magenta        — upgraded heat
        "peak":      "#FF9E00",   # amber          — direct combustion
        "loss":      "#E74C3C",   # red            — system losses
        "baseline_ref": "#9ca3af", # grey         — boiler/90%/100% lines
        "excluded":  "#e5e7eb",   # light grey     — outside boundary
        "text_primary":   "#1a1a2e",  # near-black
        "text_secondary": "#4b5563",  # medium grey
        "grid":        "#d1d5db",   # soft grey
        "background":  "#ffffff",   # pure white
    },

    # ═══════════════════════════════════════════════════════════════
    # nature  ← Alias for the Nature-recommended colour-blind-safe palette.
    # Kept so --palette nature does what a user naturally expects.
    # ═══════════════════════════════════════════════════════════════
    "nature": {
        "cold":      "#0072B2",   # blue       — ambient source
        "mid":       "#E69F00",   # orange     — work paths
        "hot":       "#009E73",   # bluish green — upgraded heat
        "peak":      "#CC79A7",   # reddish purple — direct combustion
        "loss":      "#D55E00",   # vermilion  — system losses
        "baseline_ref": "#989898", # grey     — boiler/90%/100% lines
        "excluded":  "#f2f2f2",   # very light
        "text_primary":   "#212121",
        "text_secondary": "#555555",
        "grid":        "#cccccc",
        "background":  "#ffffff",
    },

    # ═══════════════════════════════════════════════════════════════
    # ncr  ← Default Nature-recommended colour-blind-safe palette
    # Uses the Okabe-Ito / Colour Universal Design colours listed in the
    # Nature research figure guide as an accessible example palette.
    # ═══════════════════════════════════════════════════════════════
    "ncr": {
        "cold":      "#0072B2",   # blue       — ambient source
        "mid":       "#E69F00",   # orange     — work paths (colorblind-safe)
        "hot":       "#009E73",   # green      — upgraded heat
        "peak":      "#CC79A7",   # reddish purple — direct combustion
        "loss":      "#D55E00",   # vermilion  — system losses (colorblind-safe)
        "baseline_ref": "#989898", # grey     — boiler/90%/100% lines
        "excluded":  "#f2f2f2",   # very light
        "text_primary":   "#212121",
        "text_secondary": "#555555",
        "grid":        "#cccccc",
        "background":  "#ffffff",
    },

    # ═══════════════════════════════════════════════════════════════
    # archival  ← Black & white only (print review, grayscale output)
    # Uses shades of grey — distinguishable when printed without colour
    # ═══════════════════════════════════════════════════════════════
    "archival": {
        "cold":      "#999999",   # light grey   — ambient source
        "mid":       "#555555",   # medium dark  — work paths
        "hot":       "#333333",   # dark         — upgraded heat
        "peak":      "#111111",   # near-black   — direct combustion
        "loss":      "#777777",   # medium grey  — system losses (distinguishable by hatch pattern)
        "baseline_ref": "#bbbbbb",  # pale grey
        "excluded":  "#f0f0f0",
        "text_primary":   "#000000",
        "text_secondary": "#333333",
        "grid":        "#eeeeee",
        "background":  "#ffffff",
    },

}
