"""Reusable scene component for indifference curves."""

from __future__ import annotations

from dataclasses import replace

from mosaickit import DashStyle, MarkerLayer, PathLayer, Stroke
from mosaickit import Marker as MosaicMarker

from utility_viz.core.constants.canvas import CONTOUR_DOMAIN_MIN
from utility_viz.core.scenes.indifference import indifference_layers
from utility_viz.core.styles.marker import Marker
from utility_viz.core.styles.stroke import Stroke as PublicStroke
from utility_viz.enums import UtilityType
from utility_viz.models.curves import Layer as ContourGrid
from utility_viz.models.curves import percentile_levels


class IndifferenceCurves:
    def __init__(
        self,
        func,
        levels,
        color: str,
        linewidth: float,
        show_rays: bool = False,
        ray_color: str = "black",
        ray_linewidth: float = 0.8,
        show_kinks: bool = False,
        kink_color: str = "black",
        kink_radius: float = 1.0,
        label: str | None = None,
        show_ic_labels: bool = False,
        ic_label_fmt: str = "{:.2g}",
        subsistence_color: str = "gray",
        subsistence_linewidth: float = 0.8,
        highlight_level: float | None = None,
        secondary_color: str = "gray",
        secondary_linewidth: float = 1.0,
        secondary_opacity: float = 0.45,
        label_style: str = "numeric",
    ) -> None:
        self.func, self.levels, self.color, self.linewidth = func, levels, color, linewidth
        self.label, self.show_ic_labels, self.ic_label_fmt = label, show_ic_labels, ic_label_fmt
        self.highlight_level, self.label_style = highlight_level, label_style
        self.show_rays, self.show_kinks = show_rays, show_kinks
        self.ray_color, self.ray_linewidth = ray_color, ray_linewidth
        self.kink_color, self.kink_radius = kink_color, kink_radius
        self.subsistence_color, self.subsistence_linewidth = subsistence_color, subsistence_linewidth
        self.secondary_color, self.secondary_linewidth, self.secondary_opacity = (
            secondary_color,
            secondary_linewidth,
            secondary_opacity,
        )

    def layers(self, x_max: float, y_max: float, **kwargs):
        supported = {"res", "resolution", "tolerance"}
        unknown = sorted(set(kwargs) - supported)
        if unknown:
            raise TypeError(f"renderer-specific indifference options are unsupported: {', '.join(unknown)}")
        layers, computed = indifference_layers(
            self.func,
            self.levels,
            x_max,
            y_max,
            res=int(kwargs.pop("res", 100)),
            highlight_level=self.highlight_level,
            show_labels=self.show_ic_labels,
            label_fmt=self.ic_label_fmt,
            label_style=self.label_style,
            stroke=Stroke(color=self.color, width=self.linewidth),
            secondary_stroke=Stroke(
                color=self.secondary_color,
                width=self.secondary_linewidth,
                opacity=self.secondary_opacity,
            ),
            legend=self.label,
            **kwargs,
        )
        return (*layers, *self._decoration_layers(computed, x_max, y_max)), computed

    def _decoration_layers(self, levels: list[float], x_max: float, y_max: float) -> tuple:
        layers: list = []
        if getattr(self.func, "utility_type", None) is UtilityType.KINKED:
            if self.show_rays:
                for index, slope in enumerate(self.func.ray_slopes(), 1):
                    end = (x_max, min(y_max, slope * x_max)) if slope <= y_max / x_max else (y_max / slope, y_max)
                    layers.append(
                        PathLayer(
                            ((0, 0), end),
                            id=f"utility.ray.{index}",
                            role="utility.equilibrium.ray",
                            stroke=Stroke(
                                color=self.ray_color,
                                width=self.ray_linewidth,
                                dash=DashStyle.DASHED,
                            ),
                        )
                    )
            if self.show_kinks:
                points = tuple(self.func.kink_points(levels))
                if points:
                    layers.append(
                        MarkerLayer(
                            points,
                            id="utility.kinks",
                            role="utility.indifference.kink",
                            marker=MosaicMarker(
                                color=self.kink_color,
                                size=(4 * self.kink_radius) ** 2,
                            ),
                        )
                    )
        if hasattr(self.func, "subsistence_lines"):
            sub_x, sub_y = self.func.subsistence_lines()
            stroke = Stroke(
                color=self.subsistence_color,
                width=self.subsistence_linewidth,
                dash=DashStyle.DASHED,
                opacity=0.6,
            )
            layers.extend(
                (
                    PathLayer(
                        ((sub_x, 0), (sub_x, y_max)),
                        id="utility.subsistence.x",
                        role="utility.indifference.subsistence",
                        stroke=stroke,
                    ),
                    PathLayer(
                        ((0, sub_y), (x_max, sub_y)),
                        id="utility.subsistence.y",
                        role="utility.indifference.subsistence",
                        stroke=stroke,
                    ),
                )
            )
        return tuple(layers)

    def draw(self, canvas, x_max: float, y_max: float, **kwargs) -> list[float]:
        supported = {"res", "resolution", "tolerance"}
        unknown = sorted(set(kwargs) - supported)
        if unknown:
            raise TypeError(f"renderer-specific indifference options are unsupported: {', '.join(unknown)}")
        before = {layer.id for layer in canvas.snapshot().layers}
        canvas.add_utility(
            self.func,
            levels=self.levels,
            color=self.color,
            linewidth=self.linewidth,
            show_rays=self.show_rays,
            show_kinks=self.show_kinks,
            kink_radius=self.kink_radius,
            label=self.label,
            show_ic_labels=self.show_ic_labels,
            ic_label_fmt=self.ic_label_fmt,
            ray_stroke=PublicStroke(color=self.ray_color, width=self.ray_linewidth, style="dashed"),
            kink_marker=Marker(color=self.kink_color, size=4 * self.kink_radius),
            highlight_level=self.highlight_level,
            secondary_stroke=PublicStroke(
                color=self.secondary_color,
                width=self.secondary_linewidth,
                opacity=self.secondary_opacity,
            ),
            label_style=self.label_style,
            **kwargs,
        )
        self._restyle_subsistence(canvas, before)
        return self._computed_levels(x_max, y_max, res=int(kwargs.get("res", 100)))

    def _computed_levels(self, x_max: float, y_max: float, *, res: int) -> list[float]:
        if not isinstance(self.levels, int):
            return list(self.levels)
        _, _, values = ContourGrid.compute_contour(
            self.func,
            (CONTOUR_DOMAIN_MIN, x_max),
            (CONTOUR_DOMAIN_MIN, y_max),
            res=res,
        )
        return percentile_levels(values, n=self.levels)

    def _restyle_subsistence(self, canvas, before: set[str]) -> None:
        stroke = Stroke(color=self.subsistence_color, width=self.subsistence_linewidth)
        for layer in tuple(canvas.snapshot().layers):
            if layer.id in before or not isinstance(layer, PathLayer) or "subsistence" not in layer.id:
                continue
            canvas.remove(layer.id)
            canvas.add(replace(layer, stroke=stroke))
