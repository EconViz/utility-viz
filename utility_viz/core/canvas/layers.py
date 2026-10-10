"""Fluent utility-specific MosaicKit layer composition."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from mosaickit import LegendLayer, LegendStyle, MarkerLayer, PathLayer, TextLayer

from utility_viz.core.scenes import budget_layers, equilibrium_layers, indifference_layers
from utility_viz.core.scenes.styles import (
    to_mosaic_fill,
    to_mosaic_marker,
    to_mosaic_stroke,
    to_mosaic_text,
)
from utility_viz.core.styles.fill import Fill
from utility_viz.core.styles.label import Label, split_label
from utility_viz.core.styles.legend import Legend
from utility_viz.core.styles.marker import Marker
from utility_viz.core.styles.stroke import Stroke
from utility_viz.enums import LineStyle

if TYPE_CHECKING:
    from typing_extensions import Self


class LayerMixin:
    legacy_theme: Any
    font: str | None
    x_max: float
    y_max: float
    add: Any
    extend: Any
    _next_id: Any

    def add_utility(
        self,
        func: Callable,
        levels: int | list = 3,
        color: str | None = None,
        linewidth: float | None = None,
        show_rays: bool = False,
        show_kinks: bool = False,
        kink_radius: float = 1.0,
        show_bliss: bool = True,
        label: str | None = None,
        show_ic_labels: bool = False,
        ic_label_fmt: str = "{:.2g}",
        stroke: Stroke | None = None,
        ray_stroke: Stroke | None = None,
        kink_marker: Marker | None = None,
        bliss_marker: Marker | None = None,
        ic_label: Label | None = None,
        bliss_label: str | Label | None = None,
        highlight_level: float | None = None,
        secondary_stroke: Stroke | None = None,
        label_style: str = "numeric",
        **kwargs,
    ) -> Self:
        if kwargs:
            names = ", ".join(sorted(kwargs))
            raise TypeError(f"Matplotlib-specific add_utility options are unsupported: {names}")
        theme = self.legacy_theme
        selected = (stroke or Stroke()).merged_over(theme.ic_stroke)
        selected = Stroke(color=color, width=linewidth).merged_over(selected)
        layer_id = self._next_id("utility")
        layers, _ = indifference_layers(
            func,
            levels,
            self.x_max,
            self.y_max,
            layer_id=layer_id,
            highlight_level=highlight_level,
            show_labels=show_ic_labels or ic_label is not None,
            label_fmt=(ic_label.text if ic_label and ic_label.text else ic_label_fmt),
            label_style=label_style,
            stroke=to_mosaic_stroke(selected),
            legend=label,
        )
        self.extend(layers)
        _ = (
            show_rays,
            show_kinks,
            kink_radius,
            show_bliss,
            ray_stroke,
            kink_marker,
            bliss_marker,
            bliss_label,
            secondary_stroke,
        )
        return self

    def add_budget(
        self,
        px: float,
        py: float,
        income: float,
        color: str | None = None,
        linewidth: float | None = None,
        linestyle: str | None = None,
        label: str | None = None,
        fill: bool | Fill = False,
        fill_alpha: float | None = None,
        stroke: Stroke | None = None,
    ) -> Self:
        theme = self.legacy_theme
        selected = (stroke or Stroke()).merged_over(theme.budget_stroke)
        selected = Stroke(
            color=color,
            width=linewidth,
            style=LineStyle(linestyle) if linestyle is not None else None,
        ).merged_over(selected)
        shade = fill if isinstance(fill, Fill) else Fill(opacity=fill_alpha)
        shade = shade.merged_over(theme.budget_fill)
        self.extend(
            budget_layers(
                px,
                py,
                income,
                layer_id=self._next_id("budget"),
                fill=fill is not False,
                label=label,
                stroke=to_mosaic_stroke(selected),
                fill_style=to_mosaic_fill(shade),
                legend=label,
            )
        )
        return self

    def add_equilibrium(
        self,
        eq,
        color: str | None = None,
        markersize: float | None = None,
        label: str | Label | None = "x^*",
        drop_dashes: bool = True,
        show_ray: bool = False,
        drop_stroke: Stroke | None = None,
        ray_stroke: Stroke | None = None,
        marker: Marker | None = None,
    ) -> Self:
        theme = self.legacy_theme
        text, label_style = split_label(label, theme.point_label, "x^*")
        selected_marker = (marker or Marker()).merged_over(theme.eq_marker)
        selected_marker = Marker(color=color, size=markersize).merged_over(selected_marker)
        layers = list(
            equilibrium_layers(
                eq,
                layer_id=self._next_id("equilibrium"),
                label=text,
                drop_lines=drop_dashes,
                ray_to=(self.x_max, self.y_max) if show_ray else None,
                marker=to_mosaic_marker(selected_marker),
                drop_stroke=to_mosaic_stroke((drop_stroke or Stroke()).merged_over(theme.drop_stroke)),
                ray_stroke=to_mosaic_stroke((ray_stroke or Stroke()).merged_over(theme.ray_stroke)),
            )
        )
        if text:
            for index, layer in enumerate(layers):
                if isinstance(layer, TextLayer):
                    layers[index] = TextLayer(
                        layer.position,
                        layer.text,
                        id=layer.id,
                        role=layer.role,
                        style=to_mosaic_text(label_style, family=self.font),
                        offset=layer.offset,
                        anchor=layer.anchor,
                        math=layer.math,
                        z_index=layer.z_index,
                    )
        self.extend(layers)
        return self

    def add_ray(
        self,
        slope: float,
        color: str | None = None,
        linewidth: float | None = None,
        stroke: Stroke | None = None,
    ) -> Self:
        if not math.isfinite(slope) or slope < 0:
            raise ValueError("slope must be finite and non-negative")
        end = (
            (self.x_max, min(self.y_max, slope * self.x_max))
            if slope <= self.y_max / self.x_max
            else (self.y_max / slope, self.y_max)
        )
        selected = (stroke or Stroke()).merged_over(self.legacy_theme.ray_stroke)
        selected = Stroke(color=color, width=linewidth).merged_over(selected)
        self.add(
            PathLayer(
                ((0, 0), end),
                id=self._next_id("ray"),
                role="utility.equilibrium.ray",
                stroke=to_mosaic_stroke(selected),
            )
        )
        return self

    def add_point(
        self,
        x: float,
        y: float,
        label: str | Label | None = None,
        color: str | None = None,
        markersize: float | None = None,
        offset: tuple[float, float] | None = None,
        marker: Marker | None = None,
    ) -> Self:
        prefix = self._next_id("point")
        selected = (marker or Marker()).merged_over(self.legacy_theme.point_marker)
        selected = Marker(color=color, size=markersize).merged_over(selected)
        self.add(
            MarkerLayer(
                ((x, y),),
                id=prefix,
                role="utility.equilibrium",
                marker=to_mosaic_marker(selected),
                z_index=6,
            )
        )
        text, style = split_label(label, self.legacy_theme.point_label)
        if text and style.visible is not False:
            self.add(
                TextLayer(
                    (x, y),
                    text,
                    id=f"{prefix}.label",
                    role="utility.equilibrium",
                    style=to_mosaic_text(style, family=self.font),
                    offset=offset or (5, 5),
                    anchor="bottom-left",
                    math=True,
                    z_index=7,
                )
            )
        return self

    def add_path(
        self,
        path,
        color: str | None = None,
        linewidth: float | None = None,
        label: str | None = None,
        show_points: bool | None = None,
        show_budgets: bool | None = None,
        show_curves: bool = False,
        show_equilibria: bool = False,
        invert_axes: bool = False,
        smooth_curve: bool | None = None,
        stroke: Stroke | None = None,
        budget_stroke: Stroke | None = None,
        curve_stroke: Stroke | None = None,
        point_marker: Marker | None = None,
        equilibrium_marker: Marker | None = None,
    ) -> Self:
        prefix = self._next_id("path")
        points = (
            tuple(zip(path.parameter_values, path.quantity_values("x"), strict=True))
            if invert_axes
            else tuple(zip(path.x_values, path.y_values, strict=True))
        )
        selected = (stroke or Stroke()).merged_over(self.legacy_theme.path_stroke)
        selected = Stroke(color=color, width=linewidth).merged_over(selected)
        self.add(
            PathLayer(
                points,
                id=prefix,
                role="utility.path",
                stroke=to_mosaic_stroke(selected),
                legend=label,
                model=path,
                z_index=4,
            )
        )
        show_points = path.default_show_points if show_points is None else show_points
        show_budgets = path.default_show_budgets if show_budgets is None else show_budgets
        if show_points or show_equilibria:
            chosen = equilibrium_marker if show_equilibria else point_marker
            fallback = self.legacy_theme.eq_marker if show_equilibria else self.legacy_theme.path_marker
            self.add(
                MarkerLayer(
                    points,
                    id=f"{prefix}.points",
                    role="utility.equilibrium" if show_equilibria else "utility.path",
                    marker=to_mosaic_marker((chosen or Marker()).merged_over(fallback)),
                    z_index=5,
                )
            )
        if show_budgets:
            for index, budget in enumerate(path.budgets, 1):
                self.extend(
                    budget_layers(
                        budget.px,
                        budget.py,
                        budget.income,
                        layer_id=f"{prefix}.budget.{index}",
                        stroke=to_mosaic_stroke(
                            (budget_stroke or Stroke()).merged_over(self.legacy_theme.budget_stroke)
                        ),
                    )
                )
        if show_curves:
            for index, eq in enumerate(path.equilibria, 1):
                layers, _ = indifference_layers(
                    path.func,
                    [eq.utility],
                    self.x_max,
                    self.y_max,
                    layer_id=f"{prefix}.curve.{index}",
                    stroke=to_mosaic_stroke((curve_stroke or Stroke()).merged_over(self.legacy_theme.ic_stroke)),
                )
                self.extend(layers)
        _ = smooth_curve
        return self

    def show_legend(self, legend: Legend | None = None, **kwargs) -> Self:
        if kwargs:
            names = ", ".join(sorted(kwargs))
            raise TypeError(f"Matplotlib-specific legend options are unsupported: {names}")
        selected = (legend or Legend()).merged_over(self.legacy_theme.legend)
        if selected.visible is False:
            return self
        self.add(
            LegendLayer(
                id=self._next_id("legend"),
                style=LegendStyle(
                    visible=selected.visible,
                    location=(
                        str(getattr(selected.position, "value", selected.position))
                        if selected.position is not None
                        else None
                    ),
                    frame=selected.frame,
                    size=selected.fontsize,
                ),
            )
        )
        return self
