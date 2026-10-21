"""Font choices for diagrams: a generic font, replacement font files, and a math font.

Every diagram package built on MosaicKit takes the same three settings:

* ``font``: ``"sans"`` (the default), ``"serif"`` or ``"mono"``;
* ``fonts``: a :class:`mosaickit.TextFonts` that replaces any of the three with font files, the
  rest keeping MosaicKit's DejaVu defaults;
* ``math_font``: a :class:`mosaickit.MathFont`, or the path of an OpenType math font, to set math
  through GlyphKit; without it math is set by Matplotlib.
"""

from __future__ import annotations

import os
from pathlib import Path

from mosaickit import ConfigurationError, MathFont, TextFonts

from utility_viz.core.errors.exceptions import InvalidParameterError

GENERIC_FONTS = ("sans", "serif", "mono")


def resolve_font(font: str | None) -> str | None:
    """Validate a generic font name; ``None`` keeps the default (sans)."""
    if font is None:
        return None
    if font not in GENERIC_FONTS:
        raise InvalidParameterError(
            f"font must be one of {', '.join(GENERIC_FONTS)}, got {font!r}; "
            "to use your own font files pass fonts=TextFonts(...)"
        )
    return font


def resolve_fonts(fonts: TextFonts | None) -> TextFonts | None:
    if fonts is not None and not isinstance(fonts, TextFonts):
        raise InvalidParameterError("fonts must be a mosaickit.TextFonts or None")
    return fonts


_OLD_MATH_TOKENS = frozenset({"dejavusans", "dejavuserif", "cm", "stix", "stixsans"})


def resolve_math_font(math_font: MathFont | str | os.PathLike[str] | None) -> MathFont | None:
    """A ``MathFont`` from one, or from the path of an OpenType math font file."""
    if math_font is None or isinstance(math_font, MathFont):
        return math_font
    if isinstance(math_font, str) and math_font in _OLD_MATH_TOKENS:
        raise InvalidParameterError(
            f"math_font {math_font!r} is a font set name from utility-viz 2.0.0b2 and earlier; "
            "pass the path of an OpenType math font file (STIX Two Math, Libertinus Math, ...)"
        )
    if isinstance(math_font, (str, os.PathLike)):
        try:
            return MathFont(Path(math_font))
        except ConfigurationError as error:
            raise InvalidParameterError(f"math_font: {error}") from None
    raise InvalidParameterError("math_font must be a mosaickit.MathFont or the path of a math font file")
