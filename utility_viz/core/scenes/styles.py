"""Translate utility-viz compatibility styles to MosaicKit styles.

The public utility-viz style objects retain their 2.0 spelling while MosaicKit
owns the renderer-facing representation.  Keeping this conversion at the scene
boundary prevents economic models and compatibility data classes from knowing
about a concrete rendering backend.
"""

from __future__ import annotations

from typing import Any

from mosaickit import (
    ArrowStyle as MosaicArrowStyle,
)
from mosaickit import (
    DashStyle,
    TextStyle,
)
from mosaickit import (
    Fill as MosaicFill,
)
from mosaickit import (
    Marker as MosaicMarker,
)
from mosaickit import (
    Stroke as MosaicStroke,
)
from mosaickit import (
    Theme as MosaicTheme,
)

from utility_viz.core.styles.fill import Fill
from utility_viz.core.styles.label import Label
from utility_viz.core.styles.marker import Marker
from utility_viz.core.styles.stroke import Stroke
from utility_viz.enums import ArrowStyle, LineStyle

_DASHES = {
    LineStyle.SOLID: DashStyle.SOLID,
    LineStyle.DASHED: DashStyle.DASHED,
    LineStyle.DOTTED: DashStyle.DOTTED,
    LineStyle.DASHDOT: DashStyle.DASHDOT,
}

_ARROWS = {
    ArrowStyle.SIMPLE: MosaicArrowStyle.OPEN,
    ArrowStyle.TRIANGLE: MosaicArrowStyle.TRIANGLE,
    ArrowStyle.FANCY: MosaicArrowStyle.FANCY,
    ArrowStyle.WEDGE: MosaicArrowStyle.WEDGE,
}


def to_mosaic_stroke(value: Stroke | None) -> MosaicStroke | None:
    """Convert a sparse public stroke without filling in theme defaults."""
    if value is None:
        return None
    return MosaicStroke(
        color=value.color,
        width=value.width,
        dash=_DASHES[LineStyle(value.style)] if value.style is not None else None,
        arrow=_ARROWS[ArrowStyle(value.arrow)] if value.arrow is not None else None,
        opacity=value.opacity,
    )


def to_mosaic_fill(value: Fill | None) -> MosaicFill | None:
    """Convert a sparse public fill."""
    if value is None:
        return None
    return MosaicFill(color=value.color, opacity=value.opacity)


def to_mosaic_marker(value: Marker | None) -> MosaicMarker | None:
    """Convert marker diameter in points to MosaicKit's point-area unit."""
    if value is None:
        return None
    size = value.size**2 if value.size is not None else None
    return MosaicMarker(
        color=value.color,
        size=size,
        shape=value.shape,
        opacity=value.opacity,
        edge_color=value.color,
        edge_width=0 if value.color is not None else None,
    )


def to_mosaic_text(value: Label | None, *, family: str | None = None) -> TextStyle | None:
    """Convert the visual fields of a public label.

    Text content, anchor, offset, and visibility belong to the TextLayer and are
    intentionally handled by scene factories rather than this style converter.
    """
    if value is None and family is None:
        return None
    label = value or Label()
    return TextStyle(
        color=label.color,
        size=label.fontsize,
        family=family,
        opacity=label.opacity,
    )


def to_mosaic_theme(value: Any, *, font: str | None = None) -> MosaicTheme:
    """Compile a utility-viz Theme into its MosaicKit semantic role theme."""
    # Local import keeps the conversion module acyclic: theme.py builds the
    # default role pack, while this function adapts the compatibility object.
    from utility_viz.core.scenes.theme import UtilityColors, utility_theme

    colors = UtilityColors(
        ic_color=value.ic_color,
        ic_linewidth=value.ic_linewidth,
        secondary_ic_color=value.secondary_ic_color,
        secondary_ic_linewidth=value.secondary_ic_linewidth,
        secondary_ic_opacity=value.secondary_ic_opacity,
        budget_color=value.budget_color,
        budget_linewidth=value.budget_linewidth,
        budget_fill_alpha=value.budget_fill_alpha,
        compensated_budget_color=value.compensated_budget_color,
        compensated_budget_linewidth=value.compensated_budget_linewidth,
        eq_color=value.eq_color,
        eq_markersize=value.eq_markersize,
        ray_color=value.ray_color,
        ray_linewidth=value.ray_linewidth,
        drop_linewidth=value.drop_stroke.width or 0.8,
    )
    theme = utility_theme(colors, name=value.name)
    if font is None:
        return theme
    roles: dict[str, Any] = {}
    for name, bundle in theme.roles.items():
        text = bundle.text
        roles[name] = bundle if text is None else bundle.merged_over(type(bundle)(text=TextStyle(family=font)))
    return MosaicTheme(theme.name, roles)
