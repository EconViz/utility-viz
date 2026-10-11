"""Reusable backend-neutral economic diagram components."""

from mosaickit import DashStyle, PathLayer, Stroke

from utility_viz.core.diagrams.components.budget import BudgetConstraint
from utility_viz.core.diagrams.components.equilibrium import EquilibriumPoint
from utility_viz.core.diagrams.components.indifference import IndifferenceCurves

__all__ = ["BudgetConstraint", "EquilibriumPoint", "IndifferenceCurves", "draw_ray"]


def draw_ray(canvas, slope, x_max, y_max, color, linewidth, linestyle="--"):
    """Append a clipped ray to a MosaicKit canvas and return its layer."""
    x_end, y_end = x_max, slope * x_max
    if y_end > y_max:
        y_end, x_end = y_max, y_max / slope
    dash = {"-": DashStyle.SOLID, "--": DashStyle.DASHED, ":": DashStyle.DOTTED, "-.": DashStyle.DASHDOT}
    layer = PathLayer(
        ((0.0, 0.0), (x_end, y_end)),
        stroke=Stroke(color=color, width=linewidth, dash=dash[linestyle]),
        role="utility.equilibrium.ray",
    )
    canvas.add(layer)
    return layer
