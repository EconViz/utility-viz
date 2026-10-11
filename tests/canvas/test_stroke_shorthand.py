"""Legacy line shorthands compile to the same scene stroke as Stroke."""

import pytest
from mosaickit import PathLayer

from utility_viz import Canvas, Stroke
from utility_viz.models.optimization import decompose_price_effect
from utility_viz.models.utility import CobbDouglas

MODEL = CobbDouglas(0.5, 0.5)
DEC = decompose_price_effect(MODEL, px=(2, 4), py=3, income=30)
COLOR, WIDTH = "#123456", 2.2


def _look(canvas, text):
    layer = next(
        layer
        for layer in canvas.snapshot().ordered_layers
        if isinstance(layer, PathLayer) and (text in layer.id or text in layer.role)
    )
    stroke = layer.stroke
    return stroke.color.to_hex(), stroke.width, stroke.dash


CASES = [
    (
        "utility.1",
        lambda: Canvas().add_utility(MODEL, levels=[3], color=COLOR, linewidth=WIDTH),
        lambda: Canvas().add_utility(MODEL, levels=[3], stroke=Stroke(color=COLOR, width=WIDTH)),
    ),
    (
        "budget",
        lambda: Canvas().add_budget(2, 3, 30, color=COLOR, linewidth=WIDTH, linestyle="--"),
        lambda: Canvas().add_budget(2, 3, 30, stroke=Stroke(color=COLOR, width=WIDTH, style="--")),
    ),
    (
        "ray",
        lambda: Canvas().add_ray(0.5, color=COLOR, linewidth=WIDTH),
        lambda: Canvas().add_ray(0.5, stroke=Stroke(color=COLOR, width=WIDTH)),
    ),
    (
        "budget.original",
        lambda: Canvas(x_max=20, y_max=15).add_decomposition(
            DEC, original_budget_color=COLOR, original_budget_linewidth=WIDTH, original_budget_linestyle=":"
        ),
        lambda: Canvas(x_max=20, y_max=15).add_decomposition(
            DEC, original_budget_stroke=Stroke(color=COLOR, width=WIDTH, style=":")
        ),
    ),
    (
        "effect.income",
        lambda: Canvas(x_max=20, y_max=15).add_decomposition(DEC, income_color=COLOR, effect_arrow_linewidth=WIDTH),
        lambda: Canvas(x_max=20, y_max=15).add_decomposition(DEC, income_stroke=Stroke(color=COLOR, width=WIDTH)),
    ),
]


@pytest.mark.parametrize("role,shorthand,styled", CASES)
def test_shorthand_matches_stroke(role, shorthand, styled):
    assert _look(shorthand(), role) == _look(styled(), role)
