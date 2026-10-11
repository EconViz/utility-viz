"""Renderer-neutral validation and scene font-family selection."""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Sequence
from functools import cache

from utility_viz.core.errors.exceptions import InvalidParameterError

GENERIC_FAMILIES = frozenset({"serif", "sans-serif", "sans", "monospace", "cursive", "fantasy"})
MATH_FAMILIES = {
    "dejavusans": "DejaVu Sans",
    "dejavuserif": "DejaVu Serif",
    "cm": "Computer Modern",
    "stix": "STIXGeneral",
    "stixsans": "STIXGeneral",
}
_BUNDLED_FAMILIES = frozenset({"dejavu sans", "dejavu serif", "stixgeneral", "computer modern"})


@cache
def _system_families() -> frozenset[str] | None:
    """Read fontconfig when present without importing a rendering backend."""
    executable = shutil.which("fc-list")
    if executable is None:
        return None
    try:
        result = subprocess.run(
            [executable, ":", "family"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return frozenset(
        name.strip().casefold() for line in result.stdout.splitlines() for name in line.split(",") if name.strip()
    )


def resolve_font(font: str | Sequence[str] | None) -> tuple[tuple[str, ...] | None, str | None]:
    """Validate an ordered fallback list and select the first available family."""
    if font is None:
        return None, None
    families = (font,) if isinstance(font, str) else tuple(font)
    if not families or not all(isinstance(family, str) and family.strip() for family in families):
        raise InvalidParameterError("font must be a family name or a non-empty list of family names")
    installed = _system_families()
    for family in families:
        normalized = family.strip().casefold()
        if normalized in GENERIC_FAMILIES or normalized in _BUNDLED_FAMILIES:
            return families, family
        if installed is None or normalized in installed:
            return families, family
    raise InvalidParameterError(
        f"font not found: {', '.join(families)}. Install it, add a fallback, "
        "or use a generic family such as 'serif', 'sans-serif', or 'monospace'."
    )


def resolve_math_font(math_font: str | None) -> tuple[str | None, str | None]:
    """Return the public math-font token and its MosaicKit text family."""
    if math_font is None:
        return None, None
    try:
        return math_font, MATH_FAMILIES[math_font]
    except KeyError:
        choices = ", ".join(MATH_FAMILIES)
        raise InvalidParameterError(f"invalid math_font {math_font!r}; choose: {choices}") from None
