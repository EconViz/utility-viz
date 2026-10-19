"""Label values are translated to backend-neutral text layers."""

import pytest
from mosaickit import TextLayer

from utility_viz import Canvas, Label, Marker, solve
from utility_viz.core.diagrams.consumer.edgeworth import EdgeworthBox
from utility_viz.core.errors.exceptions import InvalidParameterError
from utility_viz.core.styles.label import split_label
from utility_viz.enums import LabelPosition
from utility_viz.models.optimization import decompose_price_effect
from utility_viz.models.utility import CobbDouglas, Satiation

MODEL = CobbDouglas(alpha=0.5, beta=0.5)
EQ = solve(MODEL, px=2.0, py=3.0, income=30.0)
DEC = decompose_price_effect(MODEL, px=(2.0, 4.0), py=3.0, income=30.0)


def _text(canvas, suffix: str) -> TextLayer:
    return next(
        layer
        for layer in canvas.snapshot().ordered_layers
        if isinstance(layer, TextLayer) and layer.id.endswith(suffix)
    )


class TestLabelValue:
    def test_defaults(self):
        label = Label()
        assert (label.text, label.position, label.offset, label.color, label.fontsize, label.visible) == (
            None,
            None,
            None,
            None,
            None,
            None,
        )

    def test_positions_aliases_and_validation(self):
        assert Label(position="top-left").position is LabelPosition.TOP_LEFT
        assert Label(position="above").position is LabelPosition.TOP
        assert Label(position="below").position is LabelPosition.BOTTOM
        for kwargs in ({"position": "middle"}, {"fontsize": 0}, {"fontsize": -1}):
            with pytest.raises(InvalidParameterError):
                Label(**kwargs)

    def test_merge_and_split(self):
        merged = Label(offset=9).merged_over(Label(position="left", offset=2, color="red"))
        assert (merged.position, merged.offset, merged.color) == (LabelPosition.LEFT, 9, "red")
        default = Label(position="top-right", offset=5)
        assert split_label("P", default) == ("P", default)
        text, style = split_label(Label(position="left"), default, "x^*")
        assert (text, style.position, style.offset) == ("x^*", LabelPosition.LEFT, 5)


def test_point_label_style_placement_visibility_and_marker_color():
    canvas = Canvas().add_point(
        2, 2, label=Label(text="Q", position="left", fontsize=15, opacity=0.4), marker=Marker(color="#123456")
    )
    layer = _text(canvas, "point.label")
    assert (layer.text, layer.offset, layer.anchor, layer.visible) == ("Q", (-5, 0), "right", True)
    assert (layer.style.color.to_hex(), layer.style.size, layer.style.opacity) == ("#123456", 15, 0.4)
    hidden = _text(Canvas().add_point(2, 2, label=Label(text="P", visible=False)), "point.label")
    assert hidden.visible is False


def test_equilibrium_and_decomposition_label_placement():
    equilibrium = _text(
        Canvas(x_max=20, y_max=15).add_equilibrium(EQ, label=Label(position="bottom", offset=8)),
        "equilibrium.label",
    )
    assert (equilibrium.text, equilibrium.offset, equilibrium.anchor) == ("x^*", (0, -8), "top")
    canvas = Canvas(x_max=20, y_max=15).add_decomposition(DEC, point_label=Label(position="bottom-left", visible=False))
    labels = [layer for layer in canvas.snapshot().ordered_layers if layer.id.startswith("decomposition.bundle.")]
    assert labels and all(
        (layer.offset, layer.anchor, layer.visible) == ((-6, -6), "top-right", False) for layer in labels
    )


def test_ic_and_bliss_labels_are_scene_text():
    canvas = Canvas(x_max=20, y_max=15).add_utility(MODEL, levels=[3, 5], ic_label=Label(text="{:.1f}", position="top"))
    labels = [
        layer
        for layer in canvas.snapshot().ordered_layers
        if isinstance(layer, TextLayer) and layer.id.startswith("utility") and ".label" in layer.id
    ]
    assert [layer.text for layer in labels] == ["3.0", "5.0"]
    assert labels[0].offset == (0, 4) and labels[0].anchor == "bottom"
    bliss = Canvas(x_max=12, y_max=10).add_utility(
        Satiation(bliss_x=6, bliss_y=4), levels=[-8], bliss_label=Label(visible=False)
    )
    layer = _text(bliss, "bliss.label")
    assert layer.text == r"\mathbf{x}^*" and layer.visible is False


def test_edgeworth_label_uses_requested_position_and_color():
    box = EdgeworthBox(MODEL, MODEL, total_x=10, total_y=10)
    box.add_endowment(7, 3, label=Label(text=r"\omega", position="bottom", color="#123456"))
    layer = _text(box, "endowment.label")
    assert (layer.text, layer.offset, layer.anchor, layer.style.color.to_hex()) == (
        r"\omega",
        (0, -5),
        "top",
        "#123456",
    )


def test_label_reaches_tikz_and_is_exported(tmp_path):
    output = tmp_path / "label.tex"
    Canvas().add_point(5, 5, label=Label(text="Q", position="left")).save(output)
    assert "Q" in output.read_text(encoding="utf-8")
    import utility_viz

    assert utility_viz.Label is Label
