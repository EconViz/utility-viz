"""CLI entry point and argument parser for utility-viz."""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import version

from utility_viz.cli.errors import CliConfigError
from utility_viz.cli.help import cmd_help
from utility_viz.cli.init import cmd_init
from utility_viz.cli.models import cmd_models
from utility_viz.cli.plot import cmd_plot
from utility_viz.cli.solve_tex import cmd_solve_tex


def build_parser() -> tuple[argparse.ArgumentParser, dict[str, argparse.ArgumentParser]]:
    """Construct the top-level parser and all sub-command parsers.

    Returns
    -------
    parser : argparse.ArgumentParser
        The root parser.
    subparsers : dict[str, argparse.ArgumentParser]
        Mapping of sub-command name to its individual parser, for use by
        the ``help`` command.
    """
    parser = argparse.ArgumentParser(
        prog="utility-viz",
        description="Produce publication-quality microeconomics diagrams.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {version('utility-viz')}")
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    subparsers: dict[str, argparse.ArgumentParser] = {}

    subparsers["models"] = sub.add_parser("models", help="List available utility models.")
    subparsers["plot"] = _register_plot(sub)
    subparsers["solve-tex"] = _register_solve_tex(sub)
    subparsers["help"] = _register_help(sub)
    subparsers["init"] = _register_init(sub)

    return parser, subparsers


def _register_help(sub) -> argparse.ArgumentParser:
    """Add the ``help`` sub-command to *sub* and return its parser."""
    p = sub.add_parser("help", help="Show help for a command.")
    p.add_argument(
        "topic",
        nargs="?",
        metavar="<command>",
        help="Command to get help on: models, plot, solve-tex.",
    )
    return p


def _add_model_args(p: argparse.ArgumentParser) -> None:
    mgrp = p.add_mutually_exclusive_group()
    mgrp.add_argument(
        "--model",
        "-m",
        metavar="NAME",
        help="Model name: cobb-douglas, leontief, perfect-substitutes, ces, satiation.",
    )
    mgrp.add_argument(
        "--latex",
        "-l",
        metavar="EXPR",
        help=r'LaTeX expression, e.g. "x^{0.5} y^{0.5}" or "\min(2x, 3y)".',
    )

    p.add_argument("--alpha", type=float, metavar="A", help="Alpha parameter.")
    p.add_argument("--beta", type=float, metavar="B", help="Beta parameter.")
    p.add_argument("--a", type=float, metavar="A", help="a parameter (Leontief / PerfectSubs / Satiation).")
    p.add_argument("--b", type=float, metavar="B", help="b parameter (Leontief / PerfectSubs / Satiation).")
    p.add_argument("--rho", type=float, metavar="R", help="Rho parameter (CES).")
    p.add_argument("--bliss-x", dest="bliss_x", type=float, metavar="X", help="Bliss point x (Satiation).")
    p.add_argument("--bliss-y", dest="bliss_y", type=float, metavar="Y", help="Bliss point y (Satiation).")
    p.add_argument("--linear-in", dest="linear_in", choices=("x", "y"), help="Linear good for QuasiLinear.")
    p.add_argument("--v-func", dest="v_func", choices=("log", "sqrt"), help="One-variable transform for QuasiLinear.")
    p.add_argument("--bar-x", dest="bar_x", type=float, metavar="X", help="Subsistence quantity of x (StoneGeary).")
    p.add_argument("--bar-y", dest="bar_y", type=float, metavar="Y", help="Subsistence quantity of y (StoneGeary).")
    p.add_argument("--alpha-0", dest="alpha_0", type=float, metavar="A0", help="Intercept parameter (Translog).")
    p.add_argument("--alpha-x", dest="alpha_x", type=float, metavar="AX", help="x log weight (Translog).")
    p.add_argument("--alpha-y", dest="alpha_y", type=float, metavar="AY", help="y log weight (Translog).")
    p.add_argument("--beta-xx", dest="beta_xx", type=float, metavar="BXX", help="x curvature term (Translog).")
    p.add_argument("--beta-yy", dest="beta_yy", type=float, metavar="BYY", help="y curvature term (Translog).")
    p.add_argument("--beta-xy", dest="beta_xy", type=float, metavar="BXY", help="cross term (Translog).")


def _register_plot(sub) -> argparse.ArgumentParser:
    """Add the ``plot`` sub-command to *sub* and return its parser."""
    p = sub.add_parser("plot", help="Generate a diagram and save or display it.")
    _add_model_args(p)

    p.add_argument("--px", type=float, metavar="P", help="Price of good x.")
    p.add_argument("--py", type=float, metavar="P", help="Price of good y.")
    p.add_argument("--income", type=float, metavar="I", help="Consumer income.")

    p.add_argument("--x-max", dest="x_max", type=float, default=10.0, help="Horizontal axis limit (default 10).")
    p.add_argument("--y-max", dest="y_max", type=float, default=10.0, help="Vertical axis limit (default 10).")
    p.add_argument("--x-label", dest="x_label", type=str, default="x", help="Horizontal axis label (default 'x').")
    p.add_argument("--y-label", dest="y_label", type=str, default="y", help="Vertical axis label (default 'y').")
    p.add_argument("--title", type=str, default=None, help="Figure title.")
    p.add_argument("--dpi", type=int, default=300, help="Output DPI for raster images (default 300).")
    p.add_argument(
        "--theme",
        type=str,
        default=None,
        metavar="NAME",
        help=(
            "Theme name: manual, default, colorblind, monochrome, nord, paper, presentation, dark "
            "(default: default, or the config's base)."
        ),
    )
    p.add_argument(
        "--config", type=str, default=None, metavar="FILE", help="TOML settings file (see 'utility-viz init')."
    )

    p.add_argument(
        "--n-curves", dest="n_curves", type=int, default=5, help="Number of indifference curves (default 5)."
    )
    p.add_argument("--fill", action="store_true", help="Shade the feasible set under the budget line.")
    p.add_argument(
        "--show-ray", dest="show_ray", action="store_true", help="Draw expansion-path ray through the optimum."
    )
    p.add_argument("--no-budget", dest="no_budget", action="store_true", help="Omit the budget line.")
    p.add_argument("--no-equilibrium", dest="no_equilibrium", action="store_true", help="Omit the equilibrium point.")
    p.add_argument("--no-curves", dest="no_curves", action="store_true", help="Omit indifference curves.")

    p.add_argument(
        "--output", "-o", metavar="FILE", help="Output file (.png, .pdf, .svg). Omit to display interactively."
    )

    return p


def _register_init(sub) -> argparse.ArgumentParser:
    """Add the ``init`` sub-command to *sub* and return its parser."""
    p = sub.add_parser("init", help="Write a commented econ-viz.toml settings template.")
    p.add_argument("path", nargs="?", default="econ-viz.toml", help="File to write (default: econ-viz.toml).")
    p.add_argument("--force", action="store_true", help="Overwrite an existing file.")
    p.add_argument(
        "--migrate",
        action="store_true",
        help=(
            "Move utility-viz's top-level settings under [utility]: rewrites utility-viz.toml in the same "
            "directory into econ-viz.toml (the old file is kept), or else econ-viz.toml in place."
        ),
    )
    return p


def _register_solve_tex(sub) -> argparse.ArgumentParser:
    """Add the ``solve-tex`` sub-command to *sub* and return its parser."""
    p = sub.add_parser("solve-tex", help="Print a closed-form Marshallian demand as TeX text.")
    _add_model_args(p)
    p.add_argument("--px-symbol", default=r"p_x", help=r"Symbol for the price of x (default: p_x).")
    p.add_argument("--py-symbol", default=r"p_y", help=r"Symbol for the price of y (default: p_y).")
    p.add_argument("--income-symbol", default="I", help="Symbol for income (default: I).")
    p.add_argument(
        "--symbolic-params",
        action="store_true",
        help=r"Use symbolic model parameters such as \alpha, \beta, a, b, \bar{x}, \bar{y}.",
    )
    return p


def main() -> None:
    """Parse CLI arguments and dispatch to the appropriate sub-command."""
    parser, subparsers = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "help":
            cmd_help(args, parser, subparsers)
        elif args.command == "models":
            cmd_models(args)
        elif args.command == "plot":
            cmd_plot(args)
        elif args.command == "solve-tex":
            cmd_solve_tex(args)
        elif args.command == "init":
            cmd_init(args)
    except CliConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
