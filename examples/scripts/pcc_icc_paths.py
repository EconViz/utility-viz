"""Generate PCC / ICC path examples for common core models."""

from pathlib import Path

import numpy as np

from utility_viz import Canvas, IncomePath, LinearBudget, PricePath
from utility_viz.models import CES, CobbDouglas, Leontief, PerfectSubstitutes, QuasiLinear, StoneGeary

OUTPUT_DIR = "examples/output/paths"
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


def representative_levels(path, n: int = 3) -> list[float]:
    """Pick a few utility levels directly from solved equilibria on the path."""
    if not path.equilibria:
        return [1.0]

    idxs = np.linspace(0, len(path.equilibria) - 1, n, dtype=int)
    levels = [path.equilibria[idx].utility for idx in idxs]
    ordered_unique = list(dict.fromkeys(sorted(levels)))
    return ordered_unique


cases = [
    (
        "cobb_douglas",
        CobbDouglas(alpha=0.5, beta=0.5),
        LinearBudget(px=2.0, py=2.0, income=40.0),
        (0.8, 6.0),
        (10.0, 80.0),
        28.0,
        28.0,
        "Cobb-Douglas",
    ),
    (
        "ces",
        CES(alpha=0.5, beta=0.5, rho=0.25),
        LinearBudget(px=2.0, py=2.0, income=40.0),
        (0.8, 6.0),
        (10.0, 80.0),
        28.0,
        28.0,
        "CES",
    ),
    (
        "perfect_substitutes",
        PerfectSubstitutes(a=1.0, b=1.0),
        LinearBudget(px=2.0, py=2.0, income=40.0),
        (0.8, 6.0),
        (10.0, 80.0),
        55.0,
        55.0,
        "Perfect Substitutes",
    ),
    (
        "leontief",
        Leontief(a=1.0, b=1.0),
        LinearBudget(px=2.0, py=2.0, income=40.0),
        (0.8, 6.0),
        (10.0, 80.0),
        28.0,
        28.0,
        "Leontief",
    ),
    (
        "quasi_linear",
        QuasiLinear(v_func=np.log, linear_in="y"),
        LinearBudget(px=2.0, py=1.0, income=6.0),
        (0.5, 5.0),
        (4.0, 20.0),
        12.0,
        20.0,
        "Quasi-Linear",
    ),
    (
        "stone_geary",
        StoneGeary(alpha=0.5, beta=0.5, bar_x=1.0, bar_y=1.0),
        LinearBudget(px=2.0, py=2.0, income=20.0),
        (0.8, 4.0),
        (8.0, 50.0),
        20.0,
        20.0,
        "Stone-Geary",
    ),
]

for slug, model, budget, price_range, income_range, x_max, y_max, label in cases:
    pcc = PricePath(model, budget=budget, price="px", price_range=price_range, n=40)
    (
        Canvas(x_max=x_max, y_max=y_max, x_label="x", y_label="y", title=f"PCC: {label}")
        .add_utility(model, levels=representative_levels(pcc))
        .add_path(pcc, label="PCC")
        .save(f"{OUTPUT_DIR}/pcc_{slug}.png")
    )

    icc = IncomePath(model, budget=budget, income_range=income_range, n=40)
    (
        Canvas(x_max=x_max, y_max=y_max, x_label="x", y_label="y", title=f"ICC: {label}")
        .add_utility(model, levels=representative_levels(icc))
        .add_path(icc, label="ICC")
        .save(f"{OUTPUT_DIR}/icc_{slug}.png")
    )
