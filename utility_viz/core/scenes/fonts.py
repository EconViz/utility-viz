"""Compatibility normalization for renderer-owned font selection."""

from __future__ import annotations

from collections.abc import Sequence

from utility_viz.core.errors.exceptions import InvalidParameterError

MATH_FAMILIES = {
    "dejavusans": "DejaVu Sans",
    "dejavuserif": "DejaVu Serif",
    "cm": "Computer Modern",
    "stix": "STIXGeneral",
    "stixsans": "STIXGeneral",
}
def resolve_font(font: str | Sequence[str] | None) -> tuple[tuple[str, ...] | None, str | None]:
    """Validate a compatibility hint and leave availability to the renderer."""
    if font is None:
        return None, None
    families = (font,) if isinstance(font, str) else tuple(font)
    if not families or not all(isinstance(family, str) and family.strip() for family in families):
        raise InvalidParameterError("font must be a family name or a non-empty list of family names")
    return families, families[0]


def resolve_math_font(math_font: str | None) -> tuple[str | None, str | None]:
    """Return the public math-font token and its MosaicKit text family."""
    if math_font is None:
        return None, None
    try:
        return math_font, MATH_FAMILIES[math_font]
    except KeyError:
        choices = ", ".join(MATH_FAMILIES)
        raise InvalidParameterError(f"invalid math_font {math_font!r}; choose: {choices}") from None
