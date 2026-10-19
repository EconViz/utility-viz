"""Backend-neutral validation of public colour and marker-shape tokens."""

from __future__ import annotations

import re

from utility_viz.core.errors.exceptions import InvalidParameterError

_COLORS = frozenset(
    {
        "black",
        "white",
        "red",
        "green",
        "blue",
        "yellow",
        "orange",
        "purple",
        "pink",
        "brown",
        "gray",
        "grey",
        "lightgray",
        "lightgrey",
        "darkgray",
        "darkgrey",
        "cyan",
        "magenta",
        "teal",
        "navy",
        "olive",
        "maroon",
        "gold",
        "transparent",
        "none",
    }
)
_SHAPES = frozenset({"o", "s", "^", "v", "<", ">", "D", "d", "*", "+", "x", ".", ",", "p", "h", "H", "|", "_"})


def check_color(owner: str, value: str | None) -> None:
    """Raise :class:`InvalidParameterError` if *value* is a colour the backend rejects."""
    valid = value is None or bool(re.fullmatch(r"#[0-9a-fA-F]{3}([0-9a-fA-F]{3})?([0-9a-fA-F]{2})?", value))
    valid = valid or (value is not None and value.lower() in _COLORS)
    if not valid:
        raise InvalidParameterError(f"invalid {owner} color {value!r}")


def check_shape(owner: str, value: str | None) -> None:
    """Raise :class:`InvalidParameterError` if *value* is a marker shape the backend rejects."""
    if value is not None and value not in _SHAPES:
        raise InvalidParameterError(f"invalid {owner} shape {value!r}")
