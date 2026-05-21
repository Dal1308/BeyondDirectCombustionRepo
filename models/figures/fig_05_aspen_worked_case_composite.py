"""Fig. 5 Nature composite: Aspen worked-case evidence."""

from pathlib import Path

from composite import Box, CompositeSpec, SvgPanel, save_composite


OUTPUT_DIR = Path(__file__).resolve().parent / "output"

SPEC = CompositeSpec(
    name="fig_05_aspen_worked_case_composite",
    heading="Worked-case evidence from Aspen simulation",
    width_mm=183.0,
    height_mm=91.0,
    panels=(
        SvgPanel(
            path=OUTPUT_DIR / "fig_05c_comparison_bars.svg",
            box=Box(5.0, 7.0, 84.0, 78.0),
            label="a",
            prefix="fig05a",
            strip_titles=(
                "Worked case delivers 199% of fuel input (condenser duty), far below the reversible benchmark",
            ),
        ),
        SvgPanel(
            path=OUTPUT_DIR / "fig_05d_waterfall.svg",
            box=Box(93.0, 7.0, 86.0, 78.0),
            label="b",
            prefix="fig05b",
            strip_titles=(
                "Energy build-up to delivered heat: 52% environmental + 48% work-converted",
            ),
        ),
    ),
)


def main() -> None:
    save_composite(SPEC, OUTPUT_DIR)


if __name__ == "__main__":
    main()
