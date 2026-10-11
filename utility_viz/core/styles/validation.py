"""Pluggable value checks for styles that need a drawing backend.

Styles are pure data and never import a renderer. Whether a colour string or a
marker shape is valid is a backend question, so the rendering layer registers
the checks when it is imported (see ``utility_viz.core.rendering.style_checks``).
Until a check is registered the value is accepted and only the backend rejects it.
"""

from __future__ import annotations

from collections.abc import Callable

from utility_viz.core.errors.exceptions import InvalidParameterError

_color_check: Callable[[str], bool] | None = None
_shape_check: Callable[[str], bool] | None = None


def register_checks(*, color: Callable[[str], bool], shape: Callable[[str], bool]) -> None:
    """Install the backend predicates for colour and marker-shape strings."""
    global _color_check, _shape_check
    _color_check = color
    _shape_check = shape


def check_color(owner: str, value: str | None) -> None:
    """Raise :class:`InvalidParameterError` if *value* is a colour the backend rejects."""
    if value is not None and _color_check is not None and not _color_check(value):
        raise InvalidParameterError(f"invalid {owner} color {value!r}")


def check_shape(owner: str, value: str | None) -> None:
    """Raise :class:`InvalidParameterError` if *value* is a marker shape the backend rejects."""
    if value is not None and _shape_check is not None and not _shape_check(value):
        raise InvalidParameterError(f"invalid {owner} shape {value!r}")
