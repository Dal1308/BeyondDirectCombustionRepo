"""Fig. 1 Nature composite: benchmark-led process concept."""

from pathlib import Path

from composite import Box, CompositeSpec, RasterPanel, SchematicPanel, save_composite


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
ASSET_DIR = ROOT / "assets" / "figures"

SPEC = CompositeSpec(
    name="fig_01_concept_composite",
    heading="Benchmark-led process concept",
    width_mm=183.0,
    height_mm=150.0,
    panels=(
        RasterPanel(
            path=ASSET_DIR / "OverallFlowsheet.PNG",
            box=Box(8.0, 6.0, 167.0, 83.0),
            label="a",
        ),
        SchematicPanel(
            box=Box(8.0, 95.0, 82.0, 48.0),
            label="b",
            heading="Benchmark logic",
            rows=(
                "chemical fuel reaction",
                "entropy-balance benchmark",
                "reversible heating between T_C and T_H",
                "maximum delivered heat",
            ),
        ),
        SchematicPanel(
            box=Box(93.0, 95.0, 82.0, 48.0),
            label="c",
            heading="Architecture-space logic",
            rows=(
                "methane fuel input",
                "fuel-derived work",
                "heat-upgrading block",
                "sink-side heat delivery",
            ),
            side_note="combustion-side remainder -> recoverable heat",
        ),
    ),
)


def main() -> None:
    save_composite(SPEC, OUTPUT_DIR)


if __name__ == "__main__":
    main()
