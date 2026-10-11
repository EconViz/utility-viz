"""Export a mosaickit scene to TikZ.

Curve layers whose ``model`` is a bezierkit ``PiecewiseBezier`` (the indifference curves)
are written with bezierkit's native ``.. controls ..`` serialiser, i.e. from the same
Bezier source the raster backend sampled. Other paths are polylines, markers are circles,
and text becomes nodes. Styles come from the canvas theme through the same role
resolution used by the MosaicKit scene, and colour names resolve against the canvas palette.
"""

from __future__ import annotations

import math
from typing import Any

from bezierkit.bezier.path import PiecewiseBezier
from bezierkit.export.tikz import to_tikz
from mosaickit import (
    ArrowPlacement,
    Canvas,
    Color,
    FillLayer,
    Layer,
    LegendLayer,
    MarkerLayer,
    Palette,
    PathLayer,
    Stroke,
    TextLayer,
)
from mosaickit.scene.text import TEXT_ANCHORS

_DASH = {"solid": "", "dashed": "dashed", "dotted": "dotted", "dashdot": "dash dot"}
_HORIZONTAL = {"left": "west", "right": "east", "center": ""}
_VERTICAL = {"top": "north", "bottom": "south", "center": ""}
_ESCAPES = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}"}


class _Colors:
    def __init__(self, palette: Palette) -> None:
        self._palette = palette
        self.defined: dict[str, str] = {}

    def name(self, color: Color | str) -> str:
        if isinstance(color, str):
            color = Color.from_hex(color) if color.startswith("#") else self._palette[color]
        value = color.to_hex(include_alpha=False).lstrip("#").upper()
        name = f"uv{value}"
        self.defined[name] = value
        return name


def _number(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".") or "0"


def _points(points: object) -> str:
    return " -- ".join(f"({_number(x)},{_number(y)})" for x, y in points)  # type: ignore[attr-defined]


def _stroke_options(stroke: Stroke, placement: ArrowPlacement, colors: _Colors) -> list[str]:
    opts = [colors.name(stroke.color), f"line width={_number(stroke.width)}pt"]  # type: ignore[arg-type]
    dash = _DASH[stroke.dash.value]  # type: ignore[union-attr]
    if dash:
        opts.append(dash)
    if stroke.opacity is not None and stroke.opacity < 1:
        opts.append(f"opacity={_number(stroke.opacity)}")
    if stroke.arrow is not None:
        tip = "{Stealth[length=5pt]}"
        opts.append(
            {
                ArrowPlacement.END: f"-{tip}",
                ArrowPlacement.START: f"{tip}-",
                ArrowPlacement.BOTH: f"{tip}-{tip}",
            }[placement]
        )
    return opts


def _path_command(layer: PathLayer, bundle: Any, colors: _Colors, clip: str) -> str:
    stroke = layer.stroke.merged_over(bundle.stroke) if layer.stroke and bundle.stroke else bundle.stroke
    assert stroke is not None
    opts = _stroke_options(stroke, layer.arrow_placement, colors)
    if isinstance(layer.model, PiecewiseBezier):
        command = to_tikz(layer.model, options=",".join(opts))
    else:
        command = f"\\draw[{','.join(opts)}] {_points(layer.path)};"
    return f"\\begin{{scope}}{clip}{command}\\end{{scope}}" if layer.clip else command


def _fill_command(layer: FillLayer, bundle: Any, colors: _Colors) -> str:
    fill = layer.fill.merged_over(bundle.fill) if layer.fill and bundle.fill else bundle.fill
    assert fill is not None
    opts = [colors.name(fill.color)]  # type: ignore[arg-type]
    if fill.opacity is not None and fill.opacity < 1:
        opts.append(f"opacity={_number(fill.opacity)}")
    return f"\\fill[{','.join(opts)}] {_points(layer.boundary)} -- cycle;"


def _marker_commands(layer: MarkerLayer, bundle: Any, colors: _Colors) -> list[str]:
    marker = layer.marker.merged_over(bundle.marker) if layer.marker and bundle.marker else bundle.marker
    assert marker is not None
    radius = math.sqrt(marker.size) / 2  # type: ignore[arg-type]
    opts = [colors.name(marker.color)]  # type: ignore[arg-type]
    if marker.opacity is not None and marker.opacity < 1:
        opts.append(f"opacity={_number(marker.opacity)}")
    shape = marker.shape or "o"
    return [_marker_command(x, y, radius, shape, opts) for x, y in layer.points]


def _marker_command(x: float, y: float, radius: float, shape: str, opts: list[str]) -> str:
    """Emit common MosaicKit marker shapes without depending on a TikZ plot backend."""
    at = f"({_number(x)},{_number(y)})"
    style = ",".join(opts)
    r = _number(radius)
    if shape in {"s", "square"}:
        return f"\\fill[{style}] ([xshift=-{r}pt,yshift=-{r}pt]{at}) rectangle ([xshift={r}pt,yshift={r}pt]{at});"
    if shape in {"D", "d", "diamond"}:
        return (
            f"\\fill[{style}] ([yshift={r}pt]{at}) -- ([xshift={r}pt]{at}) -- "
            f"([yshift=-{r}pt]{at}) -- ([xshift=-{r}pt]{at}) -- cycle;"
        )
    if shape in {"^", "v", "<", ">"}:
        vertices = {
            "^": ((0, 1), (1, -1), (-1, -1)),
            "v": ((0, -1), (1, 1), (-1, 1)),
            "<": ((-1, 0), (1, 1), (1, -1)),
            ">": ((1, 0), (-1, 1), (-1, -1)),
        }[shape]
        points = " -- ".join(
            f"([xshift={_number(dx * radius)}pt,yshift={_number(dy * radius)}pt]{at})" for dx, dy in vertices
        )
        return f"\\fill[{style}] {points} -- cycle;"
    if shape == "*":
        star_points: list[str] = []
        for index in range(10):
            angle = math.pi / 2 + index * math.pi / 5
            length = radius if index % 2 == 0 else radius * 0.4
            star_points.append(
                f"([xshift={_number(math.cos(angle) * length)}pt,yshift={_number(math.sin(angle) * length)}pt]{at})"
            )
        return f"\\fill[{style}] {' -- '.join(star_points)} -- cycle;"
    return f"\\fill[{style}] {at} circle ({r}pt);"


def _text_command(layer: TextLayer, bundle: Any, colors: _Colors) -> str:
    style = layer.style.merged_over(bundle.text) if layer.style and bundle.text else bundle.text
    assert style is not None
    horizontal, vertical = TEXT_ANCHORS[layer.anchor]
    anchor = " ".join(part for part in (_VERTICAL[vertical], _HORIZONTAL[horizontal]) if part)
    size = float(style.size or 12)
    opts = [
        f"text={colors.name(style.color)}",  # type: ignore[arg-type]
        f"font=\\fontsize{{{_number(size)}}}{{{_number(size * 1.2)}}}\\selectfont",
        f"xshift={_number(layer.offset[0])}pt",
        f"yshift={_number(layer.offset[1])}pt",
    ]
    if anchor:
        opts.insert(0, f"anchor={anchor}")
    text = f"${layer.text}$" if layer.math else "".join(_ESCAPES.get(c, c) for c in str(layer.text))
    px, py = layer.position
    return f"\\node[{','.join(opts)}] at ({_number(px)},{_number(py)}) {{{text}}};"


def _layer_commands(layer: Layer, bundle: Any, colors: _Colors, clip: str) -> list[str]:
    """TikZ commands for one visible layer (none for a legend)."""
    if isinstance(layer, PathLayer):
        return [_path_command(layer, bundle, colors, clip)]
    if isinstance(layer, FillLayer):
        return [_fill_command(layer, bundle, colors)]
    if isinstance(layer, MarkerLayer):
        return _marker_commands(layer, bundle, colors)
    if isinstance(layer, TextLayer):
        return [_text_command(layer, bundle, colors)]
    if isinstance(layer, LegendLayer):
        return []
    raise NotImplementedError(f"TikZ export does not support {type(layer).__name__}")


def canvas_to_tikz(canvas: Canvas, *, standalone: bool = True) -> str:
    """TikZ source for *canvas*'s scene; a ``standalone`` document unless disabled.

    The picture is scaled so the plotting area is ``spec.width`` by ``spec.height`` inches.
    """
    spec = canvas.spec
    colors = _Colors(canvas.config.palette)
    x0, x1, y0, y1 = spec.x_min, spec.x_max, spec.y_min, spec.y_max
    clip = f"\\clip ({_number(x0)},{_number(y0)}) rectangle ({_number(x1)},{_number(y1)});"
    body: list[str] = []

    for layer in canvas.snapshot().ordered_layers:
        if not layer.visible:
            continue
        bundle = canvas.theme.resolve(layer.role, fallback_category=layer.fallback_category)
        body.extend(_layer_commands(layer, bundle, colors, clip))

    defs = "\n".join(f"\\definecolor{{{name}}}{{HTML}}{{{value}}}" for name, value in sorted(colors.defined.items()))
    picture = (
        f"\\begin{{tikzpicture}}[x={_number(spec.width / (x1 - x0))}in,y={_number(spec.height / (y1 - y0))}in]\n"
        + "\n".join(body)
        + "\n\\end{tikzpicture}\n"
    )
    if not standalone:
        return f"{defs}\n{picture}"
    return (
        "\\documentclass[tikz,border=12pt]{standalone}\n\\usepackage{xcolor}\n\\usetikzlibrary{arrows.meta}\n"
        f"{defs}\n\\begin{{document}}\n{picture}\\end{{document}}\n"
    )
