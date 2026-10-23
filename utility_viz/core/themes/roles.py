"""Built-in themes from mosaickit's shared theme tokens.

A shared theme (:mod:`mosaickit.themes.shared`) gives a colour to each *role* and three size
multipliers. This module is the only place where utility-viz meets those tokens:

- :data:`ELEMENT_ROLES` says which role colours each utility-viz element;
- :data:`SIZE_PRESETS` holds utility-viz's own sizes (sizes are not tokens), and
- :func:`theme_from_tokens` / :func:`build_theme` turn tokens plus sizes into a :class:`Theme`.

The built-in themes in :mod:`utility_viz.core.themes` and the ``base`` names of
``econ-viz.toml`` are all built here.

Sizes
-----
A :class:`SizePreset` has two parts:

``values``
    Theme fields (line widths, marker sizes, the axis and guide strokes, ``label_scale``,
    ``budget_fill_alpha``, ...). They are the *base sizes*: the theme's ``line_scale``
    multiplies every width, ``marker_scale`` every marker size and ``label_scale`` the
    label scale.
``styles``
    Exact styles for single elements, merged over the theme's own, as an
    ``[utility.stroke.<name>]`` table would be. They are used as given, not scaled.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import cache
from types import MappingProxyType
from typing import Any

from mosaickit.themes import ThemeTokens, get_tokens, list_shared_themes

from utility_viz.core.styles.fill import Fill
from utility_viz.core.styles.label import Label
from utility_viz.core.styles.marker import Marker
from utility_viz.core.styles.stroke import Stroke
from utility_viz.core.themes.theme import Theme
from utility_viz.core.themes.variants import MonochromeTheme, PresentationTheme
from utility_viz.enums import ArrowStyle, LabelPosition, LineStyle

#: utility-viz element -> shared theme role. The element name is the Theme field without
#: ``_color`` (``ic`` -> ``ic_color``). The budget fill follows the budget line, so it is
#: ``constraint`` too.
ELEMENT_ROLES: Mapping[str, str] = MappingProxyType(
    {
        "background": "background",
        "axis": "ink",
        "label": "ink",
        "ic": "primary",
        "secondary_ic": "subtle",
        "path": "secondary",
        "compensated_budget": "secondary",
        "budget": "constraint",
        "eq": "accent",
        "core": "accent",
        "walrasian": "primary",
        "ray": "muted",
        "subsistence": "muted",
        "price": "muted",
        "contract": "muted",
        "sub_effect": "series.1",
        "inc_effect": "series.2",
        "kink": "series.3",
    }
)

#: The shared theme names, each a built-in base.
THEME_NAMES: tuple[str, ...] = list_shared_themes()


@dataclass(frozen=True)
class SizePreset:
    """utility-viz's sizes for one theme (see the module docstring)."""

    values: Mapping[str, Any] = field(default_factory=dict)
    styles: Mapping[str, Stroke | Marker | Label | Fill] = field(default_factory=dict)
    theme_class: type[Theme] = Theme


#: The sizes of the colour themes: the Theme defaults.
BASE_SIZES = SizePreset()

_GUIDE = Stroke(width=0.8, style=LineStyle.DASHED, color="#1a1a1a")

#: The figures of the manual (the playground): heavier curves, dashed guides, larger points.
MANUAL_SIZES = SizePreset(
    values={
        "axis_stroke": Stroke(width=1.0, style=LineStyle.SOLID, arrow=ArrowStyle.TRIANGLE),
        "drop_stroke": Stroke(width=0.8, style=LineStyle.DASHED, color="#1a1a1a"),
        "projection_stroke": _GUIDE,
        "guide_stroke": _GUIDE,
    },
    styles={
        "ic_stroke": Stroke(width=2.6),
        "secondary_ic_stroke": Stroke(width=1.8, opacity=1.0),
        "path_stroke": Stroke(width=1.4),
        "budget_stroke": Stroke(width=2.6),
        "ray_stroke": Stroke(width=0.9),
        "substitution_stroke": Stroke(width=1.8),
        "income_stroke": Stroke(width=1.8),
        "compensated_budget_stroke": Stroke(width=1.0),
        "contract_stroke": Stroke(width=2.6),
        "price_stroke": Stroke(width=2.6),
        "eq_marker": Marker(size=5),
        "point_marker": Marker(size=5),
        "point_label": Label(fontsize=14, position=LabelPosition.RIGHT, offset=10),
        "budget_fill": Fill(opacity=0.08),
    },
)

#: Journal figures: thinner lines, smaller points and labels.
PAPER_SIZES = SizePreset(
    values={
        "ic_linewidth": 1.2,
        "path_linewidth": 1.4,
        "budget_linewidth": 1.0,
        "budget_fill_alpha": 0.06,
        "eq_markersize": 3.0,
        "ray_linewidth": 0.6,
        "effect_arrow_linewidth": 1.1,
        "compensated_budget_linewidth": 1.0,
        "subsistence_linewidth": 0.6,
        "contract_linewidth": 0.9,
        "core_linewidth": 2.0,
        "price_linewidth": 0.9,
        "walrasian_markersize": 7.0,
        "label_scale": 0.9,
    }
)

SIZE_PRESETS: Mapping[str, SizePreset] = MappingProxyType(
    {
        "manual": MANUAL_SIZES,
        "default": BASE_SIZES,
        "colorblind": BASE_SIZES,
        "monochrome": SizePreset(values={"walrasian_markersize": 11.0}, theme_class=MonochromeTheme),
        "nord": SizePreset(values={"budget_fill_alpha": 0.10, "ray_linewidth": 1.0}),
        "paper": PAPER_SIZES,
        # Default sizes; the presentation tokens scale them up.
        "presentation": SizePreset(theme_class=PresentationTheme),
    }
)

_STROKE_FIELDS = tuple(f.name for f in dataclasses.fields(Theme) if f.type in ("Stroke", Stroke))


def theme_colors(tokens: ThemeTokens) -> dict[str, Any]:
    """The Theme colour fields for *tokens*, following :data:`ELEMENT_ROLES`.

    ``subtle`` with an alpha byte becomes ``secondary_ic_opacity`` (without one the size
    preset's opacity is kept); when its colour is the ``primary`` colour,
    ``secondary_ic_color`` stays ``None`` so the subdued curves keep following ``ic`` when
    that is changed.
    """
    colors: dict[str, Any] = {}
    for element, role in ELEMENT_ROLES.items():
        value = tokens.color(role)
        if element == "secondary_ic":
            assert value is not None
            rgb, alpha = value[:7], value[7:]
            primary = tokens.color("primary") or ""
            colors["secondary_ic_color"] = None if alpha and rgb.lower() == primary.lower() else rgb
            if alpha:
                colors["secondary_ic_opacity"] = round(int(alpha, 16) / 255, 2)
        else:
            colors[f"{element}_color"] = value
    return colors


def _scale_of(name: str, tokens: ThemeTokens) -> float | None:
    """The multiplier of Theme field *name*, or ``None`` when it is not a size."""
    if name.endswith("_linewidth") or name in _STROKE_FIELDS:
        return tokens.line_scale
    if name.endswith("_markersize"):
        return tokens.marker_scale
    if name == "label_scale":
        return tokens.label_scale
    return None


def _sizes(preset: SizePreset, tokens: ThemeTokens) -> dict[str, Any]:
    """The preset's base sizes with the theme's multipliers applied."""
    defaults = {f.name: f.default for f in dataclasses.fields(Theme)}
    values = {
        name: value.merged_over(defaults[name]) if name in _STROKE_FIELDS else value
        for name, value in preset.values.items()
    }
    for name, default in defaults.items():
        scale = _scale_of(name, tokens)
        if scale is None or scale == 1.0:
            continue
        current = values.get(name, default)
        if isinstance(current, Stroke):
            if current.width is not None:
                values[name] = dataclasses.replace(current, width=round(current.width * scale, 6))
        else:
            values[name] = round(current * scale, 6)
    return values


def _with_styles(cls: type[Theme], styles: Mapping[str, Any], name: str) -> type[Theme]:
    """A subclass of *cls* whose properties in *styles* are merged over *cls*'s own."""
    if not styles:
        return cls
    sub: type[Theme]
    namespace = {
        prop: property(
            lambda self, _prop=prop, _style=style: _style.merged_over(getattr(super(sub, self), _prop))  # type: ignore[misc]
        )
        for prop, style in styles.items()
    }
    sub = type(f"{name.title()}Theme", (cls,), namespace)
    sub.__module__ = __name__
    return sub


def theme_from_tokens(tokens: ThemeTokens, sizes: SizePreset | None = None, *, name: str | None = None) -> Theme:
    """A :class:`Theme` coloured by *tokens* with *sizes* (default: the preset of that name)."""
    preset = sizes if sizes is not None else SIZE_PRESETS.get(tokens.name, BASE_SIZES)
    theme_name = name or tokens.name
    for prop in preset.styles:
        if not isinstance(getattr(preset.theme_class, prop, None), property):
            raise ValueError(f"size preset style {prop!r} is not a Theme property")
    cls = _with_styles(preset.theme_class, preset.styles, theme_name)
    return cls(name=theme_name, **{**_sizes(preset, tokens), **theme_colors(tokens)})


@cache
def build_theme(name: str) -> Theme:
    """The built-in theme *name*: a shared theme name (see :data:`THEME_NAMES`)."""
    return theme_from_tokens(get_tokens(name))


__all__ = [
    "BASE_SIZES",
    "ELEMENT_ROLES",
    "MANUAL_SIZES",
    "PAPER_SIZES",
    "SIZE_PRESETS",
    "THEME_NAMES",
    "SizePreset",
    "build_theme",
    "theme_colors",
    "theme_from_tokens",
]
