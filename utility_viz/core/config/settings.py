"""Config: diagram settings read from ``econ-viz.toml``.

mosaickit reads the file; utility-viz only declares what its table means (:data:`SCHEMA`).
The top level holds the settings every EconViz package shares, and utility-viz keeps its
own under ``[utility]``::

    base = "default"            -> built-in theme to start from
    [font]                      -> text = generic font (sans, serif, mono), math = a math font file
    [fonts]                     -> font files that replace the generic fonts (sans, serif, mono)
    [color]                     -> background, axis, label

    [utility.color]             -> Theme colour fields, e.g. ic = "#2E86AB" -> ic_color
    [utility.stroke.budget]     -> theme.budget_stroke   (Stroke)
    [utility.marker.point]      -> theme.point_marker    (Marker)
    [utility.label.axis]        -> theme.axis_label      (Label)
    [utility.fill.budget]       -> theme.budget_fill     (Fill)
    [utility.legend]            -> theme.legend          (Legend)

The 2.0 beta layout, with utility-viz's tables at the top level, is still read with a
deprecation warning. Anything left out keeps the built-in default.
"""

from __future__ import annotations

import dataclasses
import difflib
import sys
import warnings
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import mosaickit
from mosaickit import ConfigurationError, MathFont, TextFonts
from mosaickit import econ_toml as et

import utility_viz.core.themes as themes
from utility_viz.core.config.fonts import _OLD_MATH_TOKENS
from utility_viz.core.errors.deprecation import UtilityVizDeprecationWarning, deprecation_message, warn_deprecated
from utility_viz.core.errors.exceptions import InvalidParameterError
from utility_viz.core.styles.fill import Fill
from utility_viz.core.styles.label import Label
from utility_viz.core.styles.legend import Legend
from utility_viz.core.styles.marker import Marker
from utility_viz.core.styles.stroke import Stroke
from utility_viz.core.themes import roles
from utility_viz.core.themes.theme import Theme

# The file every EconViz package reads.
DEFAULT_FILE = et.FILE_NAME
LEGACY_FILE = "utility-viz.toml"  # the 2.0 beta name; still read with a warning, removed in 3.0

# Table -> (style class, property-name pattern).
_STYLES: dict[str, tuple[type, str]] = {
    "stroke": (Stroke, "{}_stroke"),
    "marker": (Marker, "{}_marker"),
    "label": (Label, "{}_label"),
    "fill": (Fill, "{}_fill"),
}
# Friendlier names for a few properties.
_ALIASES = {"equilibrium": "eq", "substitution_effect": "sub_effect", "income_effect": "inc_effect"}
_LEGEND_FIELDS = tuple(f.name for f in dataclasses.fields(Legend))
_OVERRIDES = "_ev_overrides"


@dataclass(frozen=True)
class Config:
    """A Theme plus font choices, usually read from ``econ-viz.toml``.

    Parameters
    ----------
    theme : Theme
        Theme with the configured overrides applied.
    font : str, optional
        Generic font for every Canvas and Figure: ``"sans"`` (default), ``"serif"`` or ``"mono"``.
    fonts : mosaickit.TextFonts, optional
        Font files that replace the generic fonts; the ones left out keep the defaults.
    math_font : mosaickit.MathFont, optional
        Math font file; without it math is set by Matplotlib.
    """

    theme: Theme = themes.default
    font: str | None = None
    fonts: TextFonts | None = None
    math_font: MathFont | None = None

    @classmethod
    def load(cls, path: str | Path | None = None) -> Config:
        """Read a TOML file.

        With an explicit *path* that file is read (and must exist). With no
        *path*, :func:`find_config_file` decides: ``econ-viz.toml``, then the
        2.0 beta name ``utility-viz.toml`` (with a deprecation warning). As in 1.x,
        :class:`InvalidParameterError` is raised when neither exists; use
        :meth:`discover` to fall back to the built-in defaults instead.
        """
        if path is None:
            found = find_config_file(stacklevel=3)
            if found is None:
                raise InvalidParameterError(f"config file not found: {DEFAULT_FILE}")
            return cls._read(found)
        return cls._read(Path(path))

    @classmethod
    def discover(cls, path: str | Path | None = None, *, directory: str | Path | None = None) -> Config:
        """Resolve a Config using the documented lookup order.

        1. the explicit *path*, 2. ``econ-viz.toml``, 3. the 2.0 beta name
        ``utility-viz.toml`` (deprecated), 4. built-in defaults. Files 2 and 3 are looked up in
        *directory* (default: the current working directory).
        """
        found = find_config_file(path, directory=directory, stacklevel=3)
        return cls() if found is None else cls._read(found)

    @classmethod
    def _read(cls, path: Path) -> Config:
        return cls.from_dict(read_file(path), source=str(path), base_dir=path.parent)

    @classmethod
    def from_dict(cls, data: Mapping, *, source: str = "config", base_dir: str | Path | None = None) -> Config:
        """Build a Config from already-parsed TOML data.

        Relative font paths are resolved against *base_dir* (the TOML file's directory when read
        from a file).
        """
        try:
            config = SCHEMA.build(data, source=source, base_dir=base_dir)
        except ConfigurationError as error:
            message = str(error)
            raise InvalidParameterError(
                message if message.startswith(f"{source}:") else f"{source}: {message}"
            ) from None
        if not isinstance(config, cls):  # a subclass asked for its own type
            config = cls(**{f.name: getattr(config, f.name) for f in dataclasses.fields(Config)})
        return config

    def use(self) -> Config:
        """Make this the default for diagrams created from now on; returns *self*."""
        global _active
        _active = self
        return self

    @staticmethod
    def reset() -> None:
        """Go back to the built-in defaults."""
        global _active
        _active = None

    @staticmethod
    def active() -> Config:
        """The Config in use (the built-in defaults when none was set)."""
        return _active if _active is not None else Config()


_active: Config | None = None


def read_file(path: str | Path) -> dict[str, Any]:
    """The parsed TOML of *path*; raise :class:`InvalidParameterError` when missing or invalid."""
    file = Path(path)
    try:
        return et.read(file)
    except ConfigurationError as error:
        if file.is_file():
            raise InvalidParameterError(f"invalid TOML: {error}") from None
        raise InvalidParameterError(str(error)) from None


def find_config_file(
    path: str | Path | None = None, *, directory: str | Path | None = None, stacklevel: int = 2
) -> Path | None:
    """Locate the settings file, or ``None`` when the defaults should be used.

    Order: explicit *path*; ``econ-viz.toml``; the 2.0 beta name ``utility-viz.toml`` (warns);
    otherwise ``None``. When both named files exist the new one wins and the
    legacy one is ignored with a warning.
    """
    if path is not None:
        return Path(path)
    base = Path(directory) if directory is not None else Path.cwd()
    new, legacy = base / DEFAULT_FILE, base / LEGACY_FILE
    if new.is_file():
        if legacy.is_file():
            warn_deprecated(
                f"legacy config file {LEGACY_FILE!r} (ignored because {DEFAULT_FILE!r} exists)",
                f"{DEFAULT_FILE!r} only; delete {LEGACY_FILE!r}",
                stacklevel=stacklevel,
            )
        return new
    if legacy.is_file():
        warn_deprecated(
            f"config file {LEGACY_FILE!r}",
            f"{DEFAULT_FILE!r}, the file every EconViz package reads "
            "(run `utility-viz init --migrate`; it also moves utility-viz's tables under [utility])",
            stacklevel=stacklevel,
        )
        return legacy
    return None


def active_theme() -> Theme:
    return Config.active().theme


# ------------------------------------------------------------------
# Schema
# ------------------------------------------------------------------


def _hint(value: str, choices: list[str]) -> str:
    close = difflib.get_close_matches(value, choices, n=1)
    return f"; did you mean {close[0]!r}?" if close else ""


def _builtin_theme_names() -> list[str]:
    extra = [name for name in themes.__all__ if isinstance(getattr(themes, name, None), Theme)]
    return [*roles.THEME_NAMES, *(name for name in extra if name not in roles.THEME_NAMES)]


def _style_names(pattern: str) -> list[str]:
    """Theme properties such as ``budget_stroke`` for ``"{}_stroke"``, sorted."""
    suffix = pattern.format("")
    return sorted(
        name
        for name in dir(themes.default)
        if name.endswith(suffix) and not name.startswith("_") and name != suffix.lstrip("_")
    )


def _colour_names() -> list[str]:
    return sorted(f.name[: -len("_color")] for f in dataclasses.fields(Theme) if f.name.endswith("_color"))


# The styles a file overrides, merged over the base theme's in _finalize. ``None`` = unset.
_Styles = dataclasses.make_dataclass(
    "_Styles",
    [(name, Any, dataclasses.field(default=None)) for _, p in _STYLES.values() for name in _style_names(p)]
    + [("legend", Legend, dataclasses.field(default=Legend()))],
    frozen=True,
)


@dataclass(frozen=True)
class _Draft:
    """What :data:`SCHEMA` builds; :func:`_finalize` turns it into a :class:`Config`."""

    theme: Theme
    font: str | None = None
    fonts: TextFonts | None = None
    math_font: MathFont | None = None
    styles: Any = dataclasses.field(default_factory=_Styles)


def _style_pattern(section: str) -> et.Pattern:
    style, pattern = _STYLES[section]
    names = [name[: -len(pattern.format(""))] for name in _style_names(pattern)]
    allowed = [f.name for f in dataclasses.fields(style)]
    check_color = et.color("").convert

    def convert(name: str, table: Mapping[str, Any], ctx: et.Context) -> Mapping[str, Any]:
        prop = pattern.format(_ALIASES.get(name, name))
        if not hasattr(_Styles(), prop):
            choices = sorted([*names, *(alias for alias, target in _ALIASES.items() if target in names)])
            raise ConfigurationError(f"no such setting{_hint(name, choices)} (choose: {', '.join(names)})")
        unknown = [key for key in table if key not in allowed]
        if unknown:
            key = unknown[0]
            raise ConfigurationError(f"unknown key {key!r}{_hint(key, allowed)} (fields: {', '.join(allowed)})")
        if "color" in table:
            check_color(table["color"], ctx, "color")
        try:
            return {f"styles.{prop}": style(**table)}
        except (InvalidParameterError, TypeError, ValueError) as error:
            raise ConfigurationError(str(error)) from None

    return et.pattern(section, convert)


def _legend_field(key: str) -> et.Field:
    def convert(value: Any, ctx: et.Context) -> Any:
        if key in ("frame", "visible"):
            et.boolean("").convert(value, ctx, key)
        try:
            return getattr(Legend(**{key: value}), key)
        except (InvalidParameterError, TypeError, ValueError) as error:
            raise ctx.error(str(error)) from None

    return et.transform(f"styles.legend.{key}", convert)


def _math_font(value: Any, ctx: et.Context) -> MathFont:
    path = Path(value)
    if path.name in _OLD_MATH_TOKENS and not path.exists():
        raise ConfigurationError(
            f"{path.name!r} is a font set name from utility-viz 2.0.0b2 and earlier; "
            "pass the path of an OpenType math font file (STIX Two Math, Libertinus Math, ...)"
        )
    return MathFont(path)


def _finalize(draft: _Draft, ctx: et.Context) -> Config:
    fields: dict[str, object] = {}
    properties: dict[str, object] = {}
    theme = draft.theme
    for name in (f.name for f in dataclasses.fields(draft.styles)):
        override = getattr(draft.styles, name)
        if name == "legend" and override == Legend():
            continue
        if override is not None:
            _set(theme, name, override, fields, properties)
    return Config(
        theme=_themed(theme, fields, properties), font=draft.font, fonts=draft.fonts, math_font=draft.math_font
    )


def _warn_legacy_layout(message: str) -> None:
    """The legacy-layout warning, blamed on the first caller outside utility-viz and mosaickit."""
    _warn_outside(f"{message} (run `utility-viz init --migrate` to rewrite the file)")


def _warn_outside(message: str) -> None:
    """A UtilityVizDeprecationWarning blamed on the first caller outside utility-viz and mosaickit."""
    internal = (str(Path(__file__).resolve().parents[2]), str(Path(mosaickit.__file__).resolve().parent))
    level, frame = 1, sys._getframe(0)
    while frame is not None and frame.f_code.co_filename.startswith(internal):
        frame, level = frame.f_back, level + 1  # type: ignore[assignment]
    warnings.warn(message, UtilityVizDeprecationWarning, stacklevel=level)


def _base(name: str) -> Callable[[], _Draft]:
    """The factory of base *name*; the built-in themes come from the theme roles."""
    if name in themes.REMOVED_THEMES:
        replacement = themes.REMOVED_THEMES[name]

        def removed() -> _Draft:
            _warn_outside(
                deprecation_message(f'base = "{name}"', f'base = "{replacement}" (there is no dark theme)'),
            )
            return _Draft(theme=roles.build_theme(replacement))

        return removed
    if name in roles.THEME_NAMES:
        return lambda: _Draft(theme=roles.build_theme(name))
    return lambda: _Draft(theme=getattr(themes, name))


def _fields() -> dict[str, et.Field]:
    fields = {f"color.{name}": et.color(f"theme.{name}_color") for name in _colour_names()}
    for alias, target in _ALIASES.items():
        if f"color.{target}" in fields:
            fields[f"color.{alias}"] = et.color(f"theme.{target}_color")
    fields.update({f"legend.{key}": _legend_field(key) for key in _LEGEND_FIELDS})
    return fields


def _docs() -> dict[str, str]:
    docs = {f"color.{alias}": f"same as {target}" for alias, target in _ALIASES.items()}
    docs["color.background"] = "none (transparent) by default; overrides the shared [color] background"
    docs["color.secondary_ic"] = "follows ic by default"
    docs.update(
        {
            "legend.position": "auto, upper right, upper left, lower left, lower right, top, bottom, left, right",
            "legend.columns": "number of columns",
            "legend.opacity": "0 (transparent) to 1",
        }
    )
    for section, (style, pattern) in _STYLES.items():
        fields = ", ".join(f.name for f in dataclasses.fields(style))
        names = ", ".join(name[: -len(pattern.format(""))] for name in _style_names(pattern))
        docs[section] = f"{fields}. <name>: {names}"
    return docs


SCHEMA = et.register(
    et.Schema(
        package="utility",
        base={name: _base(name) for name in [*_builtin_theme_names(), *themes.REMOVED_THEMES]},
        fields=_fields(),
        patterns={section: _style_pattern(section) for section in _STYLES},
        shared={
            "font": "font",
            "fonts": "fonts",
            "math_font": et.transform("math_font", _math_font),
            "background": "theme.background_color",
            "axis": "theme.axis_color",
            "label": "theme.label_color",
        },
        legacy_top_level=True,
        legacy_warning=_warn_legacy_layout,
        finalize=_finalize,
        docs=_docs(),
    )
)


# ------------------------------------------------------------------
# Theme overrides
# ------------------------------------------------------------------


def _set(base: Theme, name: str, override, fields: dict, properties: dict) -> None:
    """Merge *override* over the base value; dataclass fields and properties are kept apart."""
    if name in {field.name for field in dataclasses.fields(base)}:
        fields[name] = override.merged_over(getattr(base, name))
    else:
        properties[name] = override
    properties.setdefault(_OVERRIDES, {})[name] = override


def _themed(base: Theme, fields: dict, properties: dict) -> Theme:
    """A Theme with *fields* replaced and each property in *properties* merged over the base property."""
    if not fields and not properties:
        return base
    parent = type(base)
    overrides = dict(getattr(base, _OVERRIDES, {}))
    overrides.update(properties.pop(_OVERRIDES, {}))
    cls: type[Theme]
    namespace: dict[str, object] = {
        name: property(
            lambda self, _name=name, _value=value: _value.merged_over(getattr(super(cls, self), _name))  # type: ignore[misc]
        )
        for name, value in properties.items()
    }
    # Only what the file set, so drawing code can apply it without overriding
    # a default it already draws the same way.
    namespace[_OVERRIDES] = overrides
    cls = type(f"Configured{parent.__name__}", (parent,), namespace)
    values = {field.name: getattr(base, field.name) for field in dataclasses.fields(base)}
    values.update(fields)
    return cls(**values)


# ------------------------------------------------------------------
# Template
# ------------------------------------------------------------------


def template() -> str:
    """A commented ``econ-viz.toml``: the shared settings, then every ``[utility.*]`` setting."""
    theme = themes.default
    base_choices = ", ".join(_builtin_theme_names())
    return f"""# EconViz settings, shared by every EconViz package. Load with:  Config.load("econ-viz.toml").use()
# or on the command line:          utility-viz plot --config econ-viz.toml ...
# Anything left out keeps the built-in default; delete what you don't need.
# The top level is shared by every package; utility-viz's own settings live under [utility].

base = "default"                 # built-in theme to start from: {base_choices}

[font]
# text = "serif"                 # sans (default), serif or mono
# math = "fonts/STIXTwoMath.otf"  # an OpenType math font; without it math is set by Matplotlib

[fonts]
# Font files that replace a generic font; the ones left out keep the defaults.
# A list takes a regular and a bold file, or one variable font.
# sans = ["fonts/SourceSans3-Regular.ttf", "fonts/SourceSans3-Bold.ttf"]
# serif = ["fonts/SourceSerif4-Regular.ttf"]
# mono = ["fonts/JetBrainsMono-Regular.ttf"]

[color]
# background = "#ffffff"         # none (transparent) by default
# axis = "{theme.axis_color}"
# label = "{theme.label_color}"            # text

# ---- utility-viz ------------------------------------------------------------
# Uncomment a table and the keys you want to change.

{SCHEMA.template()}
# Other EconViz packages keep their own settings in one table each, for example
# [principle.color]. utility-viz skips those tables.
"""


__all__ = ["DEFAULT_FILE", "LEGACY_FILE", "SCHEMA", "Config", "active_theme", "find_config_file", "template"]
