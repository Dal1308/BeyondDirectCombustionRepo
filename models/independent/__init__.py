"""
models/independent — reversible benchmark design-space model

This module implements the reversible thermodynamic benchmark (SI Note 1)
as a computational tool: how does Q_H,max / |ΔH°| vary across fuels,
temperatures, and temperature lift conditions?

It is NOT a Brayton heat-pump model, an idealized engineering model, or a
gas-savings calculator. Those architecture-specific questions belong to
Layer 3 (Aspen worked case) and Layer 4 (Brayton heat-pump architecture-space
model). Layer 2's sole purpose is to map the theorem-derived reversible
ceiling.

Usage:
    from models.independent import run_model
    results = run_model()         # returns dict of DataFrames

Or import individual functions:
    from models.independent.core import thermodynamic_limit, heating_multiplier
    from models.independent.data import build_benchmark_surface
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path

from .core import (
    get_fuel,
    MethaneProperties,
    thermodynamic_limit,
    heating_multiplier,
)
from .data import (
    ensure_output_dir,
    save_dataframe,
    cleanup_generated_outputs,
    build_benchmark_surface,
    build_temperature_sweep,
    build_fuel_comparison,
)


def run_model(
    base_dir: Path | None = None,
    t_cold_range: tuple[float, float] | None = None,
    t_hot_range: tuple[float, float] | None = None,
    fuel_name: str = "methane",
) -> dict[str, object]:
    """
    Full Layer 2 run: generate theorem-derived benchmark data.

    Parameters
    ----------
    base_dir : Path, optional
        Directory containing this package (defaults to this file's parent).
    t_cold_range : tuple[float, float], optional
        (min, max) K for ambient source temperature sweep.
    t_hot_range : tuple[float, float], optional
        (min, max) K for delivery sink temperature sweep.
    fuel_name : str, optional
        Fuel to sweep (default: "methane"). One of: methane, hydrogen,
        ammonia, syngas, carbon.

    Returns
    -------
    dict[str, DataFrame]
        Keys: 'benchmark_surface', 'temperature_sweep', 'fuel_comparison'
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent

    props = get_fuel(fuel_name)

    output_dir = ensure_output_dir(base_dir)
    cleanup_generated_outputs(output_dir)

    # Set default ranges. Match Layer 4 architecture-space axes:
    #   T_cold: -30 to 37 °C (full source range)
    #   T_hot:  10 to 80 °C (covers all High-Flow valid cases + margin)
    tc_min, tc_max = t_cold_range or (243.15, 310.15)
    th_min, th_max = t_hot_range or (283.15, 353.15)

    tc_range = np.linspace(tc_min, tc_max, 51)
    th_range = np.linspace(th_min, th_max, 51)

    # Build data
    benchmark_surface = build_benchmark_surface(props, tc_range, th_range)
    temp_sweep = build_temperature_sweep(props, 283.0, np.linspace(313.0, 423.0, 61))
    fuel_comparison = build_fuel_comparison(298.0, 333.0)

    # Save CSVs
    for name, df in {
        "benchmark_surface": benchmark_surface,
        "temperature_sweep": temp_sweep,
        "fuel_comparison": fuel_comparison,
    }.items():
        save_dataframe(df, output_dir / f"{name}.csv")

    print(f"Wrote analysis outputs to {output_dir}")

    return {
        "benchmark_surface": benchmark_surface,
        "temperature_sweep": temp_sweep,
        "fuel_comparison": fuel_comparison,
    }


# ── Re-export public symbols for convenience ───────────────────────────────

__all__ = [
    "run_model",
    "MethaneProperties",
    "thermodynamic_limit",
    "heating_multiplier",
    "build_benchmark_surface",
    "build_temperature_sweep",
    "build_fuel_comparison",
]
