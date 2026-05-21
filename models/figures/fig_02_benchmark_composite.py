"""Fig. 2 Nature composite: reversible benchmark design space."""

from pathlib import Path

from composite import Box, CompositeSpec, SvgPanel, save_composite


OUTPUT_DIR = Path(__file__).resolve().parent / "output"

SPEC = CompositeSpec(
    name="fig_02_benchmark_composite",
    heading="Reversible benchmark design space",
    width_mm=183.0,
    height_mm=91.0,
    panels=(
        SvgPanel(
            path=OUTPUT_DIR / "fig_02b_benchmark_ceiling_surface.svg",
            box=Box(4.0, 7.0, 89.0, 78.0),
            label="a",
            prefix="fig02a",
            strip_titles=(
                "Reversible heating ceiling — methane",
                r"Reversible heating ceiling $Q_H^{\max}/|\Delta H^\circ_{\mathrm{rxn}}|$ (–)",
            ),
        ),
        SvgPanel(
            path=OUTPUT_DIR / "fig_02a_benchmark_bar_chart.svg",
            box=Box(96.0, 7.0, 83.0, 78.0),
            label="b",
            prefix="fig02b",
            strip_titles=("Reversible heating ceiling — 10°C source, 60°C sink",),
        ),
    ),
)


def main() -> None:
    save_composite(SPEC, OUTPUT_DIR)


if __name__ == "__main__":
    main()
