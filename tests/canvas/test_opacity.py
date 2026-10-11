"""Opacity travels from compatibility styles into MosaicKit scene styles."""

import pytest
from mosaickit import FillLayer, MarkerLayer, PathLayer, TextLayer

from utility_viz import Canvas, Effect, Fill, Label, Legend, Marker, Stroke, solve
from utility_viz.core.errors.exceptions import InvalidParameterError
from utility_viz.models.optimization import decompose_price_effect
from utility_viz.models.utility import CobbDouglas

MODEL = CobbDouglas(0.5, 0.5)
EQ = solve(MODEL, px=2, py=3, income=30)
DEC = decompose_price_effect(MODEL, px=(2, 4), py=3, income=30)


def _layer(canvas, suffix: str, cls):
    return next(
        layer for layer in canvas.snapshot().ordered_layers if isinstance(layer, cls) and layer.id.endswith(suffix)
    )


@pytest.mark.parametrize("cls", [Stroke, Marker, Label, Legend, Effect, Fill])
@pytest.mark.parametrize("value", [-0.1, 1.2])
def test_rejects_out_of_range_opacity(cls, value):
    with pytest.raises(InvalidParameterError):
        cls(opacity=value)


@pytest.mark.parametrize("cls", [Stroke, Marker, Label, Legend, Fill])
def test_merge_preserves_or_overrides_opacity(cls):
    assert cls().merged_over(cls(opacity=0.3)).opacity == 0.3
    assert cls(opacity=0.7).merged_over(cls(opacity=0.3)).opacity == 0.7


def test_stroke_marker_text_and_fill_opacity():
    canvas = Canvas(x_max=20, y_max=15)
    canvas.add_budget(2, 3, 30, stroke=Stroke(opacity=0.4), fill=Fill(opacity=0.25))
    canvas.add_equilibrium(EQ, marker=Marker(opacity=0.6), label=Label(opacity=0.5))
    assert _layer(canvas, "budget", PathLayer).stroke.opacity == 0.4
    assert _layer(canvas, "budget.fill", FillLayer).fill.opacity == 0.25
    assert _layer(canvas, "equilibrium", MarkerLayer).marker.opacity == 0.6
    assert _layer(canvas, "equilibrium.label", TextLayer).style.opacity == 0.5


def test_curve_and_effect_opacity():
    curve = _layer(
        Canvas(x_max=20, y_max=15).add_utility(MODEL, levels=[3], stroke=Stroke(opacity=0.5)),
        "utility.1",
        PathLayer,
    )
    assert curve.stroke.opacity == 0.5
    canvas = Canvas(x_max=20, y_max=15).add_decomposition(
        DEC, income=Effect(opacity=0.4, label=Label(text="IE", opacity=0.9))
    )
    assert _layer(canvas, "effect.income", PathLayer).stroke.opacity == 0.4
    assert _layer(canvas, "effect.income.label", TextLayer).style.opacity == 0.9


def test_opacity_reaches_tikz(tmp_path):
    output = tmp_path / "opacity.tex"
    Canvas().add_budget(2, 3, 30, stroke=Stroke(opacity=0.4)).add_point(1, 1, label=Label(text="A", opacity=0.35)).save(
        output
    )
    source = output.read_text(encoding="utf-8")
    assert "opacity=0.4" in source
    assert "text opacity=0.35" in source
