"""Reusable scene component for an equilibrium annotation."""

from __future__ import annotations

from mosaickit import DashStyle, Marker, Stroke

from utility_viz.core.scenes.equilibrium import equilibrium_layers

_DASH = {"-": DashStyle.SOLID, "--": DashStyle.DASHED, ":": DashStyle.DOTTED, "-.": DashStyle.DASHDOT}


class EquilibriumPoint:
    def __init__(
        self,
        eq,
        color: str,
        markersize: float = 6.0,
        label: str | None = "x^*",
        drop_dashes: bool = True,
        show_ray: bool = False,
        ray_color: str | None = None,
        ray_linewidth: float = 0.8,
        marker_shape: str = "o",
        drop_linestyle: str = ":",
        ray_linestyle: str = "--",
    ) -> None:
        self.eq, self.color, self.markersize, self.label = eq, color, markersize, label
        self.drop_dashes, self.show_ray = drop_dashes, show_ray
        self.ray_color, self.ray_linewidth = ray_color or color, ray_linewidth
        self.marker_shape, self.drop_linestyle, self.ray_linestyle = marker_shape, drop_linestyle, ray_linestyle

    def layers(self, x_max: float, y_max: float):
        return equilibrium_layers(
            self.eq,
            label=self.label,
            drop_lines=self.drop_dashes,
            ray_to=(x_max, y_max) if self.show_ray else None,
            marker=Marker(color=self.color, size=self.markersize**2, shape=self.marker_shape),
            drop_stroke=Stroke(color=self.color, width=0.8, dash=_DASH[self.drop_linestyle]),
            ray_stroke=Stroke(
                color=self.ray_color,
                width=self.ray_linewidth,
                dash=_DASH[self.ray_linestyle],
            ),
        )

    def draw(self, canvas, x_max: float, y_max: float) -> None:
        canvas.extend(self.layers(x_max, y_max))
