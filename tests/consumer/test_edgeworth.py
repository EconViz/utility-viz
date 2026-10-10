"""Edgeworth economics and its backend-neutral scene representation."""

import numpy as np
import pytest
from mosaickit import Canvas as MosaicCanvas
from mosaickit import MarkerLayer, PathLayer, TextLayer

from utility_viz import EdgeworthBox, EquilibriumFocusConfig, Stroke
from utility_viz.models.utility import CobbDouglas, PerfectSubstitutes


def _box(**kwargs):
    return EdgeworthBox(CobbDouglas(), CobbDouglas(), total_x=10.0, total_y=10.0, **kwargs)


def _layers(box, prefix):
    return [layer for layer in box.snapshot().layers if layer.id.startswith(prefix)]


def test_invalid_totals_raise():
    with pytest.raises(ValueError, match="positive"):
        EdgeworthBox(CobbDouglas(), CobbDouglas(), total_x=0.0, total_y=10.0)


def test_edgeworth_box_is_a_mosaickit_scene_without_renderer_objects():
    box = _box(title="Exchange")
    assert isinstance(box, MosaicCanvas)
    assert not hasattr(box, "ax") and not hasattr(box, "fig")
    assert {layer.id for layer in box.snapshot().layers} >= {
        "box.bottom",
        "box.top",
        "box.left",
        "box.right",
        "box.origin_a",
        "box.origin_b",
    }


def test_indifference_endowment_and_save(tmp_path):
    box = _box().add_indifference_curves(levels_a=3, levels_b=3).add_endowment(4.0, 3.0)
    box.add_endowment_indifference()
    target = tmp_path / "edgeworth.png"
    box.save(target)
    assert target.read_bytes().startswith(b"\x89PNG")
    assert len(_layers(box, "indifference")) >= 8
    assert any(isinstance(layer, MarkerLayer) for layer in _layers(box, "endowment"))
    assert any(isinstance(layer, TextLayer) and layer.text == "e" for layer in _layers(box, "endowment"))


def test_custom_utility_colors_live_on_curve_layers():
    box = _box(utility_a_color="#ff006e", utility_b_color="#3a86ff")
    box.add_indifference_curves(levels_a=2, levels_b=2)
    colors = {
        layer.stroke.color.to_hex()
        for layer in _layers(box, "indifference")
        if isinstance(layer, PathLayer) and layer.stroke and layer.stroke.color
    }
    assert {"#FF006E", "#3A86FF"} <= colors


def test_contract_curve_and_price_line_are_scene_paths():
    box = _box().add_endowment(4.0, 6.0).add_contract_curve(n=70, method="mrs").add_price_line(1.0, 1.0)
    assert isinstance(_layers(box, "contract")[0], PathLayer)
    assert isinstance(_layers(box, "price")[0], PathLayer)
    assert _layers(box, "contract")[0].legend == "Contract curve"
    assert _layers(box, "price")[0].legend == "Price line"


def test_custom_contract_stroke_is_preserved():
    box = _box().add_contract_curve(stroke=Stroke(color="#123456", width=2.5, style="dashed"))
    layer = _layers(box, "contract")[0]
    assert layer.stroke.color.to_hex() == "#123456"
    assert layer.stroke.width == 2.5


def test_walrasian_equilibrium_and_equilibrium_curves():
    box = _box()
    box.add_endowment(4.0, 6.0).add_contract_curve(n=80).add_walrasian_equilibrium(1.0, 1.0)
    before = len(box.snapshot().layers)
    box.add_equilibrium_indifference(px=1.0, py=1.0)
    assert box.walrasian_equilibrium is not None
    assert len(box.snapshot().layers) > before
    assert any(isinstance(layer, MarkerLayer) for layer in _layers(box, "walrasian"))


def test_equilibrium_focus_keeps_three_to_five_levels_per_agent():
    box = EdgeworthBox(
        CobbDouglas(alpha=0.8, beta=0.2),
        CobbDouglas(alpha=0.2, beta=0.8),
        total_x=12.0,
        total_y=10.0,
    )
    box.add_endowment(5.0, 4.0).add_contract_curve(n=80).add_walrasian_equilibrium(1.2, 1.0)
    box.apply_equilibrium_focus(
        px=1.2,
        py=1.0,
        config=EquilibriumFocusConfig(
            include_endowment_indifference=True,
            min_curves_per_agent=3,
            max_curves_per_agent=5,
        ),
    )
    assert 3 <= len(box.equilibrium_focus_levels_a) <= 5
    assert 3 <= len(box.equilibrium_focus_levels_b) <= 5


def test_symmetric_cobb_douglas_contract_curve_near_diagonal():
    box = _box().add_contract_curve(n=70, method="mrs")
    assert len(box.contract_curve_points) > 10
    assert np.median(np.abs(box.contract_curve_points[:, 1] - box.contract_curve_points[:, 0])) < 0.6


def test_asymmetric_cobb_douglas_contract_curve_is_skewed():
    box = EdgeworthBox(
        CobbDouglas(alpha=0.8, beta=0.2),
        CobbDouglas(alpha=0.2, beta=0.8),
        total_x=10.0,
        total_y=10.0,
    ).add_contract_curve(n=80, method="mrs")
    assert len(box.contract_curve_points) > 8
    assert float(np.median(box.contract_curve_points[:, 1])) < 4.5


def test_perfect_substitutes_contract_curve_hits_boundaries():
    box = EdgeworthBox(PerfectSubstitutes(), PerfectSubstitutes(), total_x=10.0, total_y=10.0).add_contract_curve(
        n=50, method="pareto"
    )
    points = box.contract_curve_points
    assert len(points) >= 2
    assert np.any(
        np.isclose(points[:, 0], 0.0, atol=0.2)
        | np.isclose(points[:, 0], 10.0, atol=0.2)
        | np.isclose(points[:, 1], 0.0, atol=0.2)
        | np.isclose(points[:, 1], 10.0, atol=0.2)
    )


def test_core_and_allocation_checks_keep_numeric_behavior():
    box = _box().add_endowment(4.0, 6.0).add_contract_curve(n=80).add_core()
    assert len(box.core_points) > 0
    result = box.check_point(5.0, 5.0, px=1.0, py=1.0)
    assert set(result) == {"market_clearing", "individual_rationality", "budget_balance", "mrs_equal"}
    assert all(result.values())


def test_invalid_operations_keep_clear_errors():
    box = _box()
    with pytest.raises(ValueError, match="Endowment"):
        box.add_price_line(1.0, 1.0)
    with pytest.raises(ValueError, match="Endowment"):
        box.add_endowment_indifference()
    with pytest.raises(ValueError, match="inside"):
        box.add_endowment(11.0, 2.0)
