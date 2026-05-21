"""
models/thermodynamic/brayton_heat_pump_architecture_space/analysis/generate_sensitivity_data.py

Generate sensitivity analysis data for Fig. 6(c).
Runs Brayton heat-pump architecture-space model with each parameter at low/high bounds, outputs CSV.

Usage: .venv/bin/python models/thermodynamic/brayton_heat_pump_architecture_space/analysis/generate_sensitivity_data.py
"""

import argparse
import csv
from pathlib import Path

from models.thermodynamic.brayton_heat_pump_architecture_space.core.physics_engine import PhysicsEngine
from models.thermodynamic.brayton_heat_pump_architecture_space.analysis.export_safety import (
    is_valid,
    require_valid,
    status_msg,
    status_value,
)

def main(full_run: bool = False):
    filename = "sensitivity_data_full_run.csv" if full_run else "sensitivity_data.csv"
    output_path = Path(__file__).resolve().parent.parent / "output" / filename
    
    engine = PhysicsEngine()
    fuel_flow = 1e-3  # kg/s
    t_source = 15.0   # C
    
    # Store baseline config
    baseline_config = {
        "eta_engine": engine.config["fuel"]["eta_engine"],
        "eta_iso": engine.config["heat_pump"]["eta_iso"],
        "recovery_effectiveness": engine.config["heat_pump"]["recovery_effectiveness"],
        "ua_condenser": engine.config["heat_pump"]["ua_condenser"],
    }
    
    # Baseline run
    audit_base = engine.perform_energy_audit(fuel_flow, t_source, mode="predictive")
    require_valid(audit_base, "Baseline sensitivity case")
    baseline_useful = audit_base['ledger']['total_useful_heat_out']
    
    print(f"Baseline delivered heat: {baseline_useful:.0f} W")
    
    # Parameters to test
    param_tests = [
        ("eta_engine", r"$\eta_{engine}$", "fuel", "eta_engine", 0.20, 0.40),
        ("eta_iso", r"$\eta_{iso}$", "heat_pump", "eta_iso", 0.70, 0.83),
        ("recovery_effectiveness", r"$f_{rec}$", "heat_pump", "recovery_effectiveness", 0.50, 0.75),
        ("ua_condenser", r"$UA_{cond}$", "heat_pump", "ua_condenser", 1300, 1800),
    ]
    
    results = []
    for key, label, section, config_key, low_val, high_val in param_tests:
        engine.config["fuel"]["eta_engine"] = baseline_config["eta_engine"]
        engine.config["heat_pump"]["eta_iso"] = baseline_config["eta_iso"]
        engine.config["heat_pump"]["recovery_effectiveness"] = baseline_config["recovery_effectiveness"]
        engine.config["heat_pump"]["ua_condenser"] = baseline_config["ua_condenser"]

        # Low bound
        engine.config[section][config_key] = low_val
        audit_low = engine.perform_energy_audit(fuel_flow, t_source, mode="predictive")
        if is_valid(audit_low):
            heat_low = audit_low['ledger']['total_useful_heat_out']
            pct_change_low = (heat_low - baseline_useful) / baseline_useful * 100
        else:
            pct_change_low = None
        
        # High bound
        engine.config["fuel"]["eta_engine"] = baseline_config["eta_engine"]
        engine.config["heat_pump"]["eta_iso"] = baseline_config["eta_iso"]
        engine.config["heat_pump"]["recovery_effectiveness"] = baseline_config["recovery_effectiveness"]
        engine.config["heat_pump"]["ua_condenser"] = baseline_config["ua_condenser"]
        engine.config[section][config_key] = high_val
        audit_high = engine.perform_energy_audit(fuel_flow, t_source, mode="predictive")
        if is_valid(audit_high):
            heat_high = audit_high['ledger']['total_useful_heat_out']
            pct_change_high = (heat_high - baseline_useful) / baseline_useful * 100
        else:
            pct_change_high = None
        
        results.append({
            "parameter": key,
            "label": label,
            "low_val": low_val,
            "high_val": high_val,
            "low_status": status_value(audit_low),
            "high_status": status_value(audit_high),
            "low_status_msg": status_msg(audit_low),
            "high_status_msg": status_msg(audit_high),
            "pct_change_low": pct_change_low,
            "pct_change_high": pct_change_high,
        })
        
        low_text = f"{pct_change_low:+.1f}%" if pct_change_low is not None else audit_low["status"].value
        high_text = f"{pct_change_high:+.1f}%" if pct_change_high is not None else audit_high["status"].value
        print(f"{label:20s}: low={low_text}, high={high_text}")
    
    # Restore baseline config
    engine.config["fuel"]["eta_engine"] = baseline_config["eta_engine"]
    engine.config["heat_pump"]["eta_iso"] = baseline_config["eta_iso"]
    engine.config["heat_pump"]["recovery_effectiveness"] = baseline_config["recovery_effectiveness"]
    engine.config["heat_pump"]["ua_condenser"] = baseline_config["ua_condenser"]
    
    # Write CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "parameter",
                "label",
                "low_val",
                "high_val",
                "low_status",
                "high_status",
                "low_status_msg",
                "high_status_msg",
                "pct_change_low",
                "pct_change_high",
            ],
        )
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\nSensitivity data written to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--full-run",
        action="store_true",
        help="Write the sensitivity output with a _full_run suffix.",
    )
    args = parser.parse_args()
    main(full_run=args.full_run)
