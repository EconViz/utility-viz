"""Core Canvas behavior at the scene boundary."""

import pytest
from mosaickit import ArrowPlacement, FillLayer, MarkerLayer, PathLayer, TextLayer

from utility_viz import ArrowStyle, Canvas, LabelPosition, LineStyle
from utility_viz.core.diagrams.components import BudgetConstraint, EquilibriumPoint, IndifferenceCurves, draw_ray
from utility_viz.core.errors.exceptions import InvalidParameterError
from utility_viz.models.optimization import decompose_price_effect, solve
from utility_viz.models.utility import CobbDouglas

MODEL = CobbDouglas()


def _by_id(canvas):
    return {layer.id: layer for layer in canvas.snapshot().layers}


def test_canvas_owns_scene_spec_not_renderer_objects():
    canvas = Canvas(x_max=15, y_max=12)
    assert canvas.spec.x_range == (0.0, 15.0)
    assert canvas.spec.y_range == (0.0, 12.0)
    assert not hasattr(canvas, "fig") and not hasattr(canvas, "ax")


def test_invalid_ranges_and_renderer_injection_are_rejected():
    with pytest.raises(InvalidParameterError):
        Canvas(x_max=0)
    with pytest.raises(InvalidParameterError, match="injection"):
        Canvas(ax=object())


@pytest.mark.parametrize("position", list(LabelPosition))
def test_axis_label_positions_are_scene_offsets(position):
    valid_x = position in {LabelPosition.TOP, LabelPosition.RIGHT, LabelPosition.BOTTOM}
    if not valid_x:
        with pytest.raises(ValueError):
            Canvas(x_label_pos=position)
        return
    label = _by_id(Canvas(x_label="Q", x_label_pos=position))["axes.x.label"]
    assert isinstance(label, TextLayer)
    assert label.text == "Q" and label.offset != (0, 0)


@pytest.mark.parametrize("arrow", list(ArrowStyle))
def test_axis_arrow_style_is_compiled_into_mosaickit_stroke(arrow):
    canvas = Canvas(x_arrow_style=arrow)
    axis = _by_id(canvas)["axes.x"]
    assert isinstance(axis, PathLayer)
    assert axis.arrow_placement is ArrowPlacement.END
    assert axis.stroke.arrow is not None


@pytest.mark.parametrize("style", list(LineStyle))
def test_axis_dash_style_is_compiled_into_mosaickit_stroke(style):
    axis = _by_id(Canvas(x_line_style=style))["axes.x"]
    assert axis.stroke.dash.value == style.value


def test_fluent_economic_layers_have_semantic_roles():
    equilibrium = solve(MODEL, px=2, py=3, income=30)
    canvas = Canvas(x_max=20, y_max=15)
    canvas.add_utility(MODEL, levels=[3, 5]).add_budget(2, 3, 30, fill=True).add_equilibrium(equilibrium)
    layers = canvas.snapshot().layers
    assert any(layer.role == "utility.indifference" for layer in layers)
    assert any(layer.role == "utility.budget" for layer in layers)
    assert any(isinstance(layer, FillLayer) for layer in layers)
    assert any(isinstance(layer, MarkerLayer) and layer.role == "utility.equilibrium" for layer in layers)


def test_decomposition_bundle_labels_are_scene_text():
    decomposition = decompose_price_effect(MODEL, px=(2, 4), py=3, income=60)
    canvas = Canvas(x_max=35, y_max=25).add_decomposition(decomposition, show_arrows=False)
    labels = {layer.text for layer in canvas.snapshot().layers if layer.id.startswith("decomposition.bundle.")}
    assert labels == {"A", "B", "C"}


def test_public_components_append_mosaickit_layers():
    canvas = Canvas(x_max=20, y_max=15)
    levels = IndifferenceCurves(MODEL, levels=2, color="black", linewidth=1).draw(canvas, 20, 15)
    BudgetConstraint(2, 3, 30, color="blue", linewidth=1.5, fill=True).draw(canvas)
    equilibrium = solve(MODEL, px=2, py=3, income=30)
    EquilibriumPoint(equilibrium, color="red", show_ray=True).draw(canvas, 20, 15)
    ray = draw_ray(canvas, 0.5, 20, 15, "black", 1)
    assert len(levels) == 2
    assert isinstance(ray, PathLayer)
    assert all(isinstance(layer, (PathLayer, FillLayer, MarkerLayer, TextLayer)) for layer in canvas.snapshot().layers)


def test_canvas_tikz_can_write_an_embeddable_picture(tmp_path):
    output = tmp_path / "embedded.tex"
    Canvas().add_budget(2, 3, 30).save(output, tikz_standalone=False)

    source = output.read_text(encoding="utf-8")
    assert source.startswith("\\definecolor")
    assert "\\begin{tikzpicture}" in source
    assert "\\documentclass" not in source
