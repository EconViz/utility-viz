"""Fill: how one shaded region is drawn (colour and opacity)."""

from __future__ import annotations

from dataclasses import dataclass

from utility_viz.core.errors.exceptions import InvalidParameterError
from utility_viz.core.styles.opacity import check_opacity
from utility_viz.core.styles.validation import check_color


@dataclass(frozen=True)
class Fill:
    """How to shade one region. Fields left as ``None`` keep the default.

    Parameters
    ----------
    color : str, optional
        Any supported named or hexadecimal colour. ``None`` follows the outline's colour.
    alpha : float, optional
        Shorthand for *opacity*.
    opacity : float, optional
        From 0 (transparent) to 1 (opaque).
    """

    color: str | None = None
    alpha: float | None = None
    opacity: float | None = None

    def __post_init__(self) -> None:
        check_color("Fill", self.color)
        check_opacity("Fill", self.alpha)
        check_opacity("Fill", self.opacity)
        if self.alpha is not None and self.opacity is not None and self.alpha != self.opacity:
            raise InvalidParameterError("Fill: give opacity or alpha, not both.")
        # Keep both names in step so either reads the same value.
        value = self.opacity if self.opacity is not None else self.alpha
        object.__setattr__(self, "opacity", value)
        object.__setattr__(self, "alpha", value)

    def merged_over(self, base: Fill | None) -> Fill:
        """Return this fill with unset fields taken from *base*."""
        if base is None:
            return self
        return Fill(
            color=self.color if self.color is not None else base.color,
            opacity=self.opacity if self.opacity is not None else base.opacity,
        )
