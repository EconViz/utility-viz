"""Enumerations for axis-label placement, arrowheads, and axis line styles."""

from enum import Enum


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


class ArrowStyle(str, Enum):
    """Arrowhead styles for canvas axes."""

    SIMPLE = "->"
    TRIANGLE = "-|>"
    FANCY = "fancy"
    WEDGE = "wedge"


class LineStyle(str, Enum):
    """Line styles for the canvas axes."""

    SOLID = "solid"
    DASHED = "dashed"
    DOTTED = "dotted"
    DASHDOT = "dashdot"

    @classmethod
    def _missing_(cls, value):
        """Also accept the conventional short forms: ``-``, ``--``, ``:``, ``-.``."""
        return {"-": cls.SOLID, "--": cls.DASHED, ":": cls.DOTTED, "-.": cls.DASHDOT}.get(value)
