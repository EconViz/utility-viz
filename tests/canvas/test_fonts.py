"""Font choices: a generic font, replacement font files and a math font, as in every diagram package."""

from pathlib import Path

import matplotlib
import pytest
from mosaickit import MathFont, TextFonts, TextLayer

from utility_viz import Canvas, Figure, Layout
from utility_viz.core.errors.exceptions import InvalidParameterError

FONTS = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
SERIF = FONTS / "DejaVuSerif.ttf"
MATH = FONTS / "DejaVuSerif.ttf"  # has an OpenType MATH table


def _text_layers(canvas):
    return [layer for layer in canvas.snapshot().layers if isinstance(layer, TextLayer)]


def test_the_generic_font_reaches_every_text_layer_through_the_theme():
    canvas = Canvas(font="serif", title="Title").add_point(1, 1, label="late")
    assert canvas.font == "serif"
    assert canvas.theme.defaults.text.font == "serif"
    assert all(layer.style is None or layer.style.font in {None, "serif"} for layer in _text_layers(canvas))


def test_without_a_font_text_keeps_the_sans_default():
    canvas = Canvas()
    assert canvas.font is None
    assert canvas.theme.defaults.text is None or canvas.theme.defaults.text.font is None


@pytest.mark.parametrize("font", ["sans", "serif", "mono"])
def test_all_three_generic_fonts_are_accepted(font):
    assert Canvas(font=font).font == font


@pytest.mark.parametrize("font", ["DejaVu Serif", "Avenir", ["sans", "serif"], ""])
def test_installed_font_names_are_not_fonts_any_more(font):
    with pytest.raises(InvalidParameterError, match="font must be one of sans, serif, mono"):
        Canvas(font=font)


def test_font_files_replace_a_generic_font_through_the_mosaickit_config():
    fonts = TextFonts(serif=SERIF)
    canvas = Canvas(font="serif", fonts=fonts)
    assert canvas.fonts is fonts
    assert canvas.config.fonts is fonts
    with pytest.raises(InvalidParameterError, match="TextFonts"):
        Canvas(fonts=str(SERIF))  # type: ignore[arg-type]


def test_a_math_font_is_a_mathfont_or_the_path_of_one():
    assert Canvas(math_font=MathFont(MATH)).math_font == MathFont(MATH)
    assert Canvas(math_font=str(MATH)).math_font == MathFont(MATH)
    assert Canvas(math_font=MATH).config.math_font == MathFont(MATH)
    assert Canvas().math_font is None
    with pytest.raises(InvalidParameterError, match="not a font file"):
        Canvas(math_font="/no/such/font.otf")
    with pytest.raises(InvalidParameterError, match="pass the path of an OpenType math font"):
        Canvas(math_font="stix")  # the old tokens are gone: pass a file
    with pytest.raises(InvalidParameterError, match="MathFont"):
        Canvas(math_font=3)  # type: ignore[arg-type]


def test_figure_propagates_font_fonts_and_math_font():
    fonts = TextFonts(mono=FONTS / "DejaVuSansMono.ttf")
    figure = Figure(Layout.SIDE_BY_SIDE, font="mono", fonts=fonts, math_font=MATH)
    for panel in figure.canvases:
        panel.add_point(1, 1, label="P")
        assert panel.font == "mono"
        assert panel.fonts is fonts
        assert panel.math_font == MathFont(MATH)


def test_font_configuration_does_not_create_renderer_objects():
    canvas = Canvas(font="serif", math_font=MATH)
    assert not hasattr(canvas, "fig") and not hasattr(canvas, "ax")
