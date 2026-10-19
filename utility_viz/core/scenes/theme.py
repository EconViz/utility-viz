"""The utility-viz theme for mosaickit scenes.

Colours and widths mirror the defaults of the legacy ``utility_viz.core.themes.Theme``
(``tests/scenes/test_theme.py`` pins the parity); they are restated here because scene
modules may not import the legacy theme layer.
"""

from __future__ import annotations

from dataclasses import dataclass

from mosaickit import DashStyle, Fill, Marker, Stroke, StyleBundle, TextStyle, Theme, ThemeRegistry
from mosaickit.themes import default

from utility_viz.core.scenes.roles import Budget, Equilibrium, Indifference


@dataclass(frozen=True)
class UtilityColors:
    """Colour and weight inputs of the utility theme (legacy ``Theme`` field names)."""

    axis_color: str = "#222222"
    label_color: str = "#222222"
    background_color: str | None = None
    ic_color: str = "#377EB8"
    ic_linewidth: float = 1.8
    secondary_ic_color: str | None = None
    secondary_ic_linewidth: float = 1.0
    secondary_ic_opacity: float = 0.45
    budget_color: str = "#984EA3"
    budget_linewidth: float = 1.5
    budget_fill_alpha: float = 0.08
    compensated_budget_color: str = "#777777"
    compensated_budget_linewidth: float = 1.5
    eq_color: str = "#E41A1C"
    eq_markersize: float = 4.0  # marker diameter in points (legacy unit)
    ray_color: str = "#999999"
    ray_linewidth: float = 0.8
    drop_linewidth: float = 0.8


def utility_roles(colors: UtilityColors | None = None) -> dict[str, StyleBundle]:
    """Role -> sparse style for the budget, equilibrium and indifference concepts."""
    c = colors or UtilityColors()
    secondary = c.secondary_ic_color or c.ic_color
    return {
        Budget.MAIN.value: StyleBundle(
            stroke=Stroke(color=c.budget_color, width=c.budget_linewidth, dash=DashStyle.SOLID),
            text=TextStyle(color=c.budget_color, size=12),
        ),
        Budget.FILL.value: StyleBundle(fill=Fill(color=c.budget_color, opacity=c.budget_fill_alpha)),
        Budget.COMPENSATED.value: StyleBundle(
            stroke=Stroke(
                color=c.compensated_budget_color,
                width=c.compensated_budget_linewidth,
                dash=DashStyle.DASHED,
            ),
            text=TextStyle(color=c.compensated_budget_color),
        ),
        Equilibrium.MAIN.value: StyleBundle(
            marker=Marker(
                color=c.eq_color,
                size=c.eq_markersize**2,
                shape="o",
                edge_color=c.eq_color,
                edge_width=0,
            ),
            text=TextStyle(color=c.eq_color, size=12),
        ),
        Equilibrium.DROP.value: StyleBundle(
            stroke=Stroke(color=c.eq_color, width=c.drop_linewidth, dash=DashStyle.DOTTED)
        ),
        Equilibrium.RAY.value: StyleBundle(
            stroke=Stroke(color=c.ray_color, width=c.ray_linewidth, dash=DashStyle.DASHED)
        ),
        Indifference.MAIN.value: StyleBundle(
            stroke=Stroke(color=c.ic_color, width=c.ic_linewidth, dash=DashStyle.SOLID),
            text=TextStyle(color=c.ic_color, size=9),
        ),
        Indifference.SECONDARY.value: StyleBundle(
            stroke=Stroke(color=secondary, width=c.secondary_ic_linewidth, opacity=c.secondary_ic_opacity),
            text=TextStyle(color=secondary, opacity=c.secondary_ic_opacity),
        ),
    }


def _surface_roles(c: UtilityColors) -> dict[str, StyleBundle]:
    """MosaicKit's undotted built-in surface roles, kept out of domain registration."""
    return {
        "canvas": StyleBundle(
            fill=Fill(
                color=c.background_color or "white",
                opacity=1.0 if c.background_color is not None else 0.0,
            )
        ),
        "axes": StyleBundle(
            stroke=Stroke(color=c.axis_color, width=1.0),
            text=TextStyle(color=c.label_color),
        ),
    }


def utility_theme(colors: UtilityColors | None = None, *, name: str = "utility") -> Theme:
    """The mosaickit default theme extended with the utility-viz roles."""
    c = colors or UtilityColors()
    return Theme(name, {**default.roles, **_surface_roles(c), **utility_roles(c)})


UTILITY_THEME = utility_theme()


def register_utility_theme(registry: ThemeRegistry, colors: UtilityColors | None = None) -> Theme:
    """Add the utility roles to *registry*'s ``default`` theme and return it."""
    return registry.register_roles("default", utility_roles(colors))
