"""Built-in themes for economic diagrams.

Every theme is one of mosaickit's shared themes (``manual``, ``default``, ``colorblind``,
``monochrome``, ``nord``, ``paper``, ``presentation``), built from its tokens by
:mod:`utility_viz.core.themes.roles`. The default theme uses a colour-blind-friendly palette.

References
----------
- https://gist.github.com/thriveth/8560036
- https://www.tandfonline.com/doi/abs/10.1080/00220485.1996.10844911
"""

from utility_viz.core.themes.roles import THEME_NAMES, build_theme
from utility_viz.core.themes.theme import Theme

COLORBLIND_CYCLE_RGB: tuple[tuple[int, int, int], ...] = (
    (55, 126, 184),  # blue
    (255, 127, 0),  # orange
    (77, 175, 74),  # green
    (247, 129, 191),  # pink
    (166, 86, 40),  # brown
    (152, 78, 163),  # purple
    (153, 153, 153),  # gray
    (228, 26, 28),  # red
    (222, 222, 0),  # yellow
)


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"#{r:02X}{g:02X}{b:02X}"


COLORBLIND_CYCLE_HEX: tuple[str, ...] = tuple(_rgb_to_hex(rgb) for rgb in COLORBLIND_CYCLE_RGB)

# The built-in themes: mosaickit's shared theme tokens, coloured and sized by
# utility_viz.core.themes.roles. Every shared theme name is a built-in base.
manual = build_theme("manual")
default = build_theme("default")
colorblind = build_theme("colorblind")
monochrome = build_theme("monochrome")
nord = build_theme("nord")
paper = build_theme("paper")
presentation = build_theme("presentation")

dark = Theme(
    name="dark",
    axis_color="#E0E0E0",
    label_color="#E0E0E0",
    background_color="#1E1E1E",
    ic_color="#4FC3F7",
    path_color="#81C784",
    budget_color="#CE93D8",
    eq_color="#EF5350",
    ray_color="#B0BEC5",
    kink_color="#FFB74D",
    sub_effect_color="#FFB74D",
    inc_effect_color="#81C784",
    compensated_budget_color="#B0BEC5",
    subsistence_color="#B0BEC5",
    contract_color="#E0E0E0",
    core_color="#EF5350",
    price_color="#E0E0E0",
    walrasian_color="#4FC3F7",
)

__all__ = [
    "THEME_NAMES",
    "Theme",
    "build_theme",
    "manual",
    "COLORBLIND_CYCLE_RGB",
    "COLORBLIND_CYCLE_HEX",
    "default",
    "colorblind",
    "nord",
    "paper",
    "monochrome",
    "presentation",
    "dark",
]
