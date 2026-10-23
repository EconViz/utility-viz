"""Built-in themes come from mosaickit's shared theme tokens through the theme roles."""

import dataclasses

import pytest
from mosaickit.themes import ROLES, SHARED_THEMES, ThemeTokens, get_tokens

from utility_viz import Config, themes
from utility_viz.core.themes import roles
from utility_viz.core.themes.roles import (
    ELEMENT_ROLES,
    MANUAL_SIZES,
    SizePreset,
    build_theme,
    theme_colors,
    theme_from_tokens,
)
from utility_viz.core.themes.variants import MonochromeTheme, PresentationTheme
from utility_viz.enums import LabelPosition, LineStyle


def test_every_shared_theme_is_a_builtin_theme_and_base():
    assert tuple(SHARED_THEMES) == roles.THEME_NAMES
    for name in roles.THEME_NAMES:
        theme = getattr(themes, name)
        assert theme is build_theme(name)
        assert theme.name == name
        assert Config.from_dict({"base": name}).theme is theme


def test_roles_are_shared_roles_and_elements_are_theme_colours():
    fields = {f.name for f in dataclasses.fields(themes.Theme)}
    assert set(ELEMENT_ROLES.values()) <= set(ROLES)
    for element in ELEMENT_ROLES:
        assert f"{element}_color" in fields


@pytest.mark.parametrize("name", roles.THEME_NAMES)
def test_element_colours_follow_their_role(name):
    tokens, theme = get_tokens(name), build_theme(name)
    for element, role in ELEMENT_ROLES.items():
        if element == "secondary_ic":
            continue
        assert getattr(theme, f"{element}_color") == tokens.color(role)


def test_subtle_with_alpha_follows_ic_at_that_opacity():
    theme = themes.default
    assert theme.secondary_ic_color is None
    assert theme.secondary_ic_opacity == 0.45
    assert theme.secondary_ic_stroke.color == theme.ic_color


def test_subtle_without_alpha_is_its_own_colour():
    colors = theme_colors(get_tokens("manual"))
    assert colors["secondary_ic_color"] == "#b8b8b8"
    assert "secondary_ic_opacity" not in colors  # the size preset decides


def test_subtle_in_another_colour_keeps_its_colour():
    tokens = get_tokens("default")
    other = ThemeTokens("other", {**tokens.colors, "subtle": "#11223380"})
    colors = theme_colors(other)
    assert (colors["secondary_ic_color"], colors["secondary_ic_opacity"]) == ("#112233", 0.5)


def test_manual_reproduces_the_playground_sizes():
    theme = themes.manual
    assert theme.background_color == "#ffffff"
    assert (theme.axis_color, theme.ic_color, theme.budget_color) == ("#1a1a1a", "#8c8c8c", "#222222")
    assert theme.ic_stroke.width == 2.6 and theme.budget_stroke.width == 2.6
    assert (theme.secondary_ic_stroke.width, theme.secondary_ic_stroke.opacity) == (1.8, 1.0)
    assert theme.secondary_ic_stroke.color == "#b8b8b8"
    assert theme.path_stroke.width == 1.4 and theme.ray_stroke.width == 0.9
    assert theme.axis_stroke.width == 1.0
    assert theme.drop_stroke.style is LineStyle.DASHED
    assert theme.eq_marker.size == 5 and theme.point_marker.size == 5
    label = theme.point_label
    assert (label.fontsize, label.position, label.offset) == (14, LabelPosition.RIGHT, 10)
    assert theme.budget_fill.opacity == 0.08


def test_manual_matches_the_playground_toml():
    data = {
        "base": "default",
        "color": {"background": "#ffffff", "axis": "#1a1a1a", "label": "#1a1a1a"},
        "utility": {
            "color": {"ic": "#8c8c8c", "secondary_ic": "#b8b8b8", "budget": "#222222", "eq": "#1a1a1a"},
            "stroke": {"ic": {"width": 2.6}, "secondary_ic": {"width": 1.8, "opacity": 1.0}},
            "marker": {"eq": {"size": 5}},
            "label": {"point": {"fontsize": 14, "position": "right", "offset": 10}},
        },
    }
    configured = Config.from_dict(data).theme
    manual = themes.manual
    for name in ("ic_stroke", "secondary_ic_stroke", "eq_marker", "point_label"):
        assert getattr(configured, name) == getattr(manual, name)


def test_scales_multiply_the_base_sizes():
    base, presentation = themes.default, themes.presentation
    assert isinstance(presentation, PresentationTheme)
    assert presentation.ic_linewidth == pytest.approx(base.ic_linewidth * 1.5)
    assert presentation.axis_stroke.width == pytest.approx(base.axis_stroke.width * 1.5)
    assert presentation.eq_markersize == pytest.approx(base.eq_markersize * 1.3)
    assert presentation.kink_markersize == pytest.approx(base.kink_markersize * 1.3)
    assert presentation.label_scale == 1.25
    assert presentation.title_label.fontsize == 22


def test_preset_values_and_styles():
    tokens = get_tokens("default")
    scaled = ThemeTokens("big", tokens.colors, line_scale=2.0)
    preset = SizePreset(values={"ic_linewidth": 1.0}, styles={"budget_stroke": MANUAL_SIZES.styles["budget_stroke"]})
    theme = theme_from_tokens(scaled, preset)
    assert theme.ic_linewidth == 2.0  # values are scaled
    assert theme.budget_stroke.width == 2.6  # styles are used as given
    assert theme.name == "big"
    assert theme_from_tokens(tokens, name="mine").name == "mine"


def test_preset_style_must_be_a_property():
    with pytest.raises(ValueError, match="not a Theme property"):
        theme_from_tokens(get_tokens("default"), SizePreset(styles={"nope": MANUAL_SIZES.styles["ic_stroke"]}))


def test_monochrome_keeps_its_line_styles():
    assert isinstance(themes.monochrome, MonochromeTheme)
    assert themes.monochrome.walrasian_markersize == 11.0
    assert themes.monochrome.budget_stroke.style is LineStyle.DASHED
