from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def test_import_public_model_layers():
    from models.independent import run_model  # noqa: F401
    from models.thermodynamic.brayton_heat_pump_architecture_space.core.physics_engine import PhysicsEngine

    assert PhysicsEngine is not None


def test_expected_public_outputs_exist_and_are_readable():
    expected = [
        ROOT / "models/independent/output/benchmark_surface.csv",
        ROOT / "models/independent/output/temperature_sweep.csv",
        ROOT / "models/independent/output/fuel_comparison.csv",
        ROOT / "models/thermodynamic/output/baseline_breakdown.csv",
        ROOT / "models/thermodynamic/output/brayton_heat_pump_architecture_space_case_summary.csv",
        ROOT / "models/thermodynamic/brayton_heat_pump_architecture_space/output/layer2_layer4_comparison.csv",
        ROOT / "models/thermodynamic/brayton_heat_pump_architecture_space/output/regime_validity_sweep.csv",
        ROOT / "models/thermodynamic/brayton_heat_pump_architecture_space/output/sensitivity_data.csv",
    ]
    for path in expected:
        assert path.exists(), path
        assert not pd.read_csv(path).empty, path


def test_aspen_export_package_is_present():
    expected = [
        ROOT / "assets/aspen/ModelsMethaneHeatPumpPureBrayton.pdf",
        ROOT / "assets/aspen/ResultsMethaneHeatPumpPureBrayton_A2.pdf",
        ROOT / "assets/aspen/export/current_base_case_key_outputs.csv",
        ROOT / "assets/aspen/export/base_case_comparison_aspen_vs_python.csv",
        ROOT / "assets/aspen/export/aspen_comparator_calculations.csv",
        ROOT / "assets/aspen/export/aspen_hybrid_figure_inputs.csv",
    ]
    for path in expected:
        assert path.exists(), path
        assert path.stat().st_size > 0, path


def test_forbidden_private_material_is_absent():
    forbidden = [
        "AGENTS.md",
        "docs/planning",
        "docs/archive",
        "docs/verification-records",
        "manuscripts",
        "papers",
        "inkscape",
        "models/thermodynamic/archive",
    ]
    for rel in forbidden:
        assert not (ROOT / rel).exists(), rel
