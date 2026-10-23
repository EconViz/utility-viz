"""Built-in themes for economic diagrams.

Every theme is one of mosaickit's shared themes (``manual``, ``default``, ``colorblind``,
``monochrome``, ``nord``, ``paper``, ``presentation``), built from its tokens by
:mod:`utility_viz.core.themes.roles`. The default theme uses a colour-blind-friendly palette.
There is no dark theme: ``dark`` was removed in 2.0.0b8 and now warns and gives ``default``.

References
----------
- https://gist.github.com/thriveth/8560036
- https://www.tandfonline.com/doi/abs/10.1080/00220485.1996.10844911
"""

from utility_viz.core.errors.deprecation import warn_deprecated
from utility_viz.core.themes.roles import THEME_NAMES, build_theme
from utility_viz.core.themes.theme import Theme

#: Names that are no longer themes -> the theme used instead (until 3.0).
REMOVED_THEMES = {"dark": "default"}

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
]


def __getattr__(name: str) -> Theme:
    if name in REMOVED_THEMES:
        replacement = REMOVED_THEMES[name]
        warn_deprecated(f"the {name!r} theme", f"themes.{replacement} (there is no dark theme)")
        return build_theme(replacement)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
