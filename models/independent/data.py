"""
models/independent/data.py

Data generation for benchmark-driven design space exploration.
No plotting, no matplotlib.

Exports:
    ensure_output_dir()          — create output directory
    save_dataframe()             — write DataFrame to CSV
    build_benchmark_surface()    — Q_H,max / |ΔH°| across T_C × T_H
    build_temperature_sweep()     — single-fuel benchmark curve
    build_fuel_comparison()       — cross-fuel benchmark comparison
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
from .core import thermodynamic_limit, heating_multiplier


def ensure_output_dir(base_dir: Path) -> Path:
    output_dir = base_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def save_dataframe(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False)


def cleanup_generated_outputs(output_dir: Path) -> None:
    """Remove all generated files from the output directory."""
    for pattern in ("*.png", "*.svg", "*.csv", "summary.txt"):
        for path in output_dir.glob(pattern):
            if path.is_file():
                path.unlink()


def build_benchmark_surface(
    props,  # MethaneProperties or similar — duck-typed
    t_cold_range: np.ndarray | None = None,
    t_hot_range: np.ndarray | None = None,
) -> pd.DataFrame:
    """
    Build a benchmark surface DataFrame: Q_H,max / |ΔH°| across T_C × T_H.

    This is the data for Fig. A — the universal theoretical ceiling plot.
    Each row is one (T_cold, T_hot) point with the heating multiplier.

    Default grid: 51 points for T_cold [243.15, 310.15] K (-30 to 37 °C),
                  51 points for T_hot  [283.15, 346.15] K (10 to 73 °C).
    Matches the Layer 4 architecture-space plot axes.
    """
    if t_cold_range is None:
        t_cold_range = np.linspace(243.15, 310.15, 51)
    if t_hot_range is None:
        t_hot_range = np.linspace(283.15, 346.15, 51)

    rows = []
    for t_cold in t_cold_range:
        for t_hot in t_hot_range:
            try:
                limit = thermodynamic_limit(props, t_cold, t_hot)
                multiplier = heating_multiplier(props, t_cold, t_hot)
                lift = t_hot - t_cold
                rows.append({
                    "t_cold_k":       t_cold,
                    "t_hot_k":        t_hot,
                    "temperature_lift":  lift,
                    "q_h_max_kj_per_mol": limit["q_h_max_kj_per_mol"],
                    "multiplier":     multiplier,
                    "eta_carnot":     limit["eta_carnot"],
                    "cop_carnot":     limit["cop_carnot"],
                })
            except ValueError:
                pass  # skip invalid temperature pairs

    return pd.DataFrame(rows)




def build_temperature_sweep(
    props,
    t_cold: float,
    t_hot_range: np.ndarray | None = None,
    n_points: int = 61,
) -> pd.DataFrame:
    """
    Single-fuel benchmark curve at fixed T_C, sweeping T_H.

    Useful for showing the multiplier vs temperature lift profile
    in a simple line plot.
    """
    if t_hot_range is None:
        t_hot_range = np.linspace(t_cold + 15.0, t_cold + 85.0, n_points)

    rows = []
    for t_hot in t_hot_range:
        multiplier = heating_multiplier(props, t_cold, t_hot)
        lift = t_hot - t_cold
        try:
            limit = thermodynamic_limit(props, t_cold, t_hot)
            q_h_max = limit["q_h_max_kj_per_mol"]
        except ValueError:
            continue
        rows.append({
            "t_cold_k":     t_cold,
            "t_hot_k":      t_hot,
            "temperature_lift": lift,
            "multiplier":   multiplier,
            "q_h_max_kj_per_mol": q_h_max,
        })

    return pd.DataFrame(rows)


def build_fuel_comparison(
    t_cold: float,
    t_hot: float,
) -> pd.DataFrame:
    """
    Compare benchmark multiplier across fuel types at fixed temperatures.

    Includes all 5 fuels from the property database: methane, hydrogen,
    ammonia, syngas, carbon.
    """
    from .core import get_fuel

    fuels = ["methane", "hydrogen", "ammonia", "syngas", "carbon"]
    rows = []
    for name in fuels:
        props = get_fuel(name)
        multiplier = heating_multiplier(props, t_cold, t_hot)
        try:
            limit = thermodynamic_limit(props, t_cold, t_hot)
        except ValueError:
            continue
        rows.append({
            "fuel":               name,
            "t_cold_k":           t_cold,
            "t_hot_k":            t_hot,
            "multiplier":         multiplier,
            "q_h_max_kj_per_mol": limit["q_h_max_kj_per_mol"],
            "|delta_h|":          abs(props.delta_h_kj_per_mol),
        })

    return pd.DataFrame(rows)
