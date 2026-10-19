"""Decomposition Effect values compile into semantic scene layers."""

import pytest
from mosaickit import PathLayer, TextLayer

from utility_viz import Canvas, Effect, Label, Stroke
from utility_viz.core.errors.exceptions import InvalidParameterError
from utility_viz.models.optimization import decompose_price_effect
from utility_viz.models.utility import CobbDouglas

DEC = decompose_price_effect(CobbDouglas(), px=(2, 4), py=3, income=30)


def _canvas(**kwargs):
    return Canvas(x_max=20, y_max=15).add_decomposition(DEC, **kwargs)


def _layer(canvas, layer_id):
    return next(layer for layer in canvas.snapshot().layers if layer.id == layer_id)


def test_effect_validates_position_and_opacity():
    with pytest.raises(InvalidParameterError):
        Effect(label_position="middle")
    with pytest.raises(InvalidParameterError):
        Effect(opacity=2)


def test_effect_colors_and_stroke_precedence():
    canvas = _canvas(
        substitution=Effect(color="#123456"),
        income=Effect(color="#654321"),
        substitution_stroke=Stroke(color="#abcdef"),
    )
    assert _layer(canvas, "decomposition.effect.substitution").stroke.color.to_hex() == "#ABCDEF"
    assert _layer(canvas, "decomposition.effect.income").stroke.color.to_hex() == "#654321"


def test_range_height_and_direction_are_scene_coordinates():
    canvas = _canvas(
        show_x_projections=True,
        substitution=Effect(y=-0.06),
        income=Effect(y=-0.30),
    )
    substitution = _layer(canvas, "decomposition.range.substitution")
    income = _layer(canvas, "decomposition.range.income")
    assert isinstance(substitution, PathLayer)
    assert substitution.path[0][1] == pytest.approx(-0.9)
    assert income.path[0][1] == pytest.approx(-4.5)
    assert substitution.path[0][0] == pytest.approx(DEC.A.x)
    assert substitution.path[1][0] == pytest.approx(DEC.B.x)


@pytest.mark.parametrize("projections", [False, True])
def test_effect_labels_exist_in_both_modes(projections):
    canvas = _canvas(
        show_x_projections=projections,
        substitution=Effect(label=Label(text="Substitution", color="#123456")),
        income=Effect(label="Income"),
    )
    labels = [layer for layer in canvas.snapshot().layers if isinstance(layer, TextLayer)]
    assert {layer.text for layer in labels} >= {"Substitution", "Income"}
    substitution = next(layer for layer in labels if layer.text == "Substitution")
    assert substitution.style.color.to_hex() == "#123456"


def test_effect_labels_export_to_tikz(tmp_path):
    target = tmp_path / "effects.tex"
    _canvas(show_x_projections=True, substitution=Effect(label="Substitution")).save(target)
    assert "Substitution" in target.read_text(encoding="utf-8")
