"""Reusable scene component for a linear budget constraint."""

from __future__ import annotations

from mosaickit import DashStyle, Fill, Stroke

from utility_viz.core.errors.exceptions import InvalidParameterError
from utility_viz.core.scenes.budget import budget_layers

_DASH = {"-": DashStyle.SOLID, "--": DashStyle.DASHED, ":": DashStyle.DOTTED, "-.": DashStyle.DASHDOT}


class BudgetConstraint:
    def __init__(
        self,
        px: float,
        py: float,
        income: float,
        color: str,
        linewidth: float,
        linestyle: str = "-",
        label: str | None = None,
        fill: bool = False,
        fill_alpha: float = 0.08,
        fill_color: str | None = None,
    ) -> None:
        if px <= 0 or py <= 0 or income <= 0:
            raise InvalidParameterError(f"Budget parameters must be positive (px={px}, py={py}, income={income}).")
        self.px, self.py, self.income = px, py, income
        self.color, self.linewidth, self.linestyle = color, linewidth, linestyle
        self.label, self.fill, self.fill_alpha, self.fill_color = label, fill, fill_alpha, fill_color

    def layers(self):
        return budget_layers(
            self.px,
            self.py,
            self.income,
            fill=self.fill,
            stroke=Stroke(color=self.color, width=self.linewidth, dash=_DASH[self.linestyle]),
            fill_style=Fill(color=self.fill_color or self.color, opacity=self.fill_alpha),
            legend=self.label,
        )

    def draw(self, canvas) -> None:
        """Compatibility spelling: append this component to a MosaicKit canvas."""
        canvas.extend(self.layers())
