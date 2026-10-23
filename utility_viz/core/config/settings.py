"""Config: diagram settings loaded from a TOML file.

Section names map straight to Theme properties, and fields are the arguments of
the matching style object::

    [stroke.budget]   -> theme.budget_stroke   (Stroke)
    [marker.point]    -> theme.point_marker    (Marker)
    [label.axis]      -> theme.axis_label      (Label)
    [fill.budget]     -> theme.budget_fill     (Fill)
    [legend]          -> theme.legend          (Legend)
    [color]           -> Theme colour fields, e.g. ic = "#2E86AB" -> ic_color
    [font]            -> text = generic font (sans, serif, mono), math = a math font file
    [fonts]           -> font files that replace the generic fonts (sans, serif, mono)

Anything left out keeps the built-in default.
"""

from __future__ import annotations

import dataclasses
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mosaickit import ConfigurationError, MathFont, TextFonts

import utility_viz.core.themes as themes
from utility_viz.core.config.fonts import _OLD_MATH_TOKENS, resolve_font, resolve_math_font
from utility_viz.core.errors.deprecation import warn_deprecated
from utility_viz.core.errors.exceptions import InvalidParameterError
from utility_viz.core.styles.fill import Fill
from utility_viz.core.styles.label import Label
from utility_viz.core.styles.legend import Legend
from utility_viz.core.styles.marker import Marker
from utility_viz.core.styles.stroke import Stroke
from utility_viz.core.themes.theme import Theme

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - exercised on Python 3.10 only
    import tomli as tomllib

from mosaickit.econ_toml import PACKAGE_TABLES

# The file every EconViz package reads; utility-viz keeps its settings at the top level.
DEFAULT_FILE = "econ-viz.toml"
LEGACY_FILE = "utility-viz.toml"  # the 2.0 beta name; still read with a warning, removed in 3.0

# Section -> (style class, property-name pattern).
_STYLES = {
    "stroke": (Stroke, "{}_stroke"),
    "marker": (Marker, "{}_marker"),
    "label": (Label, "{}_label"),
    "fill": (Fill, "{}_fill"),
}
# Friendlier names for a few properties.
_ALIASES = {"equilibrium": "eq", "substitution_effect": "sub_effect", "income_effect": "inc_effect"}
_TOP_LEVEL = {"base", "font", "fonts", "color"} | set(_STYLES) | {"legend"}
# Other packages' tables in the shared file, skipped here.
_OTHER_PACKAGES = PACKAGE_TABLES
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
        try:
            with path.open("rb") as handle:
                data = tomllib.load(handle)
        except FileNotFoundError:
            raise InvalidParameterError(f"config file not found: {path}") from None
        except tomllib.TOMLDecodeError as error:
            raise InvalidParameterError(f"{path}: invalid TOML: {error}") from None
        return cls.from_dict(data, source=str(path), base_dir=path.parent)

    @classmethod
    def from_dict(cls, data: Mapping, *, source: str = "config", base_dir: Path | None = None) -> Config:
        """Build a Config from already-parsed TOML data.

        Relative font paths are resolved against *base_dir* (the TOML file's directory when read
        from a file).
        """
        unknown = set(data) - _TOP_LEVEL - _OTHER_PACKAGES
        if unknown:
            raise InvalidParameterError(
                f"{source}: unknown section(s) {', '.join(sorted(unknown))}; "
                f"choose from {', '.join(sorted(_TOP_LEVEL))}"
            )
        base = _base_theme(data.get("base", "default"), source)
        fields: dict[str, object] = {}
        properties: dict[str, object] = {}

        for key, value in _table(data, "color", source).items():
            name = f"{_ALIASES.get(key, key)}_color"
            _require_field(base, name, f"{source}: [color] {key}")
            fields[name] = value

        for section, (style, pattern) in _STYLES.items():
            for key, table in _table(data, section, source).items():
                name = pattern.format(_ALIASES.get(key, key))
                where = f"{source}: [{section}.{key}]"
                if not hasattr(base, name):
                    raise InvalidParameterError(f"{where}: no such setting ({_choices(base, pattern)})")
                override = _build(style, table, where)
                _set(base, name, override, fields, properties)

        if "legend" in data:
            _set(
                base,
                "legend",
                _build(Legend, _table(data, "legend", source), f"{source}: [legend]"),
                fields,
                properties,
            )

        font = _table(data, "font", source)
        extra = set(font) - {"text", "math"}
        if extra:
            raise InvalidParameterError(f"{source}: [font] takes text and math, not {', '.join(sorted(extra))}")
        try:
            text = resolve_font(font.get("text"))
            math_font = resolve_math_font(_resolve(font.get("math"), base_dir))
            fonts = _text_fonts(_table(data, "fonts", source), base_dir, source)
        except InvalidParameterError as error:
            raise InvalidParameterError(f"{source}: {error}") from None
        return cls(theme=_themed(base, fields, properties), font=text, fonts=fonts, math_font=math_font)

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
            "(run `utility-viz init --migrate`; section names are unchanged)",
            stacklevel=stacklevel,
        )
        return legacy
    return None


def active_theme() -> Theme:
    return Config.active().theme


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _builtin_theme_names() -> list[str]:
    return [name for name in themes.__all__ if isinstance(getattr(themes, name, None), Theme)]


def _base_theme(name: str, source: str) -> Theme:
    theme = getattr(themes, str(name), None)
    if not isinstance(theme, Theme):
        choices = ", ".join(_builtin_theme_names())
        raise InvalidParameterError(f"{source}: unknown base theme {name!r}; choose: {choices}")
    return theme


def _table(data: Mapping, key: str, source: str) -> Mapping:
    value = data.get(key, {})
    if not isinstance(value, Mapping):
        raise InvalidParameterError(f"{source}: [{key}] must be a table")
    return value


def _resolve(value: Any, base_dir: Path | None) -> Any:
    """A font path relative to the config file's directory; anything else is returned as it is."""
    if isinstance(value, str) and value and value not in _OLD_MATH_TOKENS:
        path = Path(value).expanduser()
        return path if path.is_absolute() or base_dir is None else base_dir / path
    return value


def _text_fonts(table: Mapping, base_dir: Path | None, source: str) -> TextFonts | None:
    """``[fonts]``: ``sans``, ``serif`` and ``mono``, each a font file or a list of them."""
    extra = set(table) - {"sans", "serif", "mono"}
    if extra:
        raise InvalidParameterError(f"[fonts] takes sans, serif and mono, not {', '.join(sorted(extra))}")
    slots: dict[str, list[Path]] = {}
    for slot, files in table.items():
        files = [files] if isinstance(files, str) else files
        if not isinstance(files, list) or not files or not all(isinstance(f, str) and f for f in files):
            raise InvalidParameterError(f"[fonts] {slot} must be a font file or a non-empty list of them")
        slots[slot] = [_resolve(f, base_dir) for f in files]
    if not slots:
        return None
    try:
        return TextFonts(**{slot: tuple(files) for slot, files in slots.items()})
    except ConfigurationError as error:
        raise InvalidParameterError(f"[fonts] {error}") from None


def _require_field(theme: Theme, name: str, where: str) -> None:
    if name not in {field.name for field in dataclasses.fields(theme)}:
        colours = sorted(f.name[: -len("_color")] for f in dataclasses.fields(theme) if f.name.endswith("_color"))
        raise InvalidParameterError(f"{where}: no such colour; choose: {', '.join(colours)}")


def _choices(theme: Theme, pattern: str) -> str:
    suffix = pattern.format("")
    names = sorted(
        name[: -len(suffix)]
        for name in dir(theme)
        if name.endswith(suffix) and not name.startswith("_") and name != suffix.lstrip("_")
    )
    return "choose: " + ", ".join(names)


def _build(style, table, where: str):
    if not isinstance(table, Mapping):
        raise InvalidParameterError(f"{where} must be a table")
    try:
        return style(**table)
    except TypeError as error:
        allowed = ", ".join(f.name for f in dataclasses.fields(style))
        raise InvalidParameterError(f"{where}: {error}; fields: {allowed}") from None
    except InvalidParameterError as error:
        raise InvalidParameterError(f"{where}: {error}") from None


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


def template() -> str:
    """A commented ``econ-viz.toml`` listing every setting name."""
    theme = themes.default

    def names(pattern: str) -> str:
        return _choices(theme, pattern).removeprefix("choose: ")

    colours = sorted(f.name[: -len("_color")] for f in dataclasses.fields(theme) if f.name.endswith("_color"))
    base_choices = ", ".join(_builtin_theme_names())
    return f"""# EconViz settings, shared by every EconViz package. Load with:  Config.load("econ-viz.toml").use()
# or on the command line:          utility-viz plot --config econ-viz.toml ...
# Anything left out keeps the built-in default; delete what you don't need.

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
# One of: {", ".join(colours)}
# ic = "#377EB8"

# [stroke.<name>]: width, style, color, arrow, opacity
# <name>: {names("{}_stroke")}
[stroke.budget]
# width = 1.5
# style = "solid"                # solid, dashed, dotted, dashdot

# [marker.<name>]: color, size, shape, opacity
# <name>: {names("{}_marker")}
[marker.eq]
# size = 4

# [label.<name>]: position, offset, color, fontsize, visible, opacity
# <name>: {names("{}_label")}
[label.point]
# fontsize = 12
# position = "top-right"         # top, bottom, left, right, or a corner

# [fill.<name>]: color, opacity
[fill.budget]
# opacity = 0.08

[legend]                         # position, fontsize, frame, columns, visible, opacity
# position = "auto"              # auto, upper right, ..., top, bottom, left, right

# Other EconViz packages read base, [font], [fonts] and the background, axis and
# label colours above, and keep their own settings in one table each, for example
# [principle.color]. utility-viz skips those tables.
"""
