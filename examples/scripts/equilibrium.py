"""Plot indifference curves with budget constraints and equilibrium solutions.

Workflow: solve → compute levels from solution → draw.
The levels module ensures the equilibrium IC is always one of the drawn curves.
"""

from pathlib import Path

from utility_viz import Canvas, levels, solve
from utility_viz.models import CES, CobbDouglas, Leontief, PerfectSubstitutes

OUTPUT_DIR = "examples/output/equilibrium"
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

models = [
    ("cobb_douglas_eq", CobbDouglas(0.5, 0.5)),
    ("leontief_eq", Leontief(2, 3)),
    ("perfect_substitutes_eq", PerfectSubstitutes(1, 2)),
    ("ces_eq", CES(0.5, 0.5, 0.5)),
]

px, py, income = 2.0, 3.0, 30.0

for name, model in models:
    eq = solve(model, px, py, income)
    lvls = levels.around(eq.utility, n=5)

    cvs = Canvas(x_max=20, y_max=15, x_label="Pizza", y_label="Cola")
    cvs.add_utility(model, levels=lvls, show_rays=True, show_kinks=True)
    cvs.add_budget(px, py, income, fill=True)
    cvs.add_equilibrium(eq, show_ray=True)
    cvs.save(f"{OUTPUT_DIR}/{name}.png")
