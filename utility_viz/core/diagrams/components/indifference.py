"""Reusable scene component for indifference curves."""

from __future__ import annotations

from mosaickit import Stroke

from utility_viz.core.scenes.indifference import indifference_layers


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
        return indifference_layers(
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
            legend=self.label,
        )

    def draw(self, canvas, x_max: float, y_max: float, **kwargs) -> list[float]:
        layers, levels = self.layers(x_max, y_max, **kwargs)
        canvas.extend(layers)
        return levels
