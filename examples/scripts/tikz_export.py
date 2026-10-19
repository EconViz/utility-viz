"""Generate standalone pure-TikZ export examples."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import numpy as np

from utility_viz import Canvas, levels, solve
from utility_viz.core.scenes import canvas_to_tikz
from utility_viz.models import (
    CES,
    CobbDouglas,
    CustomUtility,
    Leontief,
    MultiGoodCD,
    PerfectSubstitutes,
    QuasiLinear,
    Satiation,
    StoneGeary,
    Translog,
)

OUTPUT_DIR = Path("examples/output/tikz")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PX, PY, INCOME = 2.0, 3.0, 30.0
MAIN_TEX = OUTPUT_DIR / "main.tex"
_OLD_SINGLE_FILES = {
    "ces",
    "cobb_douglas",
    "leontief",
    "min_piecewise",
    "multigood_projection",
    "perfect_substitutes",
    "quasi_linear",
    "satiation",
    "stone_geary",
    "translog",
}


def _min_piecewise() -> CustomUtility:
    """U(x, y) = min(2x+y, x+3y)."""
    return CustomUtility(
        func=lambda x, y: np.minimum(2.0 * x + y, x + 3.0 * y),
        name="min(2x+y, x+3y)",
    )


def _multigood_projection() -> CustomUtility:
    """U(x, y, z) = x^0.3 y^0.3 z^0.4 with z fixed."""
    return MultiGoodCD({"x": 0.3, "y": 0.3, "z": 0.4}).freeze(z=8.0)


def _draw_budget_equilibrium(canvas: Canvas, model) -> None:
    try:
        eq = solve(model, PX, PY, INCOME)
    except Exception:
        canvas.add_budget(PX, PY, INCOME, fill=True)
        return

    canvas.add_budget(PX, PY, INCOME, fill=True)
    canvas.add_equilibrium(eq, show_ray=True)


def _cleanup_old_outputs() -> None:
    for stem in _OLD_SINGLE_FILES:
        for suffix in (".tex", ".pdf", ".aux", ".log"):
            (OUTPUT_DIR / f"{stem}{suffix}").unlink(missing_ok=True)


def _build_case(
    *,
    title: str,
    model,
    x_max: float = 20.0,
    y_max: float = 15.0,
    level_spec: int | list[float] | None = None,
    show_budget: bool = True,
    configure: Callable[[Canvas], None] | None = None,
) -> Canvas:
    canvas = Canvas(x_max=x_max, y_max=y_max, x_label="Pizza", y_label="Cola", title=title)
    if level_spec is None:
        if show_budget:
            try:
                eq = solve(model, PX, PY, INCOME)
                level_spec = levels.around(eq.utility, n=5)
            except Exception:
                level_spec = 5
        else:
            level_spec = 5
    canvas.add_utility(
        model,
        levels=level_spec,
        show_rays=True,
        show_kinks=True,
    )
    if configure is not None:
        configure(canvas)
    if show_budget:
        _draw_budget_equilibrium(canvas, model)
    return canvas


def _case_snippet(label: str, canvas: Canvas) -> str:
    snippet = canvas_to_tikz(canvas, standalone=False)
    return "\n".join(
        [
            rf"% {label}",
            r"\begingroup",
            snippet.rstrip(),
            r"\endgroup",
        ]
    )


def _write_multi_standalone(cases: list[tuple[str, Canvas]]) -> None:
    snippets = [_case_snippet(label, canvas) for label, canvas in cases]
    document = "\n\n".join(
        [
            r"\documentclass[multi=tikzpicture,border=8pt]{standalone}",
            r"\usepackage{tikz}",
            r"\usetikzlibrary{arrows.meta}",
            r"\usepackage{amsmath}",
            r"\begin{document}",
            *snippets,
            r"\end{document}",
            "",
        ]
    )
    MAIN_TEX.write_text(document, encoding="utf-8")


def build_examples() -> None:
    """Write one multi-page standalone TikZ document with representative models."""
    _cleanup_old_outputs()
    main_model = CobbDouglas(alpha=0.5, beta=0.5)
    main_eq = solve(main_model, PX, PY, INCOME)

    cases = [
        (
            "main-cobb-douglas-equilibrium",
            _build_case(
                title="Cobb-Douglas equilibrium",
                model=main_model,
                level_spec=levels.around(main_eq.utility, n=5),
            ),
        ),
        ("cobb-douglas", _build_case(title="Cobb-Douglas", model=CobbDouglas(alpha=0.5, beta=0.5))),
        ("leontief", _build_case(title="Leontief", model=Leontief(a=2.0, b=3.0))),
        (
            "perfect-substitutes",
            _build_case(title="Perfect Substitutes", model=PerfectSubstitutes(a=1.0, b=2.0)),
        ),
        ("ces", _build_case(title="CES", model=CES(alpha=0.5, beta=0.5, rho=0.5))),
        (
            "translog",
            _build_case(
                title="Translog",
                model=Translog(alpha_x=0.45, alpha_y=0.55, beta_xx=-0.03, beta_yy=-0.02, beta_xy=0.01),
            ),
        ),
        (
            "quasi-linear",
            _build_case(
                title="Quasi-Linear",
                model=QuasiLinear(v_func=np.log, linear_in="y"),
            ),
        ),
        (
            "stone-geary",
            _build_case(title="Stone-Geary", model=StoneGeary(alpha=0.5, beta=0.5, bar_x=1.0, bar_y=1.0)),
        ),
        (
            "satiation",
            _build_case(
                title="Satiation",
                model=Satiation(bliss_x=8.0, bliss_y=6.0, a=1.0, b=1.5),
                show_budget=False,
                configure=lambda c: c.add_point(8.0, 6.0, label="x^*"),
            ),
        ),
        (
            "min-piecewise",
            _build_case(
                title=r"$U=\min(2x+y,\ x+3y)$",
                model=_min_piecewise(),
            ),
        ),
        (
            "multigood-projection",
            _build_case(title="Multi-Good Cobb-Douglas Projection", model=_multigood_projection()),
        ),
    ]

    _write_multi_standalone(cases)


if __name__ == "__main__":
    build_examples()
