"""Utilities for manuscript composite figures.

The composite layer keeps individual panels available for debugging/SI reuse
while producing one Nature-sized vector file per main-text figure.
"""

from __future__ import annotations

import base64
import html
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import cairosvg
from PIL import Image


from models.figures.config.font_config import COMPOSITE as _COMP_FONTS

PT_PER_MM = 72.0 / 25.4
NATURE_DOUBLE_COLUMN_MM = 183.0
NATURE_MAX_HEIGHT_MM = 170.0
PANEL_LABEL_SIZE_PT = _COMP_FONTS["panel_label"]
COMPOSITE_HEADING_SIZE_PT = _COMP_FONTS["heading"]
FIGURE_TEXT_MIN_PT = _COMP_FONTS["text_min"]
FIGURE_TEXT_MAX_PT = _COMP_FONTS["text_max"]
FONT_STACK = "Arial, Helvetica, DejaVu Sans, sans-serif"
INK = "#212121"
MUTED = "#555555"
PANEL_STROKE = "#d6d6d6"
BACKGROUND = "#ffffff"
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"


def mm_to_inches(mm: float) -> float:
    """Convert millimetres to inches."""
    return mm / 25.4


def mm_to_pt(mm: float) -> float:
    """Convert millimetres to SVG/PDF points."""
    return mm * PT_PER_MM


@dataclass(frozen=True)
class Box:
    """A panel slot in millimetres."""

    x: float
    y: float
    width: float
    height: float

    @property
    def pt(self) -> tuple[float, float, float, float]:
        return (mm_to_pt(self.x), mm_to_pt(self.y), mm_to_pt(self.width), mm_to_pt(self.height))


@dataclass(frozen=True)
class SvgPanel:
    path: Path
    box: Box
    label: str
    prefix: str
    strip_titles: tuple[str, ...] = ()


@dataclass(frozen=True)
class RasterPanel:
    path: Path
    box: Box
    label: str


@dataclass(frozen=True)
class SchematicPanel:
    box: Box
    label: str
    heading: str
    rows: tuple[str, ...]
    side_note: str | None = None


CompositePanel = SvgPanel | RasterPanel | SchematicPanel


@dataclass(frozen=True)
class CompositeSpec:
    name: str
    heading: str
    width_mm: float
    height_mm: float
    panels: tuple[CompositePanel, ...]

    @property
    def labels(self) -> tuple[str, ...]:
        return tuple(panel.label for panel in self.panels)


def add_panel_label(label: str, x_pt: float, y_pt: float) -> str:
    """Return a Nature-style lowercase panel label."""
    return (
        f'<text class="panel-label" x="{x_pt:.3f}" y="{y_pt:.3f}" '
        f'font-family="{FONT_STACK}" font-size="{PANEL_LABEL_SIZE_PT:.1f}" '
        f'font-weight="700" fill="{INK}">{html.escape(label)}</text>'
    )


def add_composite_heading(heading: str, width_pt: float) -> str:
    return (
        f'<text class="composite-heading" x="{width_pt / 2.0:.3f}" y="{mm_to_pt(3.8):.3f}" '
        f'text-anchor="middle" font-family="{FONT_STACK}" '
        f'font-size="{COMPOSITE_HEADING_SIZE_PT:.1f}" font-weight="700" '
        f'fill="{INK}">{html.escape(heading)}</text>'
    )


def _extract_svg_body(svg_text: str) -> tuple[str, float, float]:
    viewbox_match = re.search(r'viewBox="([^"]+)"', svg_text)
    if not viewbox_match:
        width_match = re.search(r'width="([\d.]+)pt"', svg_text)
        height_match = re.search(r'height="([\d.]+)pt"', svg_text)
        if not width_match or not height_match:
            raise ValueError("SVG panel has no viewBox or point width/height")
        width = float(width_match.group(1))
        height = float(height_match.group(1))
    else:
        values = [float(value) for value in viewbox_match.group(1).replace(",", " ").split()]
        if len(values) != 4:
            raise ValueError(f"Unsupported SVG viewBox: {viewbox_match.group(1)}")
        width = values[2]
        height = values[3]

    body_match = re.search(r"<svg\b[^>]*>(.*)</svg>\s*$", svg_text, flags=re.DOTALL)
    if not body_match:
        raise ValueError("Could not extract SVG body")
    body = body_match.group(1)
    body = re.sub(r"<metadata>.*?</metadata>", "", body, flags=re.DOTALL)
    return body, width, height


def _prefix_svg_ids(svg_body: str, prefix: str) -> str:
    svg_body = re.sub(r'\bid="([^"]+)"', rf'id="{prefix}_\1"', svg_body)
    svg_body = re.sub(r"url\(#([^)]+)\)", rf"url(#{prefix}_\1)", svg_body)
    svg_body = re.sub(r'\bxlink:href="#([^"]+)"', rf'xlink:href="#{prefix}_\1"', svg_body)
    svg_body = re.sub(r'(?<!:)\bhref="#([^"]+)"', rf'href="#{prefix}_\1"', svg_body)
    return svg_body


def _strip_title_groups(svg_body: str, titles: Sequence[str]) -> str:
    """Remove exact-title text groups from Matplotlib SVG panels."""
    for title in titles:
        escaped = re.escape(title)
        svg_body = re.sub(
            rf'\s*<g id="text_[^"]+">\s*<!-- {escaped} -->\s*<g\b.*?</g>\s*</g>\s*',
            "\n",
            svg_body,
            flags=re.DOTALL,
        )
        svg_body = re.sub(
            rf'\s*<g id="text_[^"]+">\s*<!-- {escaped} -->.*?</g>\s*',
            "\n",
            svg_body,
            flags=re.DOTALL,
        )
        svg_body = re.sub(
            rf'\s*<text\b[^>]*>\s*{escaped}\s*</text>\s*',
            "\n",
            svg_body,
            flags=re.DOTALL,
        )
    return svg_body


def _place_inner(width: float, height: float, box: Box) -> tuple[float, float, float]:
    x_pt, y_pt, w_pt, h_pt = box.pt
    scale = min(w_pt / width, h_pt / height)
    dx = (w_pt - width * scale) / 2.0
    dy = (h_pt - height * scale) / 2.0
    return x_pt + dx, y_pt + dy, scale


def _render_svg_panel(panel: SvgPanel) -> str:
    svg_text = panel.path.read_text(encoding="utf-8")
    body, width, height = _extract_svg_body(svg_text)
    body = _strip_title_groups(body, panel.strip_titles)
    body = _prefix_svg_ids(body, panel.prefix)
    x_pt, y_pt, scale = _place_inner(width, height, panel.box)
    box_x, box_y, _, _ = panel.box.pt
    return "\n".join(
        [
            add_panel_label(panel.label, box_x, box_y + PANEL_LABEL_SIZE_PT),
            f'<g transform="translate({x_pt:.3f} {y_pt:.3f}) scale({scale:.6f})">',
            body,
            "</g>",
        ]
    )


def _render_raster_panel(panel: RasterPanel) -> str:
    image_bytes = panel.path.read_bytes()
    encoded = base64.b64encode(image_bytes).decode("ascii")
    with Image.open(panel.path) as image:
        width, height = image.size
    x_pt, y_pt, scale = _place_inner(float(width), float(height), panel.box)
    box_x, box_y, _, _ = panel.box.pt
    rendered_width = width * scale
    rendered_height = height * scale
    return "\n".join(
        [
            add_panel_label(panel.label, box_x, box_y + PANEL_LABEL_SIZE_PT),
            f'<image x="{x_pt:.3f}" y="{y_pt:.3f}" width="{rendered_width:.3f}" '
            f'height="{rendered_height:.3f}" preserveAspectRatio="xMidYMid meet" '
            f'href="data:image/png;base64,{encoded}" />',
        ]
    )


def _text_line(text: str, x_pt: float, y_pt: float, size: float = 6.2, weight: int = 400) -> str:
    return (
        f'<text x="{x_pt:.3f}" y="{y_pt:.3f}" text-anchor="middle" '
        f'font-family="{FONT_STACK}" font-size="{size:.1f}" '
        f'font-weight="{weight}" fill="{INK}">{html.escape(text)}</text>'
    )


def _render_schematic_panel(panel: SchematicPanel) -> str:
    x, y, w, h = panel.box.pt
    cx = x + w / 2.0
    top = y + mm_to_pt(7.0)
    line_gap = mm_to_pt(6.7)
    parts = [
        add_panel_label(panel.label, x, y + PANEL_LABEL_SIZE_PT),
        f'<rect x="{x + mm_to_pt(4):.3f}" y="{y + mm_to_pt(3):.3f}" '
        f'width="{w - mm_to_pt(8):.3f}" height="{h - mm_to_pt(6):.3f}" '
        f'rx="{mm_to_pt(1.2):.3f}" fill="{BACKGROUND}" stroke="{PANEL_STROKE}" stroke-width="0.8" />',
        _text_line(panel.heading, cx, top, size=6.8, weight=700),
    ]
    y_cursor = top + mm_to_pt(8.0)
    for idx, row in enumerate(panel.rows):
        parts.append(_text_line(row, cx, y_cursor, size=6.0))
        if idx != len(panel.rows) - 1:
            parts.append(_text_line("↓", cx, y_cursor + mm_to_pt(4.3), size=6.8, weight=700))
            y_cursor += line_gap
    if panel.side_note:
        _sn_size = _COMP_FONTS["text_min"]
        parts.append(
            f'<text x="{cx:.3f}" y="{y + h - mm_to_pt(6.0):.3f}" text-anchor="middle" '
            f'font-family="{FONT_STACK}" font-size="{_sn_size:.1f}" fill="{MUTED}">'
            f'{html.escape(panel.side_note)}</text>'
        )
    return "\n".join(parts)


def render_composite_svg(spec: CompositeSpec) -> str:
    """Render a complete composite SVG document."""
    if spec.width_mm > NATURE_DOUBLE_COLUMN_MM or spec.height_mm > NATURE_MAX_HEIGHT_MM:
        raise ValueError(f"{spec.name} exceeds Nature size limits")
    width_pt = mm_to_pt(spec.width_mm)
    height_pt = mm_to_pt(spec.height_mm)
    bodies = []
    for panel in spec.panels:
        if isinstance(panel, SvgPanel):
            bodies.append(_render_svg_panel(panel))
        elif isinstance(panel, RasterPanel):
            bodies.append(_render_raster_panel(panel))
        elif isinstance(panel, SchematicPanel):
            bodies.append(_render_schematic_panel(panel))
        else:
            raise TypeError(f"Unsupported panel type: {type(panel)!r}")
    return "\n".join(
        [
            '<?xml version="1.0" encoding="utf-8" standalone="no"?>',
            f'<svg xmlns="{SVG_NS}" xmlns:xlink="{XLINK_NS}" width="{width_pt:.3f}pt" '
            f'height="{height_pt:.3f}pt" viewBox="0 0 {width_pt:.3f} {height_pt:.3f}">',
            f'<rect width="100%" height="100%" fill="{BACKGROUND}" />',
            add_composite_heading(spec.heading, width_pt),
            *bodies,
            "</svg>",
        ]
    )


def export_composite(svg_path: Path, pdf_path: Path, png_path: Path) -> None:
    """Export SVG to PDF and PNG preview via the Python CairoSVG API."""
    cairosvg.svg2pdf(url=str(svg_path), write_to=str(pdf_path))
    cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), dpi=300)


def save_composite(spec: CompositeSpec, output_dir: Path) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    svg_path = output_dir / f"{spec.name}.svg"
    pdf_path = output_dir / f"{spec.name}.pdf"
    png_path = output_dir / f"{spec.name}.png"
    svg_path.write_text(render_composite_svg(spec), encoding="utf-8")
    export_composite(svg_path, pdf_path, png_path)
    return pdf_path, svg_path, png_path


def source_panels(spec: CompositeSpec) -> Iterable[Path]:
    for panel in spec.panels:
        if isinstance(panel, (SvgPanel, RasterPanel)):
            yield panel.path
