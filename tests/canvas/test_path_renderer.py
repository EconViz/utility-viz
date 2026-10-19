"""Behavioral tests for consumption-path rendering branches."""

import pytest
from mosaickit import LegendLayer, MarkerLayer, PathLayer

from utility_viz import Canvas
from utility_viz.models.consumer.paths import LinearBudget, PricePath
from utility_viz.models.utility import CobbDouglas


@pytest.fixture()
def price_path():
    return PricePath(
        CobbDouglas(),
        budget=LinearBudget(px=2.0, py=2.0, income=40.0),
        price="px",
        price_range=(1.0, 3.0),
        n=3,
    )


def test_path_can_render_curves_budgets_equilibria_and_legend(price_path):
    canvas = Canvas(x_max=25, y_max=25)

    canvas.add_path(
        price_path,
        label="PCC",
        show_curves=True,
        show_budgets=True,
        show_equilibria=True,
        smooth_curve=True,
    ).show_legend()

    layers = canvas.snapshot().ordered_layers
    assert any(isinstance(layer, LegendLayer) for layer in layers)
    assert any(isinstance(layer, PathLayer) and layer.id.startswith("path.curve") for layer in layers)
    assert len([layer for layer in layers if isinstance(layer, PathLayer) and ".budget." in layer.id]) == 3
    assert (
        len(next(layer for layer in layers if isinstance(layer, MarkerLayer) and layer.id == "path.points").points) == 3
    )


def test_inverted_path_can_render_raw_points(price_path):
    canvas = Canvas(x_max=25, y_max=25)

    canvas.add_path(
        price_path,
        show_points=True,
        show_budgets=False,
        show_curves=False,
        show_equilibria=False,
        invert_axes=True,
        smooth_curve=False,
    )

    points = next(layer for layer in canvas.snapshot().ordered_layers if isinstance(layer, MarkerLayer))
    assert len(points.points) == len(price_path.equilibria)
    assert points.points[0][0] == pytest.approx(price_path.parameter_values[0])
