"""Stroke values compile into MosaicKit paths without renderer-owned state."""

from dataclasses import replace

import pytest
from mosaickit import ArrowStyle as MosaicArrowStyle
from mosaickit import DashStyle, PathLayer

from utility_viz import ArrowStyle, Canvas, Figure, Layout, LineStyle, Stroke, solve, themes
from utility_viz.core.diagrams.consumer.edgeworth import EdgeworthBox
from utility_viz.core.errors.exceptions import InvalidParameterError
from utility_viz.models.optimization import decompose_price_effect
from utility_viz.models.utility import CobbDouglas, Leontief

MODEL = CobbDouglas(0.5, 0.5)
EQ = solve(MODEL, px=2, py=3, income=30)
DEC = decompose_price_effect(MODEL, px=(2, 4), py=3, income=30)
DASHED = Stroke(width=2.5, style="dashed", color="#123456")


def _paths(canvas, text: str) -> list[PathLayer]:
    return [
        layer
        for layer in canvas.snapshot().ordered_layers
        if isinstance(layer, PathLayer) and (text in layer.id or text in layer.role)
    ]


def _assert_stroke(layer: PathLayer, expected: Stroke = DASHED):
    assert layer.stroke is not None
    assert layer.stroke.color is not None and not isinstance(layer.stroke.color, str)
    assert layer.stroke.width == pytest.approx(expected.width)
    assert layer.stroke.color.to_hex() == expected.color
    if expected.style is not None:
        assert layer.stroke.dash is not None
        assert layer.stroke.dash.value == expected.style.value


def test_stroke_value_normalization_and_validation():
    assert Stroke() == Stroke(width=None, style=None, color=None, arrow=None)
    stroke = Stroke(style="dotted", arrow="->")
    assert stroke.style is LineStyle.DOTTED and stroke.arrow is ArrowStyle.SIMPLE
    for kwargs in ({"width": 0}, {"width": -1}, {"style": "wavy"}, {"arrow": "<<"}):
        with pytest.raises(InvalidParameterError):
            Stroke(**kwargs)


def test_axis_strokes_are_scene_paths_and_figure_forwards_them():
    canvas = Canvas(axis_stroke=Stroke(width=1.6, style="dashed", color="#aa0000", arrow="wedge"))
    for axis in ("axes.x", "axes.y"):
        layer = _paths(canvas, axis)[0]
        assert layer.stroke.width == 1.6 and layer.stroke.dash is DashStyle.DASHED
        assert layer.stroke.color.to_hex().lower() == "#aa0000"
        assert layer.stroke.arrow is MosaicArrowStyle.WEDGE
    figure = Figure(Layout.SIDE_BY_SIDE, x_axis_stroke=Stroke(width=2))
    assert all(_paths(panel, "axes.x")[0].stroke.width == 2 for panel in figure.canvases)


def test_layer_strokes_and_explicit_object_precedence():
    canvas = (
        Canvas(x_max=20, y_max=15)
        .add_utility(MODEL, levels=[4], stroke=DASHED)
        .add_budget(2, 3, 30, color="red", linewidth=0.5, stroke=Stroke(width=3, color="#123456"))
        .add_ray(0.5, stroke=DASHED)
        .add_equilibrium(EQ, show_ray=True, drop_stroke=DASHED)
    )
    _assert_stroke(_paths(canvas, "utility.1")[0])
    budget = _paths(canvas, "budget")[0]
    assert budget.stroke.width == 3 and budget.stroke.color.to_hex() == "#123456"
    _assert_stroke(_paths(canvas, "ray")[0])
    _assert_stroke(_paths(canvas, "equilibrium.drop")[0])


def test_kink_rays_and_decomposition_strokes():
    rays = Canvas().add_utility(Leontief(1, 2), levels=[2, 4], show_rays=True, ray_stroke=DASHED)
    assert _paths(rays, "ray")
    _assert_stroke(_paths(rays, "ray")[0])
    canvas = Canvas(x_max=20, y_max=15).add_decomposition(
        DEC,
        original_budget_stroke=DASHED,
        compensated_budget_stroke=DASHED,
        final_budget_stroke=DASHED,
        substitution_stroke=DASHED,
        income_stroke=DASHED,
    )
    for name in ("budget.original", "budget.compensated", "budget.final", "effect.substitution", "effect.income"):
        _assert_stroke(_paths(canvas, name)[0])


@pytest.mark.parametrize("arrow", list(ArrowStyle))
def test_arrow_styles_reach_mosaickit_and_tikz(arrow, tmp_path):
    canvas = Canvas().add_budget(2, 3, 30, stroke=Stroke(arrow=arrow))
    assert _paths(canvas, "budget")[0].stroke.arrow is not None
    output = tmp_path / f"{arrow.name}.tex"
    canvas.save(output)
    assert "Stealth" in output.read_text(encoding="utf-8")


def test_no_arrow_by_default():
    assert _paths(Canvas().add_budget(2, 3, 30), "budget")[0].stroke.arrow is None


def test_custom_theme_and_edgeworth_frame_strokes():
    theme = replace(themes.default, axis_stroke=Stroke(width=1.4, style="dashed", arrow="->"))
    axis = _paths(Canvas(theme=theme), "axes.y")[0]
    assert axis.stroke.width == 1.4 and axis.stroke.dash is DashStyle.DASHED
    box = EdgeworthBox(MODEL, MODEL, total_x=10, total_y=10, box_stroke=DASHED)
    for name in ("box.bottom", "box.top", "box.left", "box.right"):
        _assert_stroke(_paths(box, name)[0])


def test_edgeworth_line_strokes():
    box = EdgeworthBox(MODEL, MODEL, total_x=10, total_y=10).add_endowment(7, 3)
    box.add_indifference_curves(levels_a=[3], levels_b=[3], stroke_a=DASHED, stroke_b=DASHED)
    box.add_contract_curve(stroke=DASHED).add_price_line(px=1, py=1, stroke=DASHED)
    for text in (".a.1", ".b.1", "contract", "price"):
        _assert_stroke(_paths(box, text)[0])
