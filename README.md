# Beyond Direct Combustion: Code Repo

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20324897.svg)](https://doi.org/10.5281/zenodo.20324897)

Public reproducibility package for the manuscript **"Beyond direct combustion: a reversible benchmark for heat delivery from chemical fuels"**.

This repository contains the public model code, generated CSV outputs, rendered figure assets, and Aspen exported audit material for inspecting and reproducing the manuscript results.

## Quick Start

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .

./run.sh --dry-run
./run.sh --smoke-test
```

The smoke test checks that the public model layers import and that the expected generated CSVs and Aspen export artifacts are present and readable.

## What This Repository Reproduces

- **Layer 2 reversible benchmark**: theorem-derived upper-bound heat delivery from chemical fuels across source temperature, delivery temperature, and fuel identity.
- **Layer 4 Brayton heat-pump architecture-space support**: a bounded, semi-realistic R134a architecture-family model used to show how a specific implementation family occupies part of the reversible design space.
- **Rendered manuscript and supplementary figures**: public PNG, PDF, and SVG outputs under `figures/`, with generation scripts under `models/figures/`.
- **Aspen worked-case audit package**: exported CSV tables, reports, and flowsheet imagery for the methane Brayton heat-pump worked case.

## Repository Map

| Path                    | Contents                                                                          |
| ----------------------- | --------------------------------------------------------------------------------- |
| `models/independent/`   | Layer 2 reversible benchmark model and generated outputs.                         |
| `models/thermodynamic/` | Layer 4 thermodynamic support model outputs and Brayton architecture-space model. |
| `models/figures/`       | Figure scripts and composite-figure assembly utilities.                           |
| `data/`                 | Public mirrored CSV outputs and `data/manifest.csv`.                              |
| `figures/`              | Rendered public figure assets.                                                    |
| `assets/aspen/`         | Aspen exported audit PDFs, flowsheet image, and comparison CSVs.                  |
| `tests/smoke/`          | Public package integrity tests.                                                   |

## Running the Package

The public runner supports local-scale model reproduction, data refreshes, figure generation, and package checks.

```bash
./run.sh --model independent
./run.sh --model brayton
./run.sh --data
./run.sh --figures
./run.sh --smoke-test
```

`./run.sh` with no arguments runs the independent model, the local-scale Brayton analyses, refreshes public data mirrors, and runs the smoke tests.

Use `PYTHON=/path/to/python ./run.sh ...` if you want the runner to use a specific interpreter.

## Model Layers

### Layer 2: Reversible Benchmark

The independent model computes the thermodynamic ceiling:

```text
Q_H,max = |Delta G_reaction(T_C)| / eta_Carnot
eta_Carnot = 1 - T_C / T_H
```

Its main output is the dimensionless multiplier `Q_H,max / |Delta H|`. The model includes methane, syngas, carbon, hydrogen, and ammonia fuel-property definitions in `models/independent/core.py`.

Run it directly with:

```bash
python -c "from models.independent import run_model; run_model()"
```

Generated files:

- `models/independent/output/benchmark_surface.csv`
- `models/independent/output/temperature_sweep.csv`
- `models/independent/output/fuel_comparison.csv`

These files are mirrored in `data/independent/`.

### Layer 4: Brayton Heat-Pump Architecture Space

The Brayton architecture-space model is a bounded implementation-family model that couples methane fuel input to mechanical work and an R134a heat-pump cycle, with sink temperature emerging from the configured heat-transfer closure. It provides architecture-space support alongside the reversible benchmark.

Key files:

- `models/thermodynamic/brayton_heat_pump_architecture_space/system_config.yaml`
- `models/thermodynamic/brayton_heat_pump_architecture_space/core/physics_engine.py`
- `models/thermodynamic/brayton_heat_pump_architecture_space/core/refrigerant_properties.py`
- `models/thermodynamic/brayton_heat_pump_architecture_space/analysis/`

Run the local public analyses with:

```bash
./run.sh --model brayton
```

Generated files include:

- `multivariate_design_space.csv`
- `regime_validity_sweep.csv`
- `sensitivity_data.csv`
- `efficiency_distribution_high_res*.csv`
- `layer2_layer4_comparison.csv`
- `stress_test_results.csv`

These files are mirrored in `data/brayton_heat_pump_architecture_space/`.

## Data and Figures

`data/manifest.csv` maps public CSV files to their generated source paths and gives a short description of each dataset. The mirrored `data/` tree is the easiest place for downstream inspection; the corresponding `models/**/output/` folders are the generated source of record.

Rendered figures are stored in `figures/`. Figure scripts write to `models/figures/output/`; the public `figures/` directory contains the released copies. To regenerate available public figures:

```bash
./run.sh --figures
```

Some figure scripts consume Aspen exported CSVs, so keep `assets/aspen/export/` intact when regenerating figures.

## Aspen Audit Package

The Aspen audit package provides exported material for inspecting the worked-case boundary and key comparison quantities.

Included Aspen artifacts:

- `assets/aspen/ModelsMethaneHeatPumpPureBrayton.pdf`
- `assets/aspen/ResultsMethaneHeatPumpPureBrayton_A2.pdf`
- `assets/aspen/OverallFlowsheet.PNG`
- `assets/aspen/export/current_base_case_key_outputs.csv`
- `assets/aspen/export/base_case_comparison_aspen_vs_python.csv`
- `assets/aspen/export/aspen_comparator_calculations.csv`
- `assets/aspen/export/aspen_hybrid_figure_inputs.csv`

The public smoke test verifies that these exported audit files are present and non-empty.

## Interpretation

- The reversible benchmark is a thermodynamic upper bound for heat delivery from chemical fuels.
- The Brayton architecture-space model is an implementation-family support model with explicit validity labels; use `status` and `is_valid` fields when interpreting its outputs.
- The high-resolution CSVs included in the package are manuscript-preparation outputs. The public runner regenerates local-scale analyses by default.
- Aspen support is provided through exported tables, reports, and flowsheet imagery.

## Citation

This repository is archived on Zenodo:

- DOI: [10.5281/zenodo.20324897](https://doi.org/10.5281/zenodo.20324897)
- Source repository: <https://github.com/Dal1308/BeyondDirectCombustionRepo>

See `CITATION.cff` for citation metadata.

## License

This package is distributed under the GNU General Public License v3.0. See `LICENSE`.
