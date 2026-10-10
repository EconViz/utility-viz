"""Price decomposition is expressed entirely as MosaicKit scene layers."""

from dataclasses import replace

import pytest
from mosaickit import ArrowPlacement, LegendLayer, MarkerLayer, PathLayer, TextLayer

from utility_viz import Canvas, Label, Stroke
from utility_viz.models.optimization import decompose_price_effect
from utility_viz.models.utility import CobbDouglas

MODEL = CobbDouglas(alpha=0.5, beta=0.5)


def _dec(method: str):
    return decompose_price_effect(MODEL, px=(2.0, 4.0), py=3.0, income=60.0, method=method)


def _layers(canvas: Canvas, prefix: str):
    return [layer for layer in canvas.snapshot().layers if layer.id.startswith(prefix)]


def test_result_keeps_the_function():
    dec = _dec("hicks")
    assert dec.func is MODEL
    assert "func" not in repr(dec)


def test_hicks_draws_two_distinct_utility_levels_and_three_budgets():
    canvas = Canvas(x_max=40, y_max=27).add_decomposition(_dec("hicks"))
    curve_ids = {layer.id.split(".")[2] for layer in _layers(canvas, "decomposition.curve.")}
    assert curve_ids == {"U0", "U1"}
    assert {layer.id for layer in _layers(canvas, "decomposition.budget.")} == {
        "decomposition.budget.original",
        "decomposition.budget.compensated",
        "decomposition.budget.final",
    }


def test_slutsky_adds_the_curve_through_b():
    canvas = Canvas(x_max=40, y_max=27).add_decomposition(_dec("slutsky"))
    curve_ids = {layer.id.split(".")[2] for layer in _layers(canvas, "decomposition.curve.")}
    assert curve_ids == {"U0", "UB", "U1"}


def test_show_curves_false_omits_curve_layers():
    canvas = Canvas(x_max=40, y_max=27).add_decomposition(_dec("slutsky"), show_curves=False)
    assert _layers(canvas, "decomposition.curve.") == []


def test_curve_stroke_and_labels_are_scene_properties():
    canvas = Canvas(x_max=40, y_max=27).add_decomposition(
        _dec("slutsky"),
        curve_stroke=Stroke(color="#123456", width=2.5, style="--"),
        curve_label=Label(position="top", color="#654321", text="ignored"),
    )
    curves = [layer for layer in _layers(canvas, "decomposition.curve.") if isinstance(layer, PathLayer)]
    labels = [layer for layer in _layers(canvas, "decomposition.curve.") if isinstance(layer, TextLayer)]
    assert curves
    assert all(layer.stroke.color.to_hex() == "#123456" and layer.stroke.width == 2.5 for layer in curves)
    assert {label.text for label in labels} == {"U_0", "U_B", "U_1"}
    assert all(label.style.color.to_hex() == "#654321" for label in labels)


def test_decomposition_without_function_skips_curves():
    canvas = Canvas(x_max=40, y_max=27).add_decomposition(replace(_dec("hicks"), func=None))
    assert _layers(canvas, "decomposition.curve.") == []


def test_effect_arrows_point_from_start_to_end():
    dec = _dec("hicks")
    canvas = Canvas(x_max=40, y_max=27).add_decomposition(dec)
    by_id = {layer.id: layer for layer in canvas.snapshot().layers}
    substitution = by_id["decomposition.effect.substitution"]
    income = by_id["decomposition.effect.income"]
    assert isinstance(substitution, PathLayer)
    assert tuple(substitution.path)[0] == pytest.approx((dec.A.x, dec.A.y))
    assert tuple(substitution.path)[1] == pytest.approx((dec.B.x, dec.B.y))
    assert tuple(income.path)[0] == pytest.approx((dec.B.x, dec.B.y))
    assert tuple(income.path)[1] == pytest.approx((dec.C.x, dec.C.y))
    assert substitution.arrow_placement is ArrowPlacement.END


def test_x_projection_mode_draws_guides_and_horizontal_ranges():
    dec = _dec("hicks")
    canvas = Canvas(x_max=40, y_max=27).add_decomposition(dec, show_x_projections=True)
    ranges = [layer for layer in _layers(canvas, "decomposition.range.") if isinstance(layer, PathLayer)]
    assert len(ranges) == 2
    assert tuple(ranges[0].path)[0][0] == pytest.approx(dec.A.x)
    assert tuple(ranges[0].path)[1][0] == pytest.approx(dec.B.x)
    assert tuple(ranges[1].path)[0][0] == pytest.approx(dec.B.x)
    assert tuple(ranges[1].path)[1][0] == pytest.approx(dec.C.x)
    assert len(_layers(canvas, "decomposition.projection.")) == 3


def test_zero_effect_draws_no_range_arrow():
    import numpy as np

    from utility_viz.models.utility import QuasiLinear

    dec = decompose_price_effect(
        QuasiLinear(v_func=lambda z: 4.0 * np.log(z), linear_in="y"), px=(2.0, 1.0), py=1.0, income=28.0, method="hicks"
    )
    canvas = Canvas(x_max=30, y_max=35).add_decomposition(dec, show_x_projections=True)
    assert len([layer for layer in _layers(canvas, "decomposition.range.") if isinstance(layer, PathLayer)]) == 1


def test_bundle_markers_labels_and_legend_are_mosaickit_layers():
    canvas = Canvas(x_max=40, y_max=27).add_decomposition(_dec("hicks"))
    layers = canvas.snapshot().layers
    assert isinstance(next(layer for layer in layers if layer.id == "decomposition.bundles"), MarkerLayer)
    assert {layer.text for layer in _layers(canvas, "decomposition.bundle.") if isinstance(layer, TextLayer)} == {
        "A",
        "B",
        "C",
    }
    assert any(isinstance(layer, LegendLayer) for layer in layers)
