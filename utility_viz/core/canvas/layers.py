"""Fluent utility-specific MosaicKit layer composition."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from mosaickit import LegendLayer, LegendStyle, MarkerLayer, PathLayer, TextLayer

from utility_viz.core.scenes import budget_layers, decomposition_layers, equilibrium_layers, indifference_layers
from utility_viz.core.scenes.path import smooth_path
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
from utility_viz.core.styles.placement import placement
from utility_viz.core.styles.stroke import Stroke
from utility_viz.enums import LabelPosition, LineStyle, UtilityType

if TYPE_CHECKING:
    from typing_extensions import Self


_LEGEND_LOCATIONS = {
    "auto": "best",
    "top": "upper center",
    "bottom": "lower center",
    "left": "center left",
    "right": "center right",
}


class LayerMixin:
    legacy_theme: Any
    font: str | None
    x_max: float
    y_max: float
    add: Any
    extend: Any
    _next_id: Any

    def add_decomposition(
        self,
        decomposition,
        *,
        show_arrows: bool = True,
        label_effects: bool = True,
        show_x_projections: bool = False,
        point_color: str | None = None,
        point_markersize: float | None = None,
        original_budget_color: str | None = None,
        original_budget_linewidth: float | None = None,
        original_budget_linestyle: str | None = None,
        compensated_budget_color: str | None = None,
        compensated_budget_linewidth: float | None = None,
        compensated_budget_linestyle: str | None = None,
        final_budget_color: str | None = None,
        final_budget_linewidth: float | None = None,
        final_budget_linestyle: str | None = None,
        substitution_color: str | None = None,
        income_color: str | None = None,
        effect_arrow_linewidth: float | None = None,
        original_budget_stroke: Stroke | None = None,
        compensated_budget_stroke: Stroke | None = None,
        final_budget_stroke: Stroke | None = None,
        substitution_stroke: Stroke | None = None,
        income_stroke: Stroke | None = None,
        projection_stroke: Stroke | None = None,
        guide_stroke: Stroke | None = None,
        range_stroke: Stroke | None = None,
        substitution=None,
        income=None,
        point_marker: Marker | None = None,
        point_label: Label | None = None,
        show_curves: bool = True,
        curve_stroke: Stroke | None = None,
        curve_label: Label | None = None,
        legend: Legend | None = None,
    ) -> Self:
        """Add a Hicks/Slutsky decomposition as backend-neutral layers."""
        theme = self.legacy_theme
        budget_specs = (
            (
                original_budget_stroke,
                theme.budget_stroke,
                original_budget_color,
                original_budget_linewidth,
                original_budget_linestyle,
            ),
            (
                compensated_budget_stroke,
                theme.compensated_budget_stroke,
                compensated_budget_color,
                compensated_budget_linewidth,
                compensated_budget_linestyle,
            ),
            (
                final_budget_stroke,
                theme.final_budget_stroke,
                final_budget_color,
                final_budget_linewidth,
                final_budget_linestyle,
            ),
        )
        budgets = []
        for explicit, fallback, color, width, style in budget_specs:
            selected = (explicit or Stroke()).merged_over(fallback)
            selected = Stroke(color=color, width=width, style=LineStyle(style) if style else None).merged_over(selected)
            budgets.append(to_mosaic_stroke(selected))

        marker = (point_marker or Marker()).merged_over(theme.eq_marker)
        marker = Marker(color=point_color, size=point_markersize).merged_over(marker)
        _, bundle_label = split_label(point_label, theme.bundle_label)
        bundle_offset, bundle_anchor = _label_placement(bundle_label)
        sub = Stroke(
            color=getattr(substitution, "color", None) or substitution_color,
            width=effect_arrow_linewidth,
            opacity=getattr(substitution, "opacity", None),
            arrow="->",
        ).merged_over(theme.substitution_stroke)
        sub = (substitution_stroke or Stroke()).merged_over(sub)
        inc = Stroke(
            color=getattr(income, "color", None) or income_color,
            width=effect_arrow_linewidth,
            opacity=getattr(income, "opacity", None),
            arrow="->",
        ).merged_over(theme.income_stroke)
        inc = (income_stroke or Stroke()).merged_over(inc)
        projection_selected = (projection_stroke or Stroke()).merged_over(theme.projection_stroke)
        guide_selected = (guide_stroke or Stroke()).merged_over(theme.guide_stroke)
        range_sub = (range_stroke or Stroke()).merged_over(sub)
        range_inc = (range_stroke or Stroke()).merged_over(inc)
        substitution_label = (
            substitution.resolved_label(theme.effect_label) if substitution is not None else (None, None)
        )
        income_label = income.resolved_label(theme.effect_label) if income is not None else (None, None)

        def effect_label(value):
            text, style = value
            style = style or theme.effect_label
            offset, anchor = _label_placement(style)
            return (
                text,
                to_mosaic_text(style, font=self.font),
                offset,
                anchor,
                style.visible is not False,
            )

        self.extend(
            decomposition_layers(
                decomposition,
                y_max=self.y_max,
                budget_strokes=budgets,
                bundle_marker=to_mosaic_marker(marker),
                bundle_text=to_mosaic_text(bundle_label, font=self.font),
                bundle_text_offset=bundle_offset,
                bundle_text_anchor=bundle_anchor,
                bundle_text_visible=bundle_label.visible is not False,
                substitution_stroke=to_mosaic_stroke(sub),
                income_stroke=to_mosaic_stroke(inc),
                projection_stroke=to_mosaic_stroke(projection_selected),
                guide_stroke=to_mosaic_stroke(guide_selected),
                range_strokes=(to_mosaic_stroke(range_sub), to_mosaic_stroke(range_inc)),
                substitution_label=effect_label(substitution_label),
                income_label=effect_label(income_label),
                range_y=(getattr(substitution, "y", None), getattr(income, "y", None)),
                show_arrows=show_arrows,
                show_x_projections=show_x_projections,
                label_effects=label_effects,
            )
        )

        if show_curves and decomposition.func is not None:
            selected = (curve_stroke or Stroke()).merged_over(theme.ic_stroke)
            levels: list[tuple[str, float]] = [
                ("U0", float(decomposition.A.utility)),
                ("U1", float(decomposition.C.utility)),
            ]
            if not math.isclose(decomposition.B.utility, decomposition.A.utility, rel_tol=1e-9, abs_tol=1e-12):
                levels.insert(1, ("UB", float(decomposition.B.utility)))
            names = {"U0": "U_0", "UB": "U_B", "U1": "U_1"}
            for key, level in levels:
                layers, _ = indifference_layers(
                    decomposition.func,
                    [level],
                    self.x_max,
                    self.y_max,
                    layer_id=f"decomposition.curve.{key}",
                    show_labels=curve_label is not None,
                    label_fmt=names[key],
                    stroke=to_mosaic_stroke(selected),
                    z_index=1,
                )
                if curve_label is not None:
                    _, label_style = split_label(curve_label, theme.ic_label)
                    layers = tuple(
                        TextLayer(
                            layer.position,
                            layer.text,
                            id=layer.id,
                            role=layer.role,
                            style=to_mosaic_text(label_style, font=self.font),
                            offset=layer.offset,
                            anchor=layer.anchor,
                            math=True,
                            z_index=layer.z_index,
                        )
                        if isinstance(layer, TextLayer)
                        else layer
                        for layer in layers
                    )
                self.extend(layers)
        if label_effects:
            self.show_legend(legend)
        return self

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
        res: int = 100,
        resolution: tuple[int, int] = (161, 161),
        tolerance: float = 0.005,
        **kwargs,
    ) -> Self:
        if kwargs:
            names = ", ".join(sorted(kwargs))
            raise TypeError(f"renderer-specific add_utility options are unsupported: {names}")
        theme = self.legacy_theme
        selected = Stroke(color=color, width=linewidth).merged_over(theme.ic_stroke)
        selected = (stroke or Stroke()).merged_over(selected)
        layer_id = self._next_id("utility")
        layers, computed = indifference_layers(
            func,
            levels,
            self.x_max,
            self.y_max,
            layer_id=layer_id,
            highlight_level=highlight_level,
            show_labels=show_ic_labels or ic_label is not None,
            label_fmt=(ic_label.text if ic_label and ic_label.text else ic_label_fmt),
            label_style=label_style,
            res=res,
            resolution=resolution,
            tolerance=tolerance,
            stroke=to_mosaic_stroke(selected),
            secondary_stroke=to_mosaic_stroke((secondary_stroke or Stroke()).merged_over(theme.secondary_ic_stroke)),
            legend=label,
        )
        if ic_label is not None:
            _, ic_style = split_label(ic_label, theme.ic_label)
            layers = tuple(_restyle_text(layer, ic_style, self.font) for layer in layers)
        self.extend(layers)
        _add_kink_features(self, func, computed, layer_id, show_rays, show_kinks, kink_radius, ray_stroke, kink_marker)
        _add_subsistence_lines(self, func, layer_id)
        _add_bliss_point(self, func, layer_id, show_bliss, selected, bliss_marker, bliss_label)
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
        selected = Stroke(
            color=color,
            width=linewidth,
            style=LineStyle(linestyle) if linestyle is not None else None,
        ).merged_over(theme.budget_stroke)
        selected = (stroke or Stroke()).merged_over(selected)
        shade = fill if isinstance(fill, Fill) else Fill(opacity=fill_alpha)
        shade = shade.merged_over(theme.budget_fill)
        layers = budget_layers(
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
        self.extend(layers)
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
        selected_marker = Marker(color=color, size=markersize).merged_over(theme.eq_marker)
        selected_marker = (marker or Marker()).merged_over(selected_marker)
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
                    if label_style.color is None and selected_marker.color is not None:
                        label_style = Label(color=selected_marker.color).merged_over(label_style)
                    layers[index] = _restyle_text(layer, label_style, self.font)
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
        selected = Stroke(color=color, width=linewidth).merged_over(self.legacy_theme.ray_stroke)
        selected = (stroke or Stroke()).merged_over(selected)
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
        selected = Marker(color=color, size=markersize).merged_over(self.legacy_theme.point_marker)
        selected = (marker or Marker()).merged_over(selected)
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
        if text:
            if style.color is None and selected.color is not None:
                style = Label(color=selected.color).merged_over(style)
            label_offset, anchor = _label_placement(style, legacy_offset=offset)
            self.add(
                TextLayer(
                    (x, y),
                    text,
                    id=f"{prefix}.label",
                    role="utility.equilibrium",
                    style=to_mosaic_text(style, font=self.font),
                    offset=label_offset,
                    anchor=anchor,
                    math=True,
                    visible=style.visible is not False,
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
        use_smoothing = path.default_smooth_curve if smooth_curve is None else smooth_curve
        rendered_points, bezier = smooth_path(points) if use_smoothing else (list(points), None)
        selected = Stroke(color=color, width=linewidth).merged_over(self.legacy_theme.path_stroke)
        selected = (stroke or Stroke()).merged_over(selected)
        self.add(
            PathLayer(
                rendered_points,
                id=prefix,
                role="utility.path",
                stroke=to_mosaic_stroke(selected),
                legend=label,
                model=bezier or path,
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
        return self

    def show_legend(self, legend: Legend | None = None, **kwargs) -> Self:
        if kwargs:
            names = ", ".join(sorted(kwargs))
            raise TypeError(f"renderer-specific legend options are unsupported: {names}")
        selected = (legend or Legend()).merged_over(self.legacy_theme.legend)
        if selected.visible is False:
            return self
        self.add(
            LegendLayer(
                id=self._next_id("legend"),
                style=LegendStyle(
                    visible=selected.visible,
                    location=_mosaic_legend_location(selected.position),
                    frame=selected.frame,
                    size=selected.fontsize,
                ),
            )
        )
        return self


def _add_kink_features(
    canvas: Any,
    func: Any,
    levels: list[float],
    layer_id: str,
    show_rays: bool,
    show_kinks: bool,
    kink_radius: float,
    ray_stroke: Stroke | None,
    kink_marker: Marker | None,
) -> None:
    if getattr(func, "utility_type", None) is not UtilityType.KINKED:
        return
    if show_rays:
        for slope in func.ray_slopes():
            canvas.add_ray(slope, stroke=ray_stroke)
    if not show_kinks:
        return
    chosen = (kink_marker or Marker()).merged_over(canvas.legacy_theme.kink_marker)
    if kink_marker is None:
        chosen = Marker(size=4 * kink_radius).merged_over(chosen)
    points = tuple((float(x), float(y)) for x, y in func.kink_points(levels))
    if points:
        canvas.add(
            MarkerLayer(
                points,
                marker=to_mosaic_marker(chosen),
                id=f"{layer_id}.kinks",
                role="utility.indifference.kink",
                z_index=5,
            )
        )


def _add_subsistence_lines(canvas: Any, func: Any, layer_id: str) -> None:
    if not hasattr(func, "subsistence_lines"):
        return
    sub_x, sub_y = func.subsistence_lines()
    stroke = to_mosaic_stroke(canvas.legacy_theme.subsistence_stroke)
    canvas.add(
        PathLayer(
            ((sub_x, 0), (sub_x, canvas.y_max)),
            stroke=stroke,
            id=f"{layer_id}.subsistence.x",
            role="utility.indifference.subsistence",
            z_index=0,
        )
    )
    canvas.add(
        PathLayer(
            ((0, sub_y), (canvas.x_max, sub_y)),
            stroke=stroke,
            id=f"{layer_id}.subsistence.y",
            role="utility.indifference.subsistence",
            z_index=0,
        )
    )


def _add_bliss_point(
    canvas: Any,
    func: Any,
    layer_id: str,
    show_bliss: bool,
    curve_stroke: Stroke,
    bliss_marker: Marker | None,
    bliss_label: str | Label | None,
) -> None:
    if not show_bliss or not hasattr(func, "bliss_x") or not hasattr(func, "bliss_y"):
        return
    chosen = (bliss_marker or Marker()).merged_over(canvas.legacy_theme.bliss_marker)
    if chosen.color is None:
        chosen = Marker(color=curve_stroke.color).merged_over(chosen)
    canvas.add(
        MarkerLayer(
            ((func.bliss_x, func.bliss_y),),
            marker=to_mosaic_marker(chosen),
            id=f"{layer_id}.bliss",
            role="utility.indifference.bliss",
            z_index=5,
        )
    )
    text, style = split_label(bliss_label, canvas.legacy_theme.bliss_label, canvas.legacy_theme.bliss_label.text)
    if not text:
        return
    offset, anchor = _label_placement(style)
    if style.color is None and chosen.color is not None:
        style = Label(color=chosen.color).merged_over(style)
    canvas.add(
        TextLayer(
            (func.bliss_x, func.bliss_y),
            text,
            style=to_mosaic_text(style, font=canvas.font),
            offset=offset,
            anchor=anchor,
            math=True,
            visible=style.visible is not False,
            id=f"{layer_id}.bliss.label",
            role="utility.indifference.bliss.label",
            z_index=6,
        )
    )


def _mosaic_legend_location(position: Any) -> str | None:
    """Translate utility-viz placement names to MosaicKit renderer locations."""
    if position is None:
        return None
    value = str(getattr(position, "value", position))
    return _LEGEND_LOCATIONS.get(value, value)


def _label_placement(
    style: Label, *, legacy_offset: tuple[float, float] | None = None
) -> tuple[tuple[float, float], str]:
    """Translate the public point-label placement to MosaicKit's offset/anchor pair."""
    if style.position is None and legacy_offset is not None:
        dx, dy = legacy_offset
        horizontal = "left" if dx >= 0 else "right"
        vertical = "bottom" if dy >= 0 else "top"
        return legacy_offset, f"{vertical}-{horizontal}"
    position = LabelPosition(style.position or LabelPosition.TOP_RIGHT)
    offset, horizontal, vertical = placement(position, style.offset or 5)
    anchor = "-".join(part for part in (vertical, horizontal) if part != "center") or "center"
    return offset, anchor


def _restyle_text(layer, style: Label, font: str | None):
    if not isinstance(layer, TextLayer):
        return layer
    offset, anchor = _label_placement(style)
    return TextLayer(
        layer.position,
        layer.text,
        id=layer.id,
        role=layer.role,
        style=to_mosaic_text(style, font=font),
        offset=offset,
        anchor=anchor,
        math=layer.math,
        visible=style.visible is not False,
        z_index=layer.z_index,
    )
