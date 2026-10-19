"""Renderer-neutral placement of text beside a point."""

from __future__ import annotations

from typing import Literal

from utility_viz.enums import LabelPosition

HAlign = Literal["left", "center", "right"]
VAlign = Literal["bottom", "baseline", "center", "center_baseline", "top"]

LAYOUT: dict[LabelPosition, tuple[tuple[float, float], HAlign, VAlign]] = {
    LabelPosition.TOP: ((0, 1), "center", "bottom"),
    LabelPosition.BOTTOM: ((0, -1), "center", "top"),
    LabelPosition.LEFT: ((-1, 0), "right", "center"),
    LabelPosition.RIGHT: ((1, 0), "left", "center"),
    LabelPosition.TOP_RIGHT: ((1, 1), "left", "bottom"),
    LabelPosition.TOP_LEFT: ((-1, 1), "right", "bottom"),
    LabelPosition.BOTTOM_RIGHT: ((1, -1), "left", "top"),
    LabelPosition.BOTTOM_LEFT: ((-1, -1), "right", "top"),
}


def placement(position: LabelPosition, offset: float) -> tuple[tuple[float, float], HAlign, VAlign]:
    """Return the point offset and horizontal/vertical alignment."""
    (dx, dy), horizontal, vertical = LAYOUT[position]
    return (dx * offset, dy * offset), horizontal, vertical
