"""Purpose-driven themes compile into MosaicKit role styles."""

import pytest

from utility_viz import Canvas, Config, themes
from utility_viz.cli.resolve import resolve_theme
from utility_viz.core.errors.deprecation import UtilityVizDeprecationWarning


@pytest.mark.parametrize("name", ["manual", "default", "colorblind", "nord", "paper", "monochrome", "presentation"])
def test_themes_are_registered(name):
    assert getattr(themes, name).name == name


@pytest.mark.parametrize("name", ["manual", "colorblind", "paper", "monochrome", "presentation"])
def test_theme_resolves_from_cli_and_config(name):
    assert resolve_theme(name).name == name
    assert Config.from_dict({"base": name}).theme.name == name


def test_paper_is_thinner_and_smaller_than_default():
    assert themes.paper.ic_linewidth < themes.default.ic_linewidth
    assert themes.paper.budget_linewidth < themes.default.budget_linewidth
    assert themes.paper.eq_markersize < themes.default.eq_markersize


def test_monochrome_colors_are_neutral_and_styles_remain_distinct():
    for color in (
        themes.monochrome.ic_color,
        themes.monochrome.budget_color,
        themes.monochrome.path_color,
        themes.monochrome.eq_color,
    ):
        red, green, blue = (int(color[index : index + 2], 16) for index in (1, 3, 5))
        assert red == green == blue
    canvas = Canvas(theme=themes.monochrome).add_utility(lambda x, y: x * y, levels=[2]).add_budget(1, 1, 8)
    layers = canvas.snapshot().layers
    curve = next(layer for layer in layers if layer.id.startswith("utility."))
    budget = next(layer for layer in layers if layer.id == "budget")
    assert curve.stroke.dash != budget.stroke.dash


def test_presentation_tokens_are_larger():
    assert themes.presentation.label_scale > themes.default.label_scale
    assert themes.presentation.ic_linewidth > themes.default.ic_linewidth
    assert themes.presentation.eq_markersize > themes.default.eq_markersize
    assert themes.presentation.title_label.fontsize > 12


def test_opaque_and_transparent_backgrounds_compile_to_canvas_role():
    opaque = Canvas(theme=themes.manual).theme.roles["canvas"].fill
    transparent = Canvas(theme=themes.default).theme.roles["canvas"].fill
    assert opaque.color.to_hex().lower() == "#ffffff"
    assert opaque.opacity == 1.0
    assert transparent.opacity == 0.0


def test_manual_canvas_saves_png(tmp_path):
    target = tmp_path / "manual.png"
    Canvas(theme=themes.manual).add_budget(1, 1, 8).save(target)
    assert target.read_bytes().startswith(b"\x89PNG")


def test_dark_theme_is_removed_and_gives_default():
    with pytest.warns(UtilityVizDeprecationWarning, match="'dark' theme"):
        theme = themes.dark
    assert theme is themes.default
    assert "dark" not in themes.__all__
    with pytest.raises(AttributeError):
        themes.light  # noqa: B018


def test_dark_base_warns_and_uses_default():
    with pytest.warns(UtilityVizDeprecationWarning, match='base = "dark"'):
        config = Config.from_dict({"base": "dark"})
    assert config.theme is themes.default


def test_dark_cli_theme_warns_and_uses_default():
    with pytest.warns(UtilityVizDeprecationWarning):
        assert resolve_theme("dark") is themes.default


def test_dark_is_not_offered():
    from utility_viz.core.config.settings import template

    base = next(line for line in template().splitlines() if line.startswith("base ="))
    assert "manual" in base and "dark" not in base
