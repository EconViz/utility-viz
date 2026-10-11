"""Stroke: how one line is drawn (width, line style, colour, and arrowhead)."""

from __future__ import annotations

from dataclasses import dataclass

from utility_viz.core.errors.exceptions import InvalidParameterError
from utility_viz.core.styles.opacity import check_opacity
from utility_viz.enums import ArrowStyle, LineStyle


@dataclass(frozen=True)
class Stroke:
    """How to draw one line. Fields left as ``None`` keep the default.

    Parameters
    ----------
    width : float, optional
        Line width in points.
    style : LineStyle or str, optional
        ``"solid"``, ``"dashed"``, ``"dotted"``, or ``"dashdot"``.
    color : str, optional
        Any supported named or hexadecimal colour.
    arrow : ArrowStyle or str, optional
        Arrowhead drawn at the end of the line.
    opacity : float, optional
        From 0 (transparent) to 1 (opaque).
    """

    width: float | None = None
    style: LineStyle | str | None = None
    color: str | None = None
    arrow: ArrowStyle | str | None = None
    opacity: float | None = None

    def __post_init__(self) -> None:
        if self.width is not None and not self.width > 0:
            raise InvalidParameterError(f"Stroke width must be positive, got {self.width!r}")
        check_opacity("Stroke", self.opacity)
        for field, enum in (("style", LineStyle), ("arrow", ArrowStyle)):
            value = getattr(self, field)
            if value is None:
                continue
            try:
                object.__setattr__(self, field, enum(value))
            except ValueError:
                choices = ", ".join(item.value for item in enum)
                raise InvalidParameterError(f"invalid Stroke {field} {value!r}; choose: {choices}") from None

    def merged_over(self, base: Stroke | None) -> Stroke:
        """Return this stroke with unset fields taken from *base*."""
        if base is None:
            return self
        return Stroke(
            width=self.width if self.width is not None else base.width,
            style=self.style if self.style is not None else base.style,
            color=self.color if self.color is not None else base.color,
            arrow=self.arrow if self.arrow is not None else base.arrow,
            opacity=self.opacity if self.opacity is not None else base.opacity,
        )
