import numpy as np
import pandas as pd
import yaml
import os
import argparse
from pathlib import Path
from models.thermodynamic.brayton_heat_pump_architecture_space.core.physics_engine import PhysicsEngine
from models.thermodynamic.brayton_heat_pump_architecture_space.analysis.export_safety import safe_metric_row

def run_multivariate_study(config_path=None, 
                           output_dir=None,
                           full_run: bool = False):
    """
    Explores the interaction between multiple system parameters and emergent outputs.
    Focuses on: Fuel Flow (Load) vs Source Temperature -> Sink Temperature & Efficiency.
    """
    if config_path is None:
        config_path = Path(__file__).resolve().parents[1] / "system_config.yaml"
    else:
        config_path = Path(config_path)

    if output_dir is None:
        output_dir = Path(__file__).resolve().parents[1] / "output"
    else:
        output_dir = Path(output_dir)

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    engine = PhysicsEngine(str(config_path))
    
    # Define Parameter Grids
    # Fuel flow range: 0.5 mg/s to 2.0 mg/s (representative of load variation)
    fuel_flows = np.linspace(0.5e-3, 2.0e-3, 11) 
    # Source temperature range: 5C to 25C (seasonal variation)
    t_sources = np.linspace(5.0, 25.0, 11)
    
    results = []

    print(f"Running multivariate study: {len(fuel_flows)} fuel flows x {len(t_sources)} source temps...")

    for f_flow in fuel_flows:
        for t_src in t_sources:
            # Run the physics engine audit
            audit = engine.perform_energy_audit(fuel_flow_kg_s=f_flow, t_source_c=t_src, mode="predictive")
            
            results.append(safe_metric_row(audit, {
                'fuel_flow_kg_s': f_flow,
                't_source_c': t_src,
                't_sink_c': audit['metrics']['t_sink'],
                'eta_effective': audit['metrics']['eta_effective'],
                'cop_hp': audit['metrics']['cop_hp'],
                'q_total_out_w': audit['ledger']['total_useful_heat_out'],
            }))

    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    # Save to CSV for heatmap generation
    filename = "multivariate_design_space_full_run.csv" if full_run else "multivariate_design_space.csv"
    csv_path = output_dir / filename
    df.to_csv(csv_path, index=False)
    print(f"Results saved to {csv_path}")

    # Print a small summary of the emergent T_sink range
    print("\n--- Emergent Sink Temperature Summary ---")
    valid_df = df[df["status"] == "valid"]
    print(f"Min T_sink: {valid_df['t_sink_c'].min():.2f} C")
    print(f"Max T_sink: {valid_df['t_sink_c'].max():.2f} C")
    print(f"Avg Efficiency: {valid_df['eta_effective'].mean()*100:.2f}%")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--full-run",
        action="store_true",
        help="Write the multivariate design-space output with a _full_run suffix.",
    )
    args = parser.parse_args()
    run_multivariate_study(full_run=args.full_run)
