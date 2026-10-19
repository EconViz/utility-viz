"""Canvas, effect, and Edgeworth text is represented by MosaicKit layers."""

from mosaickit import TextLayer

from utility_viz import Axis, Canvas, Effect, Label
from utility_viz.core.diagrams.consumer.edgeworth import EdgeworthBox
from utility_viz.enums import LabelPosition
from utility_viz.models.optimization import decompose_price_effect
from utility_viz.models.utility import CobbDouglas

MODEL = CobbDouglas(0.5, 0.5)
DEC = decompose_price_effect(MODEL, px=(2, 4), py=3, income=30)


def _text(canvas, layer_id):
    return next(
        layer for layer in canvas.snapshot().ordered_layers if isinstance(layer, TextLayer) and layer.id == layer_id
    )


def test_canvas_axis_origin_and_title_labels():
    canvas = Canvas(
        x_axis=Axis(label=Label(text="x_1", fontsize=18, color="#123456", offset=16)),
        origin_label=Label(text="O", fontsize=8, color="#654321"),
        title=Label(text="Hicks", fontsize=20, color="#112233"),
    )
    x_label = _text(canvas, "axes.x.label")
    assert (x_label.text, x_label.style.size, x_label.style.color.to_hex(), x_label.offset) == (
        "x_1",
        18,
        "#123456",
        (16, 0),
    )
    origin = _text(canvas, "axes.origin.label")
    assert (origin.text, origin.style.size, origin.style.color.to_hex()) == ("O", 8, "#654321")
    title = _text(canvas, "canvas.title")
    assert (title.text, title.style.size, title.style.color.to_hex()) == ("Hicks", 20, "#112233")


def test_axis_label_positions_and_visibility():
    canvas = Canvas(y_axis=Axis(label=Label(text="q", position="right")))
    assert canvas.y_label_pos is LabelPosition.RIGHT
    hidden = Canvas(y_axis=Axis(label=Label(visible=False)))
    assert not any(layer.id == "axes.y.label" for layer in hidden.snapshot().ordered_layers)


def test_effect_label_style_position_and_visibility():
    canvas = Canvas(x_max=20, y_max=15).add_decomposition(
        DEC,
        substitution=Effect(label=Label(text="SE", fontsize=13, color="#123456", position="top", offset=9)),
        income=Effect(label=Label(text="IE", visible=False)),
    )
    substitution = _text(canvas, "decomposition.effect.substitution.label")
    assert (substitution.text, substitution.style.size, substitution.style.color.to_hex()) == ("SE", 13, "#123456")
    assert (substitution.offset, substitution.anchor) == ((0, 9), "bottom")
    assert _text(canvas, "decomposition.effect.income.label").visible is False


def test_effect_shorthand_resolution():
    text, style = Effect(label="IE", label_position="left", label_offset=7).resolved_label(Label())
    assert (text, style.position, style.offset) == ("IE", LabelPosition.LEFT, 7)


def test_edgeworth_good_origin_and_title_text():
    box = EdgeworthBox(
        MODEL,
        MODEL,
        total_x=10,
        total_y=10,
        x_axis=Axis(label=Label(text="f", fontsize=16, color="#123456")),
        origin_label=Label(fontsize=15),
        title=Label(text="Exchange", fontsize=19),
    )
    assert (_text(box, "box.x_a").text, _text(box, "box.x_b").text) == ("f_A", "f_B")
    assert _text(box, "box.x_b").style.color.to_hex() == "#123456"
    assert _text(box, "box.origin_a").style.size == 15
    assert (_text(box, "box.title").text, _text(box, "box.title").style.size) == ("Exchange", 19)


def test_axis_label_reaches_tikz(tmp_path):
    output = tmp_path / "text.tex"
    Canvas(x_axis=Axis(label=Label(text="q_1", fontsize=18))).save(output)
    assert "q_1" in output.read_text(encoding="utf-8")
