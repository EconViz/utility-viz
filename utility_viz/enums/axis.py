"""Enumerations for axis-label placement, arrowheads, and axis line styles."""

from enum import Enum

from mosaickit import ArrowStyle, DashStyle

# The line and arrow styles are MosaicKit's: ``LineStyle`` is its ``DashStyle`` under the name
# utility-viz has always used, and ``ArrowStyle.SIMPLE`` is MosaicKit's ``OPEN``.
LineStyle = DashStyle
__all__ = ["ArrowStyle", "LabelPosition", "LineStyle"]


class LabelPosition(str, Enum):
    """Cardinal positions used to place labels around an axis arrowhead."""

    TOP = "top"
    LEFT = "left"
    BOTTOM = "bottom"
    RIGHT = "right"
    TOP_RIGHT = "top-right"
    TOP_LEFT = "top-left"
    BOTTOM_RIGHT = "bottom-right"
    BOTTOM_LEFT = "bottom-left"
