"""Model and theme resolution helpers for the CLI."""

from __future__ import annotations

import argparse

from utility_viz.cli.errors import CliConfigError


def build_model(args: argparse.Namespace):
    """Instantiate the utility model specified by CLI arguments.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments.  Either ``args.latex`` or ``args.model``
        must be set.

    Returns
    -------
    UtilityFunction
        A concrete model conforming to the ``UtilityFunction`` protocol.
    """
    from utility_viz.models.utility.parser import parse_latex
    from utility_viz.models.utility.registry import build_registered_model, get_model_registry

    if args.latex:
        return parse_latex(args.latex)

    name = (args.model or "").lower()
    registry = get_model_registry()
    if name not in registry:
        raise CliConfigError(f"unknown model '{args.model}'. Run `utility-viz models` to see available models.")
    try:
        return build_registered_model(name, args)
    except ValueError as exc:
        raise CliConfigError(str(exc)) from exc


_THEMES: dict[str, object] | None = None


def _themes_map() -> dict[str, object]:
    """Return the name→Theme mapping, loading themes lazily."""
    global _THEMES
    if _THEMES is None:
        import utility_viz.core.themes as themes

        _THEMES = {name: themes.build_theme(name) for name in themes.THEME_NAMES}
        _THEMES["dark"] = themes.dark
    return _THEMES


def resolve_theme(name: str):
    """Look up a theme by name.

    Parameters
    ----------
    name : str
        Theme name (case-insensitive).

    Returns
    -------
    Theme
        The matching theme instance.
    """
    mapping = _themes_map()
    theme = mapping.get(name.lower())
    if theme is None:
        available = ", ".join(mapping)
        raise CliConfigError(f"unknown theme '{name}'. Available: {available}")
    return theme
