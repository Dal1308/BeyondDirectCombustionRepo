"""Fig. 6 Nature composite: architecture-space occupation."""

from pathlib import Path

from composite import Box, CompositeSpec, SvgPanel, save_composite


OUTPUT_DIR = Path(__file__).resolve().parent / "output"

SPEC = CompositeSpec(
    name="fig_06_architecture_occupation_composite",
    heading="Architecture-space occupation",
    width_mm=183.0,
    height_mm=91.0,
    panels=(
        SvgPanel(
            path=OUTPUT_DIR / "fig_04b_operational_envelope.svg",
            box=Box(4.0, 7.0, 86.0, 78.0),
            label="a",
            prefix="fig06a",
            strip_titles=("Thermodynamic operational envelope — Layer 4 R134a architecture sweep",),
        ),
        SvgPanel(
            path=OUTPUT_DIR / "fig_04c_regime_overlay.svg",
            box=Box(93.0, 7.0, 86.0, 78.0),
            label="b",
            prefix="fig06b",
            strip_titles=("Regime markers on reversible benchmark design map — Layer 4 R134a sweep",),
        ),
    ),
)


def main() -> None:
    save_composite(SPEC, OUTPUT_DIR)


if __name__ == "__main__":
    main()
