"""Font choices stay local to MosaicKit text styles."""

import pytest
from mosaickit import TextLayer

from utility_viz import Canvas, Figure, Layout
from utility_viz.core.errors.exceptions import InvalidParameterError


def _text_layers(canvas):
    return [layer for layer in canvas.snapshot().layers if isinstance(layer, TextLayer)]


def test_custom_font_applies_to_existing_and_late_text_layers():
    canvas = Canvas(font="DejaVu Serif", title="Title").add_point(1, 1, label="late")
    assert canvas.font == "DejaVu Serif"
    assert all(layer.style.family == "DejaVu Serif" for layer in _text_layers(canvas))


def test_font_fallback_sequence_uses_first_available_family_at_scene_boundary():
    canvas = Canvas(font=["No Such Font UtilityViz", "serif"])
    assert canvas.font == "serif"
    assert canvas.font_families == ("No Such Font UtilityViz", "serif")


def test_figure_propagates_font_and_math_font():
    figure = Figure(Layout.SIDE_BY_SIDE, font="serif", math_font="stix")
    for panel in figure.canvases:
        panel.add_point(1, 1, label="P")
        assert panel.font == "serif"
        assert panel.math_font == "stix"
        math_layers = [layer for layer in _text_layers(panel) if layer.math]
        assert math_layers and all(layer.style.family == "STIXGeneral" for layer in math_layers)
        assert next(layer for layer in _text_layers(panel) if layer.id == "axes.origin.label").style.family == "serif"


def test_missing_font_and_invalid_math_font_fail_clearly():
    with pytest.raises(InvalidParameterError, match="No Such Font UtilityViz"):
        Canvas(font="No Such Font UtilityViz")
    with pytest.raises(InvalidParameterError, match="stix"):
        Canvas(math_font="comic")


def test_font_configuration_does_not_create_renderer_objects():
    canvas = Canvas(font="serif", math_font="cm")
    assert not hasattr(canvas, "fig") and not hasattr(canvas, "ax")
