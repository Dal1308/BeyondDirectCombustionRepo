"""
models/thermodynamic/brayton_heat_pump_architecture_space/analysis/generate_regime_validity_sweep.py

Generates a sweep grid of η_engine × UA_condenser to map R134a regime validity.
Records whether each combination produces valid or out-of-envelope operation.

Output: CSV with columns
    eta_engine, ua_condenser, t_sink_c, status, is_valid, status_msg,
    q_total_out_w
"""

import argparse
from pathlib import Path

from models.thermodynamic.brayton_heat_pump_architecture_space.core.physics_engine import PhysicsEngine
from models.thermodynamic.brayton_heat_pump_architecture_space.analysis.export_safety import safe_metric_row

def main(full_run: bool = False):
    engine = PhysicsEngine()

    # ── Sweep grid ───────────────────────────────────────────────────────────
    eta_engine_values = [0.20, 0.25, 0.30, 0.35, 0.40]
    ua_values = [800, 1000, 1200, 1530, 1800, 2000, 2500, 3000]

    results = []

    for eta in eta_engine_values:
        for ua in ua_values:
            # Override parameters
            engine.config['fuel']['eta_engine'] = eta
            engine.config['heat_pump']['ua_condenser'] = ua

            audit = engine.perform_energy_audit(fuel_flow_kg_s=1e-3, t_source_c=15.0, mode="predictive")

            results.append(safe_metric_row(audit, {
                "eta_engine": eta,
                "ua_condenser": ua,
                "t_sink_c": audit["metrics"]["t_sink"],
                "q_total_out_w": audit["ledger"]["total_useful_heat_out"],
            }))

    # ── Save CSV ─────────────────────────────────────────────────────────────
    filename = "regime_validity_sweep_full_run.csv" if full_run else "regime_validity_sweep.csv"
    output_path = Path(__file__).resolve().parent.parent / "output" / filename
    import csv
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "status",
                "is_valid",
                "status_msg",
                "eta_engine",
                "ua_condenser",
                "t_sink_c",
                "q_total_out_w",
            ],
        )
        writer.writeheader()
        writer.writerows(results)

    print(f"Sweep saved to {output_path}")
    print(f"Total points: {len(results)}")

    # ── Summary ──────────────────────────────────────────────────────────────
    valid_count = sum(1 for r in results if r["status"] == "valid")
    invalid_count = len(results) - valid_count
    print(f"Valid: {valid_count}/{len(results)} ({valid_count/len(results)*100:.0f}%)")
    print(f"Out-of-envelope: {invalid_count}/{len(results)} ({invalid_count/len(results)*100:.0f}%)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--full-run",
        action="store_true",
        help="Write the regime-validity output with a _full_run suffix.",
    )
    args = parser.parse_args()
    main(full_run=args.full_run)
