"""Axis value and scene compilation tests."""

import pytest
from mosaickit import PathLayer, TextLayer

from utility_viz import Axis, Canvas, DemandDiagram, Figure, Layout, LinearBudget, PricePath, Stroke
from utility_viz.core.diagrams.consumer.edgeworth import EdgeworthBox
from utility_viz.core.errors.exceptions import InvalidParameterError
from utility_viz.enums import ArrowStyle, LabelPosition, LineStyle
from utility_viz.models.utility import CobbDouglas

MODEL = CobbDouglas()


def _layer(canvas, layer_id):
    return next(layer for layer in canvas.snapshot().layers if layer.id == layer_id)


def test_axis_defaults_and_validation():
    assert (Axis().label, Axis().label_position, Axis().stroke) == (None, None, None)
    assert Axis(label_position="bottom").label_position is LabelPosition.BOTTOM
    with pytest.raises(InvalidParameterError):
        Axis(label_position="middle")


def test_axis_object_matches_shorthand_and_compiles_to_layers():
    plain = Canvas(x_label="q", x_label_pos="bottom", x_axis_stroke=Stroke(width=2))
    same = Canvas(x_axis=Axis(label="q", label_position="bottom", stroke=Stroke(width=2)))
    assert (plain.x_label, plain.x_label_pos, plain.x_axis_stroke) == (
        same.x_label,
        same.x_label_pos,
        same.x_axis_stroke,
    )
    assert isinstance(_layer(same, "axes.x.label"), TextLayer)
    assert _layer(same, "axes.x.label").text == "q"
    assert _layer(same, "axes.x").stroke.width == 2


def test_axis_style_precedence():
    canvas = Canvas(
        x_line_style="dotted",
        x_arrow_style="-|>",
        axis_stroke=Stroke(width=1, color="#111111", style="--"),
        x_axis_stroke=Stroke(width=2, color="#222222"),
        x_axis=Axis(stroke=Stroke(width=3)),
    )
    stroke = canvas.x_axis_stroke
    assert (stroke.width, stroke.color, stroke.style, stroke.arrow) == (
        3,
        "#222222",
        LineStyle.DASHED,
        ArrowStyle.TRIANGLE,
    )
    compiled = _layer(canvas, "axes.x")
    assert isinstance(compiled, PathLayer)
    assert compiled.stroke.color.to_hex() == "#222222"


def test_axis_customization_is_forwarded_to_figure_and_demand():
    figure = Figure(Layout.SIDE_BY_SIDE, x_axis=Axis(label="q", stroke=Stroke(width=2.5)))
    assert all(canvas.x_label == "q" and canvas.x_axis_stroke.width == 2.5 for canvas in figure.canvases)
    path = PricePath(MODEL, LinearBudget(2, 2, 40), price="px", price_range=(1, 4), n=5)
    demand = DemandDiagram(path, x_axis=Axis(label="x_1", stroke=Stroke(width=2.5)))
    assert demand.utility_canvas.x_label == "x_1"
    assert demand.demand_canvas.x_axis_stroke.width == 2.5


def test_edgeworth_axis_styles_compile_to_box_sides():
    box = EdgeworthBox(
        MODEL,
        MODEL,
        10,
        10,
        x_axis=Axis(label="f", stroke=Stroke(width=3, color="#123456")),
    )
    assert box.x_label == "f"
    for layer_id in ("box.bottom", "box.top"):
        layer = _layer(box, layer_id)
        assert layer.stroke.width == 3
        assert layer.stroke.color.to_hex() == "#123456"


def test_edgeworth_rejects_axis_label_position():
    with pytest.raises(InvalidParameterError):
        EdgeworthBox(MODEL, MODEL, 10, 10, y_axis=Axis(label_position="top"))
