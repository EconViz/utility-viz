"""Plot indifference curves for all utility models.

Also demonstrates Satiation and QuasiLinear initialisation, including
an intentional validation failure for QuasiLinear(v_func=lambda z: z**2).
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

from utility_viz.core.canvas.base import Canvas
from utility_viz.models import CES, CobbDouglas, Leontief, PerfectSubstitutes, QuasiLinear, Satiation

OUTPUT_DIR = "examples/output/models"
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# Standard models
# ------------------------------------------------------------------
models: list[tuple[str, Callable[..., Any]]] = [
    ("cobb_douglas", CobbDouglas(0.5, 0.5)),
    ("leontief", Leontief(2, 3)),
    ("perfect_substitutes", PerfectSubstitutes(1, 2)),
    ("ces", CES(0.5, 0.5, 0.5)),
]

for name, model in models:
    cvs = Canvas(x_max=20, y_max=15, x_label="Pizza", y_label="Cola")
    cvs.add_utility(model, levels=5, show_rays=True, show_kinks=True)
    cvs.save(f"{OUTPUT_DIR}/{name}.png")

# ------------------------------------------------------------------
# Satiation — closed elliptical indifference curves
# ------------------------------------------------------------------
print("Initialising Satiation(bliss_x=8, bliss_y=6) ... ", end="")
satiation = Satiation(bliss_x=8, bliss_y=6, a=1.0, b=1.5)
print("OK")

cvs = Canvas(x_max=20, y_max=15, x_label="x", y_label="y", title=r"Satiation: $U = -a(x-x^*)^2 - b(y-y^*)^2$")
cvs.add_utility(satiation, levels=5, show_rays=True)
cvs.save(f"{OUTPUT_DIR}/satiation.png")

# ------------------------------------------------------------------
# QuasiLinear — default np.log (valid)
# ------------------------------------------------------------------
print("Initialising QuasiLinear(v_func=np.log) ... ", end="")
ql = QuasiLinear(v_func=np.log, linear_in="y")
print("OK")

cvs = Canvas(x_max=20, y_max=15, x_label="x", y_label="y", title=r"Quasi-Linear: $U = \ln(x) + y$")
cvs.add_utility(ql, levels=5)
cvs.save(f"{OUTPUT_DIR}/quasi_linear.png")

# ------------------------------------------------------------------
# QuasiLinear — v_func=lambda z: z**2  (must raise ValueError)
# ------------------------------------------------------------------
print("Initialising QuasiLinear(v_func=lambda z: z**2) — expecting ValueError ...")
try:
    QuasiLinear(v_func=lambda z: z**2)
    print("  ERROR: no exception was raised!")
except ValueError as exc:
    print(f"  Caught ValueError: {exc}")
