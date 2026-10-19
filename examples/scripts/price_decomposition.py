"""Generate batch price-effect decomposition examples."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from utility_viz import Canvas
from utility_viz.models import (
    CES,
    CobbDouglas,
    CustomUtility,
    Leontief,
    PerfectSubstitutes,
    QuasiLinear,
    StoneGeary,
    Translog,
)
from utility_viz.models.optimization import DecompositionMethod, decompose_price_effect

OUTPUT_DIR = Path("examples/output/decom")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _axis_limits(decomposition) -> tuple[float, float]:
    max_x = max(
        decomposition.A.x,
        decomposition.B.x,
        decomposition.C.x,
        decomposition.income / min(decomposition.px_before, decomposition.px_after),
        decomposition.compensated_income / decomposition.px_after,
    )
    max_y = max(
        decomposition.A.y,
        decomposition.B.y,
        decomposition.C.y,
        decomposition.income / decomposition.py,
        decomposition.compensated_income / decomposition.py,
    )
    return max_x * 1.25, max_y * 1.35


def _save_case(
    *,
    model,
    model_slug: str,
    model_label: str,
    method: DecompositionMethod,
    px: tuple[float, float],
    py: float,
    income: float,
) -> None:
    decomposition = decompose_price_effect(
        model,
        px=px,
        py=py,
        income=income,
        method=method,
    )
    x_max, y_max = _axis_limits(decomposition)
    canvas = Canvas(
        x_max=x_max,
        y_max=y_max,
        x_label="x",
        y_label="y",
        title=f"{model_label} - {method.name.title()} decomposition",
    )
    # The curves through A and C (and B for Slutsky) are drawn by default.
    canvas.add_decomposition(
        decomposition,
        show_arrows=True,
        label_effects=True,
        show_x_projections=True,
    )
    canvas.save(str(OUTPUT_DIR / f"{model_slug}_{method.value}.png"))


def build_examples() -> None:
    px = (2.0, 4.0)
    py = 3.0
    income = 60.0

    min_piecewise = CustomUtility(
        func=lambda x, y: np.minimum(2.0 * x + y, x + 3.0 * y),
        name="min(2x+y, x+3y)",
    )

    cases = [
        (
            "cobb_douglas",
            "Cobb-Douglas",
            CobbDouglas(alpha=0.5, beta=0.5),
            [DecompositionMethod.SLUTSKY, DecompositionMethod.HICKS],
        ),
        ("ces", "CES", CES(alpha=0.5, beta=0.5, rho=0.5), [DecompositionMethod.SLUTSKY, DecompositionMethod.HICKS]),
        (
            "quasi_linear",
            "Quasi-linear",
            QuasiLinear(v_func=np.log, linear_in="y"),
            [DecompositionMethod.SLUTSKY, DecompositionMethod.HICKS],
        ),
        (
            "stone_geary",
            "Stone-Geary",
            StoneGeary(alpha=0.5, beta=0.5, bar_x=1.0, bar_y=1.0),
            [DecompositionMethod.SLUTSKY, DecompositionMethod.HICKS],
        ),
        ("leontief", "Leontief", Leontief(a=1.0, b=1.0), [DecompositionMethod.SLUTSKY]),
        ("perfect_substitutes", "Perfect Substitutes", PerfectSubstitutes(a=1.0, b=2.0), [DecompositionMethod.SLUTSKY]),
        (
            "translog",
            "Translog",
            Translog(alpha_x=0.45, alpha_y=0.55, beta_xx=-0.03, beta_yy=-0.02, beta_xy=0.01),
            [DecompositionMethod.SLUTSKY],
        ),
        ("min_2x_plus_y_x_plus_3y", "min(2x+y, x+3y)", min_piecewise, [DecompositionMethod.SLUTSKY]),
    ]

    for model_slug, model_label, model, methods in cases:
        for method in methods:
            try:
                _save_case(
                    model=model,
                    model_slug=model_slug,
                    model_label=model_label,
                    method=method,
                    px=px,
                    py=py,
                    income=income,
                )
                print(f"[ok] {model_slug} ({method.value})")
            except Exception as exc:  # pragma: no cover - example robustness
                print(f"[skip] {model_slug} ({method.value}): {exc}")


if __name__ == "__main__":
    build_examples()
