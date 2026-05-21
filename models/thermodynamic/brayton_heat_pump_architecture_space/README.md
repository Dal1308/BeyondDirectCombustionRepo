# Brayton Heat-Pump Architecture-Space Model

## Overview
The **Brayton heat-pump architecture-space model** is the Layer 4 Python model for the project.

Its intended role is semi-realistic architecture-family exploration: it should show what subset of the Layer 2 reversible benchmark design space a Brayton heat-pump architecture can occupy. It is not an Aspen surrogate, and it is not currently promoted to final manuscript or figure evidence.

System performance and output temperatures are not "set" by the user; they **emerge** from the interaction of real-gas thermodynamics (via CoolProp) and heat transfer physics.

This model is currently **figure-promotion blocked**. The Layer 4 planning audit has been executed once, output safety has been repaired at the analysis-export level, and a candidate Layer 2/Layer 4 comparison CSV exists. No rendered Layer 4 figure is promoted yet.

## Documentation Contract
- Canonical parameter and output status lives in:
  - `docs/planning/registry/parameters.yaml`
  - `docs/planning/registry/outputs.yaml`
- Treat current outputs as audit inputs or quarantined exploratory outputs unless the registries explicitly promote them further after the Layer 4 audit.
- Do not use this README as a separate status tracker for parameter verification or manuscript readiness.

## Current Handoff Snapshot
- The former Layer 4 planning dossier was archived during documentation reduction; use registry rows and required records for current promotion status.
- Safe generated exports live in `models/thermodynamic/brayton_heat_pump_architecture_space/output/`.
- `data/manifest.csv` records the data-package mapping; `data/brayton_heat_pump_architecture_space/` now provides the manifest-driven consolidated symlink view.
- The selected next figure strategy is one compact Layer 2/Layer 4 comparison panel based on `layer2_layer4_comparison.csv`.
- The approved comparison basis is predictive mode, methane basis, source/sink matched, `status == valid` rows only, normalized to the Layer 2 reversible ceiling.

## Output Safety Contract
- The core engine may return full diagnostic ledgers for `valid`, `out_of_envelope`, and `invalid` cases.
- Analysis CSVs must not export performance quantities for non-valid cases.
- Non-valid rows may appear in regime/validity datasets, but `t_sink_c`, `eta_effective`, `cop_hp`, `q_total_out_w`, and sensitivity percentage fields must be null unless the row is valid.
- Valid-only exports that filter rejected cases must provide denominator accounting in a companion summary file.
- Figure scripts should consume safe analysis CSVs, not raw engine ledgers. Prefer the consolidated `data/brayton_heat_pump_architecture_space/` symlink view for consumer code; use `models/thermodynamic/brayton_heat_pump_architecture_space/output/` as the generated source of record.

## 1. Core Philosophy: The "No-Guessing" Rule
To prevent the model from reverting to arbitrary multipliers or "work factors," it adheres to a strict physical flow:
**Fuel Input $\rightarrow$ Mechanical Work $\rightarrow$ Refrigerant Flow $\rightarrow$ Emergent Temperature.**

If the system efficiency is low, it is because the physics (e.g., low $UA$, low source temperature, or compressor irreversibilities) dictate it, not because of a tuning constant.

## 2. Physical Architecture

### A. The Coupled Cycles
The system consists of two coupled thermodynamic cycles:
1.  **Brayton Cycle (Turbine)**: Converts the chemical energy of methane into mechanical work ($W_{turbine}$) and waste heat.
2.  **Vapor Compression Cycle (Heat Pump)**: Uses $W_{turbine}$ to lift heat from a source ($T_{source}$) to a sink ($T_{sink}$).

### B. The Heat Pump Logic (4-State Cycle)
The model implements a full thermodynamic cycle using `CoolProp` for R134a properties:
*   **State 1 (Evaporator Exit)**: Saturated vapor at $T_{source}$. Determines $P_{evap}$ and enthalpy $h_1$.
*   **State 2 (Compressor Exit)**: Isentropic compression from $P_{evap}$ to $P_{cond}$. The actual enthalpy $h_2$ is calculated using the isentropic efficiency $\eta_{iso}$:
    $$h_2 = h_1 + \frac{h_{2,is} - h_1}{\eta_{iso}}$$
*   **State 3 (Condenser Exit)**: Saturated liquid at $T_{sink}$. Determines $P_{cond}$ and enthalpy $h_3$.
*   **State 4 (Expansion Valve Exit)**: Isenthalpic expansion ($h_4 = h_3$).

### C. The Sink-Side Closure
The active Brayton heat-pump architecture-space model now supports two explicit operating modes:

*   **Predictive mode (default)**: the model solves an emergent sink temperature from the useful sink-transfer closure
    $$Q_{cond} = UA(T_{sink} - T_{ref})$$
*   **Feasibility mode**: the user specifies a requested useful load, which is converted into a required sink temperature and checked against the available condenser duty.

In predictive mode:
*   **$Q_{cond}$**: Total heat rejected by the refrigerant ($\dot{m}_{ref} \times (h_2 - h_3)$).
*   **$UA(T_{sink} - T_{ref})$**: Useful sink-side heat-transfer closure anchored to the repo's `10 C -> 60 C` external-duty framing.

In feasibility mode:
*   **$Q_{useful,requested}$**: Requested useful sink-side load.
*   **$Q_{useful,available}$**: Available useful condenser heat at the required sink temperature.
*   **`unmet_useful_load`**: Any shortfall between requested and available useful heat.

## 3. Technical Implementation

### Key Files
- `core/`: Contains the central engine logic.
  - `physics_engine.py`: The core solver. Implements the iterative loop for $T_{sink}$ and the energy audit ledger.
  - `refrigerant_properties.py`: A wrapper for `CoolProp` to ensure consistent property calls (Pressure, Enthalpy, Entropy).
- `analysis/`: Contains multivariate studies and visualization.
  - `analyze_efficiency.py`: Standard efficiency analysis.
  - `export_safety.py`: Shared helpers that prevent non-valid rows from exporting performance evidence.
  - `generate_layer2_layer4_comparison.py`: Builds the candidate methane-basis Layer 2/Layer 4 comparison package.
  - `generate_regime_validity_sweep.py`: Builds the labelled `eta_engine x UA` validity map.
  - `generate_sensitivity_data.py`: Builds the local parameter sensitivity table with bound-level validity metadata.
  - `multivariate_analysis.py`: Explores the design space across load and temperature ranges.
- `tests/`: Contains the verification and audit suite.
  - `alignment_audit.py`: Verifies role boundaries, ledger checks, and physical admissibility.
  - `stress_test.py`: Stress tests the iterative solver at extreme boundaries.
  - `test_robustness.py`, `test_solver_stability.py`, `verify_balance_model.py`.
- `utils/`:
  - `export_planning_outputs.py`: Utilities for outputting model data for planning/documentation.

### The Energy Ledger
Every Joule is tracked in the `perform_energy_audit` method.

Predictive-mode ledger:
$$Q_{cond,gross} = Q_{sink,transfer} = Q_{useful}$$
$$\eta_{effective} = \frac{Q_{useful} + Q_{waste\_recovery}}{\dot{m}_{fuel} \times LHV}$$

The audit ledger therefore distinguishes:
- gross condenser duty (`hp_condenser_heat_gross`)
- useful sink-side heat transfer (`sink_heat_transfer`)
- useful condenser delivery (`hp_useful_heat`)
- total useful heat delivered by the current system boundary (`total_useful_heat_out`)
- requested / available / unmet useful heat in feasibility mode

## 4. Verification & Sanity Testing
The model should be treated as an internal architecture-space audit target. These checks are sanity and audit tools for bounded use, not proof of Aspen equivalence, equipment-level validation, or final figure readiness.

Current verification posture:
- the active planning layer now treats compressor efficiency as a bounded supported row and the condenser `UA` as an explicit internal closure parameter
- CSV outputs are safe only with their labels and status fields; rendered figures remain blocked until rebuilt scripts pass figure-level tests and registry review

### A. Physical Behavior Sanity Suite
| Question                                              | Expected Physical Behavior                               | Status   |
| :---------------------------------------------------- | :------------------------------------------------------- | :------- |
| If $UA$ increases, what happens to $T_{sink}$?        | $T_{sink}$ should decrease for the same condenser duty.  | Verified |
| If imposed useful load increases in feasibility mode, what happens to $T_{sink}$? | $T_{sink}$ should increase because more useful transfer is requested. | Verified |
| If $T_{source}$ drops, what happens to COP?           | COP should decrease (harder lift).                       | Verified |

### B. Audit Toolset
Use the following scripts to probe behaviour and audit the current model state:
- `alignment_audit.py`: Verifies role boundaries, ledger checks, and physical admissibility.
- `stress_test.py`: Stress tests the iterative solver at extreme boundaries.
- `multivariate_analysis.py`: Explores the design space across load and temperature ranges.
- `generate_layer2_layer4_comparison.py`: Generates the current candidate comparison output for the selected Option A figure.
- `generate_regime_validity_sweep.py`: Generates validity/regime support intended for SI-level documentation.

### C. Stability Results
The iterative $T_{sink}$ solver has shown useful behaviour in nominal and moderate exploratory cases, but edge-case audit results still need to be interpreted carefully. Numerical convergence should not be treated as proof of physical admissibility near or above the refrigerant critical region.

### D. Operating Envelope
For manuscript use, interpret the model within a liquid-water sink regime:
- manuscript-facing sink outputs are intended to stay within approximately `0-100 C`
- outputs above `100 C` indicate that the tested point has left the intended central-heating operating envelope
- such points can still be useful as boundary markers, but they should not be written up as practical water-heating predictions

## 5. Usage
To run a system audit:
```python
from physics_engine import PhysicsEngine
engine = PhysicsEngine()
audit = engine.perform_energy_audit(fuel_flow_kg_s=1e-3, t_source_c=15.0)
print(audit['metrics']['t_sink'])
```

To run an explicit load-feasibility audit:
```python
from physics_engine import PhysicsEngine
engine = PhysicsEngine()
audit = engine.perform_energy_audit(
    fuel_flow_kg_s=1e-3,
    t_source_c=15.0,
    q_useful_load_w=30000,
    mode="feasibility",
)
print(audit['ledger']['available_useful_heat'])
```

To run the current alignment audit:
```bash
.venv/bin/python -m pytest tests/thermodynamic/brayton_heat_pump_architecture_space -v
```
