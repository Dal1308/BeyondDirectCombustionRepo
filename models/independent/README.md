# Reversible Benchmark Design-Space Model

This directory contains the Layer 2 model for the manuscript: a theorem-derived mapping of the reversible chemical-fuel heating benchmark across fuel and temperature space.

## Purpose
- Map `Q_H,max / |ΔH°|` across source temperature `T_C`, delivery temperature `T_H`, and fuel identity.
- Provide the reversible design-space context established by Supplementary Note 1.
- Generate benchmark-only datasets for manuscript and SI figures.

## Documentation Contract
- This model is theorem-derived; it is not a Brayton heat-pump model, an idealized engineering model, or a gas-savings calculator.
- Use `docs/planning/registry/claims.yaml`, `parameters.yaml`, and `outputs.yaml` for current project posture.
- Do not introduce turbine efficiency, heat-pump COP laws, exhaust recovery fractions, or practical-fraction calculations here.

## Modelling Basis
The model computes:
- `Q_H,max = |ΔG_reaction(T_C)| / η_Carnot`
- `η_Carnot = 1 - T_C / T_H`
- `Q_H,max / |ΔH_reaction|`

All outputs must be direct consequences of the Layer 1 benchmark derivation.

## Execution
Use the repo-local virtual environment and run as a module:

```bash
.venv/bin/python -m models.independent.independent_model
```

## Outputs
Running the script writes datasets and figures into `models/independent/output/`.
- `benchmark_surface.csv`
- `temperature_sweep.csv`
- `fuel_comparison.csv`
