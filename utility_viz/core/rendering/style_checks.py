"""Backend-neutral validation of colour and marker-shape strings."""

from __future__ import annotations

import re

from utility_viz.core.styles.validation import register_checks


def _is_color(value: str) -> bool:
    if re.fullmatch(r"#[0-9a-fA-F]{3}([0-9a-fA-F]{3})?([0-9a-fA-F]{2})?", value):
        return True
    return value.lower() in {
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


def _is_shape(value: str) -> bool:
    return value in {"o", "s", "^", "v", "<", ">", "D", "d", "*", "+", "x", ".", ",", "p", "h", "H", "|", "_"}


register_checks(color=_is_color, shape=_is_shape)
