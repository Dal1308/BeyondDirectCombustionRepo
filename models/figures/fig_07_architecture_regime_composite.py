"""Fig. 7 Nature composite: architecture regime structure and sensitivity."""

import re
from pathlib import Path

from composite import Box, CompositeSpec, SvgPanel, export_composite, render_composite_svg


OUTPUT_DIR = Path(__file__).resolve().parent / "output"
FONT_SCALE = 1.22
PANEL_FONT_SCALE = {
    "fig07a": 1.0,
    "fig07b": 0.74,
    "fig07c": 0.74,
    "fig07d": 0.72,
}

SPEC = CompositeSpec(
    name="fig_07_architecture_regime_composite",
    heading="Architecture-space regime structure and parameter sensitivity",
    width_mm=183.0,
    height_mm=165.0,
    panels=(
        SvgPanel(
            path=OUTPUT_DIR / "fig_04a_efficiency_violin.svg",
            box=Box(7.0, 0.0, 84.0, 74.0),
            label="a",
            prefix="fig07a",
            strip_titles=("Effective efficiency distribution by fuel-flow regime — Layer 4 architecture-space sweep",),
        ),
        SvgPanel(
            path=OUTPUT_DIR / "fig_06b_regime_validity_contour.svg",
            box=Box(88.0, 0.0, 84.0, 74.0),
            label="b",
            prefix="fig07b",
            strip_titles=(r"R134a regime validity — 62% of $\eta_{\mathrm{engine}} \times UA$ space covered",),
        ),
        SvgPanel(
            path=OUTPUT_DIR / "fig_06a_parameter_forest_plot.svg",
            box=Box(7.0, 70.0, 84.0, 72.0),
            label="c",
            prefix="fig07c",
            strip_titles=("Parameter evidence ranges and literature anchors — Layer 4 model",),
        ),
        SvgPanel(
            path=OUTPUT_DIR / "fig_06c_sensitivity_bars.svg",
            box=Box(88.0, 70.0, 84.0, 72.0),
            label="d",
            prefix="fig07d",
            strip_titles=("Delivered-heat sensitivity — Layer 4 parameter bounds",),
        ),
    ),
)


def _panel_font_scale(svg_text: str, pos: int) -> float:
    panel_starts = [
        (svg_text.find(f"id=\"{prefix}_"), prefix)
        for prefix in PANEL_FONT_SCALE
        if svg_text.find(f"id=\"{prefix}_") != -1
    ]
    active_prefix = None
    for start, prefix in sorted(panel_starts):
        if start < pos:
            active_prefix = prefix
        else:
            break
    if active_prefix is None:
        return 1.0
    return PANEL_FONT_SCALE[active_prefix]


def _scale_svg_fonts(svg_text: str, scale: float) -> str:
    """Scale all font-size attributes in the rendered composite SVG."""

    def replace(match: re.Match[str]) -> str:
        tag_start = svg_text.rfind("<", 0, match.start())
        tag_end = svg_text.find(">", tag_start)
        if tag_start != -1 and tag_start < match.start() < tag_end:
            tag_text = svg_text[tag_start:tag_end]
            if 'class="panel-label"' in tag_text or 'class="composite-heading"' in tag_text:
                panel_scale = 1.0
            else:
                panel_scale = _panel_font_scale(svg_text, match.start())
            tag_name = svg_text[tag_start + 1 :].split(None, 1)[0].lstrip("/")
            if tag_name == "tspan":
                return match.group(0)
        else:
            panel_scale = _panel_font_scale(svg_text, match.start())
        value = float(match.group("value"))
        unit = match.group("unit") or ""
        return f"{match.group('prefix')}{value * scale * panel_scale:.3g}{unit}"

    return re.sub(
        r"(?P<prefix>font-size(?:\s*:\s*|\s*=\s*[\"']))"
        r"(?P<value>\d+(?:\.\d+)?)(?P<unit>px|pt)?",
        replace,
        svg_text,
    )


def _remove_composite_heading_and_labels(svg_text: str) -> str:
    """Remove the composite title and panel-letter labels for this figure."""
    svg_text = re.sub(r'\n?<text class="composite-heading"[^>]*>.*?</text>', "", svg_text)
    return re.sub(r'\n?<text class="panel-label"[^>]*>.*?</text>', "", svg_text)


def save_scaled_composite(spec: CompositeSpec, output_dir: Path) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    svg_path = output_dir / f"{spec.name}.svg"
    pdf_path = output_dir / f"{spec.name}.pdf"
    png_path = output_dir / f"{spec.name}.png"
    svg_text = _scale_svg_fonts(render_composite_svg(spec), FONT_SCALE)
    svg_path.write_text(_remove_composite_heading_and_labels(svg_text), encoding="utf-8")
    export_composite(svg_path, pdf_path, png_path)
    return pdf_path, svg_path, png_path


def main() -> None:
    save_scaled_composite(SPEC, OUTPUT_DIR)


if __name__ == "__main__":
    main()
