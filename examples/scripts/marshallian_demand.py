"""Generate demand-diagram examples for common core models."""

from pathlib import Path

import numpy as np

from utility_viz import DemandDiagram, LinearBudget, PricePath
from utility_viz.models import CES, CobbDouglas, Leontief, PerfectSubstitutes, QuasiLinear, StoneGeary

OUTPUT_DIR = "examples/output/paths"
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

cases = [
    (
        "demand_cobb_douglas",
        CobbDouglas(alpha=0.5, beta=0.5),
        LinearBudget(px=2.0, py=2.0, income=40.0),
        "px",
        (0.8, 6.0),
        [1.5, 4.0],
        "Demand: Cobb-Douglas",
    ),
    (
        "demand_ces",
        CES(alpha=0.5, beta=0.5, rho=0.25),
        LinearBudget(px=2.0, py=2.0, income=40.0),
        "px",
        (0.8, 6.0),
        [1.5, 4.0],
        "Demand: CES",
    ),
    (
        "demand_leontief",
        Leontief(a=1.0, b=1.0),
        LinearBudget(px=2.0, py=2.0, income=40.0),
        "px",
        (0.8, 6.0),
        [1.5, 4.0],
        "Demand: Leontief",
    ),
    (
        "demand_perfect_substitutes",
        PerfectSubstitutes(a=1.0, b=1.0),
        LinearBudget(px=2.0, py=2.0, income=40.0),
        "px",
        (0.8, 6.0),
        [1.2, 3.0],
        "Demand: Perfect Substitutes (MRS = 1)",
    ),
    (
        "demand_quasi_linear",
        QuasiLinear(v_func=np.log, linear_in="y"),
        LinearBudget(px=2.0, py=1.0, income=2.0),
        "px",
        (0.4, 5.0),
        [0.8, 1.8],
        "Demand: Quasi-Linear",
    ),
    (
        "demand_stone_geary",
        StoneGeary(alpha=0.5, beta=0.5, bar_x=1.0, bar_y=1.0),
        LinearBudget(px=2.0, py=2.0, income=20.0),
        "px",
        (0.8, 4.0),
        [1.2, 3.2],
        "Demand: Stone-Geary",
    ),
]

for filename, model, budget, price, price_range, markers, title in cases:
    path = PricePath(model, budget=budget, price=price, price_range=price_range, n=40)
    fig = DemandDiagram(path, title=title)
    fig.add_marshallian_panel(price_markers=markers, show_pcc=False)
    fig.save(f"{OUTPUT_DIR}/{filename}.png")
