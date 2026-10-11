"""Generate Edgeworth box examples for common utility-function combinations."""

from pathlib import Path
from typing import Any

import numpy as np

from utility_viz import EdgeworthBox, EquilibriumFocusConfig, Legend, themes
from utility_viz.models import (
    CES,
    CobbDouglas,
    CustomUtility,
    Leontief,
    PerfectSubstitutes,
    QuasiLinear,
    StoneGeary,
)

OUTPUT_DIR = Path("examples/output/edgeworth")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _render_case(
    *,
    filename: str,
    title: str,
    utility_a,
    utility_b,
    total_x: float,
    total_y: float,
    endowment: tuple[float, float],
    prices: tuple[float, float],
    contract_method: str = "auto",
) -> None:
    px, py = prices
    ex, ey = endowment
    box = EdgeworthBox(
        utility_a,
        utility_b,
        total_x=total_x,
        total_y=total_y,
        title=title,
        utility_a_color=themes.default.ic_color,
        utility_b_color=themes.COLORBLIND_CYCLE_HEX[1],
    )
    (
        box.add_endowment(ex, ey)
        .add_contract_curve(n=100, method=contract_method)
        .add_core()
        .add_price_line(px=px, py=py)
        .add_walrasian_equilibrium(px=px, py=py)
        .apply_equilibrium_focus(
            px=px,
            py=py,
            config=EquilibriumFocusConfig(
                include_endowment_indifference="auto",
                min_relative_gap=0.28,
                equilibrium_linewidth=2.0,
                endowment_linewidth=1.6,
                res=300,
            ),
        )
        .show_legend(Legend(position="right"))
        .save(str(OUTPUT_DIR / filename))
    )


def _min_piecewise() -> CustomUtility:
    """U(x, y) = min(2x+y, x+3y)."""
    return CustomUtility(
        func=lambda x, y: np.minimum(2.0 * x + y, x + 3.0 * y),
        name="min(2x+y, x+3y)",
    )


def build_all_cases() -> None:
    cases: list[dict[str, Any]] = [
        {
            "filename": "edgeworth_cobb_asymmetric.png",
            "title": "Edgeworth: Asymmetric Cobb-Douglas",
            "utility_a": CobbDouglas(alpha=0.8, beta=0.2),
            "utility_b": CobbDouglas(alpha=0.2, beta=0.8),
            "total_x": 12.0,
            "total_y": 10.0,
            "endowment": (5.0, 4.0),
            "prices": (1.2, 1.0),
            "contract_method": "mrs",
        },
        {
            "filename": "edgeworth_cobb_symmetric.png",
            "title": "Edgeworth: Symmetric Cobb-Douglas",
            "utility_a": CobbDouglas(alpha=0.5, beta=0.5),
            "utility_b": CobbDouglas(alpha=0.5, beta=0.5),
            "total_x": 10.0,
            "total_y": 10.0,
            "endowment": (5.0, 5.0),
            "prices": (1.0, 1.0),
            "contract_method": "mrs",
        },
        {
            "filename": "edgeworth_ces.png",
            "title": "Edgeworth: CES vs CES",
            "utility_a": CES(alpha=0.6, beta=0.4, rho=0.2),
            "utility_b": CES(alpha=0.4, beta=0.6, rho=0.2),
            "total_x": 12.0,
            "total_y": 10.0,
            "endowment": (6.0, 3.5),
            "prices": (1.1, 1.0),
            "contract_method": "mrs",
        },
        {
            "filename": "edgeworth_perfect_substitutes.png",
            "title": "Edgeworth: Perfect Substitutes",
            "utility_a": PerfectSubstitutes(a=1.0, b=1.0),
            "utility_b": PerfectSubstitutes(a=1.2, b=0.8),
            "total_x": 10.0,
            "total_y": 10.0,
            "endowment": (4.0, 6.0),
            "prices": (1.0, 1.0),
            "contract_method": "pareto",
        },
        {
            "filename": "edgeworth_leontief.png",
            "title": "Edgeworth: Leontief",
            "utility_a": Leontief(a=1.0, b=1.0),
            "utility_b": Leontief(a=1.0, b=1.0),
            "total_x": 10.0,
            "total_y": 10.0,
            "endowment": (6.0, 4.0),
            "prices": (1.0, 1.0),
            "contract_method": "pareto",
        },
        {
            "filename": "edgeworth_quasi_linear.png",
            "title": "Edgeworth: Quasi-Linear",
            "utility_a": QuasiLinear(v_func=np.log, linear_in="y"),
            "utility_b": QuasiLinear(v_func=np.log, linear_in="y"),
            "total_x": 10.0,
            "total_y": 10.0,
            "endowment": (4.5, 5.5),
            "prices": (1.0, 1.0),
            "contract_method": "mrs",
        },
        {
            "filename": "edgeworth_stone_geary.png",
            "title": "Edgeworth: Stone-Geary",
            "utility_a": StoneGeary(alpha=0.5, beta=0.5, bar_x=1.0, bar_y=1.0),
            "utility_b": StoneGeary(alpha=0.4, beta=0.6, bar_x=0.8, bar_y=1.2),
            "total_x": 12.0,
            "total_y": 10.0,
            "endowment": (5.5, 4.0),
            "prices": (1.2, 1.0),
            "contract_method": "mrs",
        },
        {
            "filename": "edgeworth_min_piecewise.png",
            "title": r"Edgeworth: $U=\min(2x+y,\ x+3y)$",
            "utility_a": _min_piecewise(),
            "utility_b": _min_piecewise(),
            "total_x": 10.0,
            "total_y": 10.0,
            "endowment": (4.0, 5.0),
            "prices": (1.0, 1.0),
            "contract_method": "pareto",
        },
    ]

    for case in cases:
        _render_case(**case)


if __name__ == "__main__":
    build_all_cases()
