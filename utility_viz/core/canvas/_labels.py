"""Axis-label, line-style and math-text helpers shared by the canvas modules."""

from __future__ import annotations

import re

from utility_viz.core.constants.canvas import MATH_CHARS
from utility_viz.core.rendering.labels import HAlign, VAlign
from utility_viz.core.styles.stroke import Stroke
from utility_viz.enums import ArrowStyle, LabelPosition, LineStyle

_X_LABEL_POSITIONS: dict[LabelPosition, tuple[tuple[float, float], HAlign, VAlign]] = {
    LabelPosition.TOP: ((0, 8), "center", "bottom"),
    LabelPosition.RIGHT: ((8, 0), "left", "center"),
    LabelPosition.BOTTOM: ((0, -8), "center", "top"),
}
_Y_LABEL_POSITIONS: dict[LabelPosition, tuple[tuple[float, float], HAlign, VAlign]] = {
    LabelPosition.LEFT: ((-8, 0), "right", "center"),
    LabelPosition.TOP: ((0, 8), "center", "bottom"),
    LabelPosition.RIGHT: ((8, 0), "left", "center"),
}


def _label_position(value: LabelPosition | str, *, axis: str) -> LabelPosition:
    """Normalize and validate one axis-label position."""
    try:
        position = LabelPosition(value)
    except ValueError:
        valid = _X_LABEL_POSITIONS if axis == "x" else _Y_LABEL_POSITIONS
        choices = ", ".join(item.value for item in valid)
        raise ValueError(f"invalid {axis}-axis label position {value!r}; choose: {choices}") from None

    valid = _X_LABEL_POSITIONS if axis == "x" else _Y_LABEL_POSITIONS
    if position not in valid:
        choices = ", ".join(item.value for item in valid)
        raise ValueError(f"invalid {axis}-axis label position {value!r}; choose: {choices}")
    return position


def _line_style(value: LineStyle | str) -> LineStyle:
    """Normalize one axis line style."""
    try:
        return LineStyle(value)
    except ValueError:
        choices = ", ".join(item.value for item in LineStyle)
        raise ValueError(f"invalid line style {value!r}; choose: {choices}") from None


def _axis_stroke(theme, line_style, arrow_style, *overrides: Stroke | None) -> Stroke:
    """Resolve one axis's stroke; later *overrides* win, and the colour falls back to ``theme.axis_color``."""
    stroke = Stroke(
        style=_line_style(line_style) if line_style is not None else None,
        arrow=_arrow_style(arrow_style) if arrow_style is not None else None,
    ).merged_over(theme.axis_stroke)
    for override in overrides:
        if override is not None:
            stroke = override.merged_over(stroke)
    return stroke.merged_over(Stroke(color=theme.axis_color))


def _arrow_style(value: ArrowStyle | str) -> ArrowStyle:
    """Normalize one axis arrow style."""
    try:
        return ArrowStyle(value)
    except ValueError:
        choices = ", ".join(item.value for item in ArrowStyle)
        raise ValueError(f"invalid arrow style {value!r}; choose: {choices}") from None


def _label_math(text: str) -> str:
    if text.startswith("$") and text.endswith("$") and len(text) >= 2:
        return text
    return rf"${text}$"


def _math_wrap(text: str) -> str:
    """Wrap substrings containing LaTeX math characters in ``$...$``.

    Segments already enclosed in ``$...$`` are left untouched.  Plain-text
    segments that contain any of ``^ _ { } \\`` are automatically wrapped so
    that the scene text renderer treats them as mathematical notation.
    """
    parts = re.split(r"(\$[^$]+\$)", text)
    out = []
    for part in parts:
        if part.startswith("$") and part.endswith("$"):
            out.append(part)
        elif any(c in part for c in MATH_CHARS):
            out.append(f"${part}$")
        else:
            out.append(part)
    return "".join(out)
