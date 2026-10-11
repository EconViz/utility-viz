"""Font choices stay local to MosaicKit text styles."""

from mosaickit import TextLayer

from utility_viz import Canvas, Figure, Layout


def _text_layers(canvas):
    return [layer for layer in canvas.snapshot().layers if isinstance(layer, TextLayer)]


def test_custom_font_applies_to_existing_and_late_text_layers():
    canvas = Canvas(font="DejaVu Serif", title="Title").add_point(1, 1, label="late")
    assert canvas.font == "DejaVu Serif"
    assert all(layer.style.family == "DejaVu Serif" for layer in _text_layers(canvas))


def test_font_fallback_sequence_uses_first_family_at_scene_boundary():
    canvas = Canvas(font=["Preferred", "Fallback"])
    assert canvas.font == "Preferred"


def test_figure_propagates_font_and_math_font():
    figure = Figure(Layout.SIDE_BY_SIDE, font="serif", math_font="stix")
    for panel in figure.canvases:
        panel.add_point(1, 1, label="P")
        assert panel.font == "serif"
        assert panel.math_font == "stix"
        assert all(layer.style.family == "serif" for layer in _text_layers(panel))


def test_font_configuration_does_not_create_renderer_objects():
    canvas = Canvas(font="serif", math_font="cm")
    assert not hasattr(canvas, "fig") and not hasattr(canvas, "ax")
