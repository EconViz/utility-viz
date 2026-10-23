"""Label(top=, bottom=, left=, right=) moves one placed label; it becomes a mosaickit Nudge."""

import pytest
from mosaickit import TextLayer
from mosaickit.styles.nudge import Nudge

from utility_viz import Axis, Canvas, Config, Label, solve
from utility_viz.core.diagrams.consumer.edgeworth import EdgeworthBox
from utility_viz.core.errors.exceptions import InvalidParameterError
from utility_viz.core.scenes.styles import nudged, to_mosaic_nudge
from utility_viz.models.optimization import decompose_price_effect
from utility_viz.models.utility import CobbDouglas, Satiation

MODEL = CobbDouglas(0.5, 0.5)
EQ = solve(MODEL, px=2.0, py=3.0, income=30.0)


@pytest.fixture(autouse=True)
def _defaults():
    Config.reset()
    yield
    Config.reset()


def _texts(canvas):
    return {layer.id: layer for layer in canvas.snapshot().ordered_layers if isinstance(layer, TextLayer)}


def test_lengths_in_pt_em_and_mm():
    assert to_mosaic_nudge(Label(top="10pt")) == Nudge(0, 10)
    assert to_mosaic_nudge(Label(left=6)) == Nudge(-6, 0)
    assert to_mosaic_nudge(Label(right="0.5em", fontsize=14)) == Nudge(7, 0)
    assert to_mosaic_nudge(Label(bottom="1em")) == Nudge(0, -12)  # no font size: mosaickit's 12 pt
    assert to_mosaic_nudge(Label(top="2mm")).dy == pytest.approx(72 / 25.4 * 2)
    assert to_mosaic_nudge(Label(top=5, bottom=2, right=1, left=4)) == Nudge(-3, 3)


def test_no_nudge_keeps_the_layer():
    assert to_mosaic_nudge(None) is None
    assert to_mosaic_nudge(Label(fontsize=10)) is None
    layer = TextLayer((0, 0), "a")
    assert nudged(layer, Label()) is layer


@pytest.mark.parametrize("bad", ["10", "ten pt", "3px", True, [1]])
def test_bad_lengths_are_rejected(bad):
    with pytest.raises(InvalidParameterError, match="Label top"):
        Label(top=bad)


def test_equilibrium_label_moves_up():
    plain = _texts(Canvas().add_equilibrium(EQ))["equilibrium.label"]
    moved = _texts(Canvas().add_equilibrium(EQ, label=Label(top="10pt")))["equilibrium.label"]
    assert plain.nudge is None
    assert moved.nudge == Nudge(0, 10)
    assert (moved.offset, moved.anchor) == (plain.offset, plain.anchor)  # placed as before, then moved


def test_point_label_moves_left():
    layer = _texts(Canvas().add_point(5, 3, label=Label(text="A", left="6pt")))["point.label"]
    assert layer.text == "A" and layer.nudge == Nudge(-6, 0)


def test_other_labels_take_nudges():
    canvas = Canvas(x_axis=Axis(label=Label(text="x", right=3)), title=Label(text="T", top=2))
    texts = _texts(canvas)
    assert texts["axes.x.label"].nudge == Nudge(3, 0)
    assert texts["canvas.title"].nudge == Nudge(0, 2)
    bliss = _texts(Canvas(x_max=12, y_max=10).add_utility(Satiation(6, 4), levels=[-8], bliss_label=Label(top=4)))
    assert next(layer for key, layer in bliss.items() if key.endswith("bliss.label")).nudge == Nudge(0, 4)


def test_decomposition_bundle_labels_take_nudges():
    dec = decompose_price_effect(MODEL, px=(2.0, 4.0), py=3.0, income=60.0)
    texts = _texts(Canvas(x_max=40, y_max=27).add_decomposition(dec, point_label=Label(bottom=2)))
    bundles = [layer for key, layer in texts.items() if key.startswith("decomposition.bundle.")]
    assert len(bundles) == 3 and all(layer.nudge == Nudge(0, -2) for layer in bundles)


def test_edgeworth_point_labels_take_nudges():
    box = EdgeworthBox(MODEL, MODEL, 10, 10).add_endowment(7, 3, label=Label(text="e", left=2))
    layer = next(layer for layer in box.snapshot().ordered_layers if isinstance(layer, TextLayer) and layer.text == "e")
    assert layer.nudge == Nudge(-2, 0)
    frame = EdgeworthBox(MODEL, MODEL, 10, 10, x_axis=Axis(label=Label(text="x", top=1)), origin_label=Label(right=1))
    texts = {layer.id: layer for layer in frame.snapshot().ordered_layers if isinstance(layer, TextLayer)}
    assert texts["box.x_a"].nudge == Nudge(0, 1) and texts["box.origin_a"].nudge == Nudge(1, 0)


def test_toml_default_per_label_kind_and_own_value_wins_per_direction():
    Config.from_dict({"utility": {"label": {"point": {"top": "2pt", "right": 1}}}}).use()
    default = _texts(Canvas().add_point(1, 1, label="A"))["point.label"]
    assert default.nudge == Nudge(1, 2)
    own = _texts(Canvas().add_point(1, 1, label=Label(text="A", top="5pt")))["point.label"]
    assert own.nudge == Nudge(1, 5)  # top replaced, right kept


@pytest.mark.parametrize("value", ["0.5em", "x", True])
def test_toml_nudges_are_lengths_without_em(value):
    with pytest.raises(InvalidParameterError, match=r"\[utility.label.point\] top"):
        Config.from_dict({"utility": {"label": {"point": {"top": value}}}})


def test_nudge_changes_the_drawing(tmp_path):
    plain, moved = tmp_path / "plain.svg", tmp_path / "moved.svg"
    Canvas().add_point(5, 3, label="A").save(plain)
    Canvas().add_point(5, 3, label=Label(text="A", top="10pt")).save(moved)
    assert plain.read_bytes() != moved.read_bytes()
