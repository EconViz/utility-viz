"""``plot`` sub-command — generate and export an economic diagram."""

from __future__ import annotations

import argparse

from utility_viz.cli.errors import CliConfigError
from utility_viz.cli.resolve import build_model, resolve_theme


def cmd_plot(args: argparse.Namespace) -> None:
    """Run the ``plot`` sub-command.

    Builds a :class:`~utility_viz.Canvas`, optionally adds indifference
    curves, a budget line, and an equilibrium point, then either saves
    the figure to *args.output* or opens an interactive window.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments produced by :func:`~utility_viz.cli.main.build_parser`.
    """
    from utility_viz.core.canvas import Canvas
    from utility_viz.models.analysis import levels as lvl_mod
    from utility_viz.models.optimization import solve

    if args.model is None and args.latex is None:
        raise CliConfigError("provide --model <name> or --latex <expr>")

    model = build_model(args)
    font = fonts = math_font = config = None
    config_path = args.config
    if not config_path:
        from utility_viz.core.config.settings import find_config_file

        found = find_config_file()  # econ-viz.toml, then legacy utility-viz.toml (warns), else None
        config_path = str(found) if found is not None else None
    if config_path:
        config = _load_config(config_path, args.theme)
        theme, font, fonts, math_font = config.theme, config.font, config.fonts, config.math_font
    else:
        theme = resolve_theme(args.theme or "default")

    cvs = Canvas(
        font=font,
        fonts=fonts,
        math_font=math_font,
        x_max=args.x_max,
        y_max=args.y_max,
        x_label=args.x_label,
        y_label=args.y_label,
        title=args.title,
        dpi=args.dpi,
        theme=theme,
    )

    eq = _maybe_solve(args, model, solve)

    if not args.no_curves:
        lvls = _compute_levels(args, model, eq, lvl_mod)
        cvs.add_utility(model, levels=lvls)

    if not args.no_budget and _has_prices(args):
        cvs.add_budget(args.px, args.py, args.income, fill=args.fill)

    if not args.no_equilibrium and eq is not None:
        cvs.add_equilibrium(eq, show_ray=args.show_ray)

    if args.output:
        try:
            if config is not None:
                config.use()  # also activates the file's [figure.<stem>.label."<id>"] overrides for save()
            cvs.save(args.output)
        finally:
            if config is not None:
                config.reset()
        print(f"Saved to {args.output}")
    else:
        cvs.show()


def _load_config(path: str, theme_name: str | None):
    """Read *path*; an explicit ``--theme`` replaces the file's ``base``."""
    from pathlib import Path

    from utility_viz.core.config.settings import Config, read_file
    from utility_viz.core.errors.exceptions import InvalidParameterError

    try:
        data = read_file(path)
        if theme_name:
            data["base"] = theme_name.lower()
        return Config.from_dict(data, source=path, base_dir=Path(path).parent)
    except InvalidParameterError as error:
        raise CliConfigError(str(error)) from None


def _has_prices(args: argparse.Namespace) -> bool:
    """Return True when px, py, and income are all provided."""
    return args.px is not None and args.py is not None and args.income is not None


def _maybe_solve(args: argparse.Namespace, model, solve_fn):
    """Solve for the consumer optimum when prices and income are available.

    Returns ``None`` when prices are missing or ``--no-equilibrium`` is set.
    """
    if args.no_equilibrium or not _has_prices(args):
        return None
    return solve_fn(model, px=args.px, py=args.py, income=args.income)


def _compute_levels(args: argparse.Namespace, model, eq, lvl_mod) -> list[float]:
    """Compute indifference-curve utility levels.

    Uses :func:`~utility_viz.models.analysis.levels.around` when an equilibrium is available,
    otherwise falls back to :func:`~utility_viz.models.analysis.levels.percentile`.
    """
    if eq is not None:
        return lvl_mod.around(eq.utility, n=args.n_curves)

    import numpy as np

    x_pts = np.linspace(1e-3, args.x_max, 200)
    y_pts = np.linspace(1e-3, args.y_max, 200)
    X, Y = np.meshgrid(x_pts, y_pts)
    Z = model(X, Y)
    return lvl_mod.percentile(Z, n=args.n_curves)
