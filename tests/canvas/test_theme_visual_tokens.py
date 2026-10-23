"""Theme tokens reach the backend-neutral Edgeworth and utility layers."""

from dataclasses import replace

import numpy as np
from mosaickit import MarkerLayer, PathLayer

from utility_viz import Canvas, Config, Marker, themes
from utility_viz.core.diagrams.consumer.edgeworth import EdgeworthBox
from utility_viz.core.themes.theme import Theme
from utility_viz.models.utility import CobbDouglas, Satiation, StoneGeary

MODEL = CobbDouglas(0.5, 0.5)


def _box(theme=None):
    return EdgeworthBox(MODEL, MODEL, 10, 10, theme=theme)


def _layer(canvas, text, cls):
    return next(
        layer
        for layer in canvas.snapshot().ordered_layers
        if isinstance(layer, cls) and (text in layer.id or text in layer.role)
    )


def _core(box, *, min_points=1, **kwargs):
    box.add_endowment(7, 3)
    box.contract_curve_points = np.array([[6.0, 4.0], [7.0, 3.0], [8.0, 2.0]])
    return box.add_core(min_points=min_points, **kwargs)


def test_edgeworth_default_line_tokens():
    core = _layer(_core(_box()), "utility.edgeworth.core", PathLayer)
    assert (core.stroke.color.to_hex(), core.stroke.width) == ("#E41A1C", 3)  # accent
    price = _layer(_box().add_endowment(7, 3).add_price_line(1, 1), "price", PathLayer)
    assert (price.stroke.color.to_hex(), price.stroke.width, price.stroke.dash.value) == ("#999999", 1.2, "dashed")
    contract = _layer(_box().add_contract_curve(), "contract", PathLayer)
    assert (contract.stroke.color.to_hex(), contract.stroke.width, contract.stroke.dash.value) == (
        "#999999",  # muted
        1.2,
        "dashed",
    )


def test_edgeworth_default_marker_tokens():
    box = _box().add_endowment(7, 3).add_walrasian_equilibrium(1, 1)
    endowment = _layer(box, "endowment", MarkerLayer)
    walrasian = _layer(box, "walrasian", MarkerLayer)
    assert endowment.marker.size == 6**2
    assert (walrasian.marker.color.to_hex(), walrasian.marker.size, walrasian.marker.shape) == (
        "#E41A1C",
        10**2,
        "*",
    )  # accent


def test_bliss_and_subsistence_default_tokens():
    bliss = _layer(Canvas(x_max=12, y_max=10).add_utility(Satiation(6, 4), levels=[-8]), "bliss", MarkerLayer)
    assert bliss.marker.size == 12**2
    model = StoneGeary(bar_x=1, bar_y=1)
    canvas = Canvas(x_max=20, y_max=15).add_utility(model, levels=[1, 2])
    lines = [layer for layer in canvas.snapshot().ordered_layers if layer.role == "utility.indifference.subsistence"]
    assert len(lines) == 2
    assert all((line.stroke.color.to_hex(), line.stroke.width) == ("#999999", 0.8) for line in lines)  # muted


def test_custom_theme_propagates_to_lines_and_markers():
    theme = replace(
        themes.default,
        core_color="#00FF00",
        core_linewidth=5,
        price_color="#FF00FF",
        price_linewidth=4,
        walrasian_color="#654321",
        walrasian_markersize=20,
    )
    box = _core(_box(theme))
    box.add_price_line(1, 1).add_walrasian_equilibrium(1, 1)
    core = _layer(box, "core", PathLayer)
    price = _layer(box, "price", PathLayer)
    walrasian = _layer(box, "walrasian", MarkerLayer)
    assert (core.stroke.color.to_hex(), core.stroke.width) == ("#00FF00", 5)
    assert (price.stroke.color.to_hex(), price.stroke.width) == ("#FF00FF", 4)
    assert (walrasian.marker.color.to_hex(), walrasian.marker.size) == ("#654321", 20**2)


def test_custom_bliss_and_subsistence_tokens():
    class BigBliss(Theme):
        @property
        def bliss_marker(self):
            return Marker(size=25, shape="*")

    bliss = _layer(Canvas(theme=BigBliss("big")).add_utility(Satiation(), levels=[-8]), "bliss", MarkerLayer)
    assert bliss.marker.size == 25**2
    theme = replace(themes.default, subsistence_color="#ABCDEF", subsistence_linewidth=2.5)
    canvas = Canvas(theme=theme).add_utility(StoneGeary(), levels=[1])
    lines = [layer for layer in canvas.snapshot().ordered_layers if layer.role.endswith("subsistence")]
    assert all((line.stroke.color.to_hex(), line.stroke.width) == ("#ABCDEF", 2.5) for line in lines)


def test_explicit_arguments_beat_theme():
    core = _layer(_core(_box(), color="#101010"), "core", PathLayer)
    assert core.stroke.color.to_hex() == "#101010"
    box = _box().add_endowment(7, 3).add_walrasian_equilibrium(1, 1, marker="D")
    assert _layer(box, "walrasian", MarkerLayer).marker.shape == "D"


def test_config_overrides_reach_scene_roles():
    config = Config.from_dict(
        {
            "utility": {
                "stroke": {"core": {"color": "#0F0F0F"}, "subsistence": {"color": "#00AA00"}},
                "marker": {"walrasian": {"color": "#ABABAB"}},
            }
        }
    )
    box = _core(_box(config.theme)).add_walrasian_equilibrium(1, 1)
    assert _layer(box, "core", PathLayer).stroke.color.to_hex() == "#0F0F0F"
    assert _layer(box, "walrasian", MarkerLayer).marker.color.to_hex() == "#ABABAB"
    canvas = Canvas(theme=config.theme).add_utility(StoneGeary(), levels=[1])
    assert all(
        layer.stroke.color.to_hex() == "#00AA00"
        for layer in canvas.snapshot().ordered_layers
        if layer.role.endswith("subsistence")
    )
