"""Label: how one text label is drawn (text, position, offset, colour, size)."""

from __future__ import annotations

from dataclasses import dataclass, replace

from mosaickit import ConfigurationError
from mosaickit.styles.nudge import parse_length

from utility_viz.core.errors.exceptions import InvalidParameterError
from utility_viz.core.styles.opacity import check_opacity
from utility_viz.enums import LabelPosition

_ALIASES = {"above": "top", "below": "bottom"}
NUDGES = ("top", "bottom", "left", "right")


def to_position(value, *, what: str) -> LabelPosition:
    """Normalise a label position, accepting ``"above"`` / ``"below"`` aliases."""
    try:
        return LabelPosition(_ALIASES.get(value, value))
    except ValueError:
        choices = ", ".join(p.value for p in LabelPosition)
        raise InvalidParameterError(f"invalid {what} {value!r}; choose: {choices}") from None


@dataclass(frozen=True)
class Label:
    """How to draw one text label. Fields left as ``None`` keep the default.

    Parameters
    ----------
    text : str, optional
        Label text, rendered as math like a plain-string label.
    position : LabelPosition or str, optional
        Side of the point or curve end where the text goes: ``"top"``,
        ``"bottom"``, ``"left"``, ``"right"``, or a corner such as
        ``"top-right"``. ``"above"`` / ``"below"`` are aliases.
    offset : float, optional
        Distance from the point, in points.
    color : str, optional
        Text colour. ``None`` follows the point's Marker colour when one is set.
    fontsize : float, optional
        Font size in points.
    visible : bool, optional
        ``False`` hides the label.
    opacity : float, optional
        From 0 (transparent) to 1 (opaque).
    top, bottom, left, right : float or str, optional
        Move the placed label up, down, left or right by a length: a number of points or a
        string such as ``"10pt"``, ``"0.5em"`` (em is the label's font size) or ``"2mm"``.
        The label is still placed as usual (by *position* and *offset*); the move is applied
        afterwards. ``top`` and ``bottom`` combine (``top - bottom``), as do ``right`` and
        ``left``; negative lengths move the other way.

    Examples
    --------
    >>> cvs.add_equilibrium(eq, label=Label(top="10pt"))  # doctest: +SKIP
    >>> cvs.add_point(5, 3, label=Label(text="A", left="6pt"))  # doctest: +SKIP
    """

    text: str | None = None
    position: LabelPosition | str | None = None
    offset: float | None = None
    color: str | None = None
    fontsize: float | None = None
    visible: bool | None = None
    opacity: float | None = None
    top: float | str | None = None
    bottom: float | str | None = None
    left: float | str | None = None
    right: float | str | None = None

    def __post_init__(self) -> None:
        check_opacity("Label", self.opacity)
        for name in NUDGES:
            check_length(f"Label {name}", getattr(self, name))
        if self.position is not None:
            object.__setattr__(self, "position", to_position(self.position, what="Label position"))
        if self.fontsize is not None and not self.fontsize > 0:
            raise InvalidParameterError(f"Label fontsize must be positive, got {self.fontsize!r}")

    def merged_over(self, base: Label | None) -> Label:
        """Return this label with unset fields taken from *base*."""
        if base is None:
            return self
        fields = ("text", "position", "offset", "color", "fontsize", "visible", "opacity", *NUDGES)
        return Label(
            **{
                field: getattr(self, field) if getattr(self, field) is not None else getattr(base, field)
                for field in fields
            }
        )


def check_length(owner: str, value) -> None:
    """Raise :class:`InvalidParameterError` unless *value* is ``None`` or a length (pt, em, mm, ...)."""
    if value is None:
        return
    try:
        parse_length(value, font_size=1.0)  # em is checked against a font size only when drawn
    except ConfigurationError as error:
        raise InvalidParameterError(f"{owner}: {error}") from None


def as_label(value) -> Label | None:
    """Accept a Label, a plain string (the text), or None."""
    if value is None or isinstance(value, Label):
        return value
    return Label(text=str(value))


def split_label(value, default: Label, text: str | None = None) -> tuple[str | None, Label]:
    """Split a ``str | Label`` argument into the text to draw and the style applied afterwards.

    *text* is used when *value* is a Label without text. The returned style is
    *value* over *default*, without text.
    """
    label = as_label(value) or Label()
    drawn = label.text if label.text is not None else (text if value is not None else None)
    return drawn, replace(label.merged_over(default), text=None)
