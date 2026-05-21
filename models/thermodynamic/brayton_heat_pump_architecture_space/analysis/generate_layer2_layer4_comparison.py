"""
Generate a safe Layer 2 / Layer 4 comparison table.

This output compares valid Brayton heat-pump architecture-space rows against
the Layer 2 reversible methane benchmark at matching source and emergent sink
temperatures. The primary numerator is the whole-system useful delivery:
heat-pump useful condenser delivery plus recovered exhaust heat.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from models.independent.core import get_fuel, heating_multiplier
from models.thermodynamic.brayton_heat_pump_architecture_space.analysis.export_safety import (
    is_valid,
    safe_metric_row,
)
from models.thermodynamic.brayton_heat_pump_architecture_space.core.physics_engine import PhysicsEngine


def build_comparison(engine: PhysicsEngine) -> pd.DataFrame:
    methane = get_fuel("methane")
    fuel_flows = np.linspace(0.5e-3, 1.6e-3, 12)
    t_sources = np.linspace(5.0, 25.0, 11)
    rows = []

    for fuel_flow in fuel_flows:
        for t_source_c in t_sources:
            audit = engine.perform_energy_audit(
                fuel_flow_kg_s=fuel_flow,
                t_source_c=t_source_c,
                mode="predictive",
            )

            ledger = audit["ledger"]
            metrics = audit["metrics"]
            input_lhv_w = ledger["input_methane_lhv"]

            values = {
                "fuel": "methane",
                "fuel_flow_kg_s": fuel_flow,
                "t_source_c": t_source_c,
                "t_source_k": t_source_c + 273.15,
                "t_sink_c": metrics["t_sink"],
                "t_sink_k": metrics["t_sink"] + 273.15,
                "input_lhv_w": input_lhv_w,
                "hp_useful_heat_w": ledger["hp_useful_heat"],
                "waste_heat_recovered_w": ledger["waste_heat_recovered"],
                "total_useful_heat_out_w": ledger["total_useful_heat_out"],
                "layer4_hp_only_multiplier": None,
                "layer4_total_multiplier": None,
                "layer2_reversible_multiplier": None,
                "layer4_hp_only_fraction_of_layer2": None,
                "layer4_total_fraction_of_layer2": None,
            }

            if is_valid(audit):
                layer2_multiplier = heating_multiplier(
                    methane,
                    values["t_source_k"],
                    values["t_sink_k"],
                )
                hp_only_multiplier = ledger["hp_useful_heat"] / input_lhv_w
                total_multiplier = ledger["total_useful_heat_out"] / input_lhv_w

                values.update({
                    "layer4_hp_only_multiplier": hp_only_multiplier,
                    "layer4_total_multiplier": total_multiplier,
                    "layer2_reversible_multiplier": layer2_multiplier,
                    "layer4_hp_only_fraction_of_layer2": hp_only_multiplier / layer2_multiplier,
                    "layer4_total_fraction_of_layer2": total_multiplier / layer2_multiplier,
                })

            rows.append(safe_metric_row(audit, values))

    return pd.DataFrame(rows)


def main(full_run: bool = False):
    output_dir = Path(__file__).resolve().parents[1] / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = "layer2_layer4_comparison_full_run.csv" if full_run else "layer2_layer4_comparison.csv"
    output_path = output_dir / filename

    df = build_comparison(PhysicsEngine())
    df.to_csv(output_path, index=False)

    valid_count = int((df["status"] == "valid").sum())
    print(f"Layer 2 / Layer 4 comparison written to {output_path}")
    print(f"Valid rows: {valid_count}/{len(df)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--full-run",
        action="store_true",
        help="Write the comparison output with a _full_run suffix.",
    )
    args = parser.parse_args()
    main(full_run=args.full_run)
