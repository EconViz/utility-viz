"""Machinery behind the ``econ_viz`` 1.x compatibility layer (removed in 3.0).

* ``shim(name)`` returns a subclass of the 2.x class that emits one
  :class:`~utility_viz.UtilityVizDeprecationWarning` per construction.
* ``install_finder()`` makes documented 1.x import paths such as
  ``econ_viz.models`` or ``econ_viz.optimizer`` resolve to their 2.x modules.
"""

from __future__ import annotations

import importlib
import importlib.abc
import importlib.machinery
import sys
from types import ModuleType
from typing import Any

from utility_viz.core.errors.deprecation import warn_deprecated

LEGACY = "econ_viz"
TARGET = "utility_viz"

# name -> (module path of the 2.x class, class name, replacement text for the warning)
_SHIMMED: dict[str, tuple[str, str, str]] = {
    "Canvas": ("utility_viz.core.canvas.base", "Canvas", "utility_viz.Canvas"),
    "Figure": (
        "utility_viz.core.layout.figure",
        "Figure",
        "utility_viz.Figure (planned replacement: utility_viz.CanvasGrid)",
    ),
    "Animator": (
        "utility_viz.core.animation.animator",
        "Animator",
        "utility_viz.core.animation.Animator (planned replacement: utility_viz.Animation)",
    ),
}
# Legacy names that warn when accessed instead of constructed (enums cannot be "constructed").
_WARN_ON_ACCESS: dict[str, str] = {
    "Layout": "utility_viz.Layout (planned replacement: utility_viz.CanvasGrid layouts)",
}

_shim_cache: dict[str, type] = {}


class _LegacyMeta(type):
    """Make ``isinstance``/``issubclass`` symmetric between a shim and its 2.x base class."""

    def __instancecheck__(cls, instance: Any) -> bool:
        if cls.__dict__.get("_legacy_shim"):
            return isinstance(instance, cls.__mro__[1])
        return type.__instancecheck__(cls, instance)

    def __subclasscheck__(cls, subclass: Any) -> bool:
        if cls.__dict__.get("_legacy_shim"):
            return issubclass(subclass, cls.__mro__[1])
        return type.__subclasscheck__(cls, subclass)


def shim(name: str) -> type:
    """Return the cached deprecated subclass for a legacy class *name*."""
    if name in _shim_cache:
        return _shim_cache[name]
    module_name, attr, replacement = _SHIMMED[name]
    base = getattr(importlib.import_module(module_name), attr)
    old = f"{LEGACY}.{name}"

    def __init__(self: Any, *args: Any, **kwargs: Any) -> None:
        warn_deprecated(old, replacement, stacklevel=2)
        base.__init__(self, *args, **kwargs)

    __init__.__doc__ = base.__init__.__doc__
    cls = _LegacyMeta(
        name,
        (base,),
        {"__init__": __init__, "__module__": LEGACY, "__doc__": base.__doc__, "_legacy_shim": True},
    )
    _shim_cache[name] = cls
    return cls


def legacy_attr(name: str) -> Any:
    """Resolve a legacy root-level name, or raise :class:`AttributeError`."""
    if name in _SHIMMED:
        return shim(name)
    target = importlib.import_module(TARGET)
    if name in _WARN_ON_ACCESS:
        warn_deprecated(f"{LEGACY}.{name}", _WARN_ON_ACCESS[name], stacklevel=3)
    try:
        return getattr(target, name)
    except AttributeError:
        pass
    try:  # legacy sub-module such as ``econ_viz.parser`` / ``econ_viz.figure``
        return importlib.import_module(f"{LEGACY}.{name}")
    except ImportError:
        raise AttributeError(f"module {LEGACY!r} has no attribute {name!r}") from None


# --- legacy module path -> 2.x module path ---------------------------------------------------------
# Longest prefix wins. Names in ``_REAL`` are implemented as real modules and are never aliased.
_MODULE_MAP: list[tuple[str, str]] = [
    ("exceptions", "core.errors.exceptions"),
    ("config", "core.config.settings"),
    ("constants", "core.constants"),
    ("io", "core.export"),
    ("themes.axis", "core.styles.axis"),
    ("themes.fill", "core.styles.fill"),
    ("themes.label", "core.styles.label"),
    ("themes.legend", "core.styles.legend"),
    ("themes.marker", "core.styles.marker"),
    ("themes.opacity", "core.styles.opacity"),
    ("themes.stroke", "core.styles.stroke"),
    ("themes.theme", "core.themes.theme"),
    ("themes", "core.themes"),
    ("canvas.base", "core.canvas.base"),
    ("canvas.figure", "core.layout.figure"),
    ("canvas.labels", "core.rendering.labels"),
    ("canvas.effect", "core.rendering.effect"),
    ("canvas.layers", "models.curves.layers"),
    ("components", "core.diagrams.components"),
    ("consumer.demand", "core.diagrams.consumer.demand"),
    ("consumer.edgeworth_compute", "models.consumer.edgeworth_compute"),
    ("consumer.edgeworth_state", "models.consumer.edgeworth_state"),
    ("consumer.paths", "models.consumer.paths"),
    ("consumer.edgeworth", "core.diagrams.consumer.edgeworth"),
    ("contours", "models.curves"),
    ("models", "models.utility"),
    ("optimizer", "models.optimization"),
    ("analysis", "models.analysis"),
    ("animation", "core.animation"),
    ("interactive", "core.interactive"),
    ("levels", "models.analysis.levels"),
    ("parser", "models.utility.parser"),
    ("logging", "utils.logging"),
    ("enums", "enums"),
    ("utils", "utils"),
    ("cli", "cli"),
]
_MODULE_MAP.sort(key=lambda item: -len(item[0].split(".")))
# ``econ_viz.models`` is the documented import for every utility model; the 2.x facade provides it.
_EXACT = {"models": "models"}
# Modules implemented for real in this distribution (they add deprecation shims).
_REAL = {"canvas", "animation", "consumer", "figure", "cli", "_legacy"}


def target_for(tail: str) -> str | None:
    """Map a legacy dotted tail (``"models.core"``) to its 2.x module name, or ``None``."""
    if tail in _EXACT:
        return f"{TARGET}.{_EXACT[tail]}"
    parts = tail.split(".")
    for old, new in _MODULE_MAP:
        old_parts = old.split(".")
        if parts[: len(old_parts)] == old_parts:
            return ".".join([TARGET, *new.split("."), *parts[len(old_parts) :]])
    return None


class _AliasLoader(importlib.abc.Loader):
    def __init__(self, target: str) -> None:
        self.target = target
        self._spec: Any = None

    def create_module(self, spec: importlib.machinery.ModuleSpec) -> ModuleType:
        module = importlib.import_module(self.target)
        self._spec = getattr(module, "__spec__", None)
        return module

    def exec_module(self, module: ModuleType) -> None:
        # The import system overwrote __spec__ with the alias spec; restore the real one.
        if self._spec is not None:
            module.__spec__ = self._spec


class LegacyFinder(importlib.abc.MetaPathFinder):
    """Resolve ``econ_viz.<legacy path>`` to the matching ``utility_viz`` module."""

    def find_spec(self, fullname: str, path: Any = None, target: Any = None):
        if not fullname.startswith(LEGACY + "."):
            return None
        tail = fullname[len(LEGACY) + 1 :]
        if tail in _REAL:
            return None
        mapped = target_for(tail)
        if mapped is None:
            return None
        return importlib.machinery.ModuleSpec(fullname, _AliasLoader(mapped))


def install_finder() -> None:
    if not any(isinstance(f, LegacyFinder) for f in sys.meta_path):
        sys.meta_path.insert(0, LegacyFinder())
