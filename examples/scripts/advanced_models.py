"""Demonstrate CustomUtility and MultiGoodCD with the freeze() projection.

Workflow
--------
1. CustomUtility — wrap a raw lambda and draw its indifference map.
2. MultiGoodCD — define a 3-good Cobb-Douglas, freeze z=10, then draw
   the resulting 2-D slice exactly like any standard model.
3. Show intentional error: freeze leaving ≠ 2 active variables.
"""

from pathlib import Path

import numpy as np

from utility_viz import Canvas, levels, solve
from utility_viz.models import CustomUtility, MultiGoodCD

OUTPUT_DIR = "examples/output/models/advanced"
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

px, py, income = 2.0, 3.0, 30.0

print("=== CustomUtility ===")
model = CustomUtility(func=lambda x, y: np.log(x) + np.log(y), name="log+log")
print(f"  model       : {model!r}")
print(f"  u(2, 3)     : {model(2.0, 3.0):.4f}")

eq = solve(model, px, py, income)
lvls = levels.around(eq.utility, n=5)
print(f"  equilibrium : x={eq.x:.3f}, y={eq.y:.3f}, U={eq.utility:.4f}")

cvs = Canvas(x_max=20, y_max=15, x_label="x", y_label="y", title=r"Custom Utility: $\ln(x) + \ln(y)$")
cvs.add_utility(model, levels=lvls)
cvs.add_budget(px, py, income, fill=True)
cvs.add_equilibrium(eq, show_ray=True)
cvs.save(f"{OUTPUT_DIR}/advanced_custom.png")
print(f"  saved → {OUTPUT_DIR}/advanced_custom.png\n")

print("=== MultiGoodCD — 3 goods ===")
m3 = MultiGoodCD({"x": 0.3, "y": 0.3, "z": 0.4})
print(f"  model       : {m3!r}")

flat = m3.freeze(z=10.0)
print(f"  freeze(z=10): {flat!r}")
print(f"  flat(2, 3)  : {flat(2.0, 3.0):.4f}")

eq2 = solve(flat, px, py, income)
lvls2 = levels.around(eq2.utility, n=5)
print(f"  equilibrium : x={eq2.x:.3f}, y={eq2.y:.3f}, U={eq2.utility:.4f}")

cvs2 = Canvas(x_max=20, y_max=15, x_label="x", y_label="y", title=r"MultiGoodCD  $z=10$")
cvs2.add_utility(flat, levels=lvls2)
cvs2.add_budget(px, py, income, fill=True)
cvs2.add_equilibrium(eq2, show_ray=True)
cvs2.save(f"{OUTPUT_DIR}/advanced_multigd.png")
print(f"  saved → {OUTPUT_DIR}/advanced_multigd.png\n")

print("=== MultiGoodCD — 4 goods, freeze two ===")
m4 = MultiGoodCD({"x": 0.25, "y": 0.25, "z": 0.25, "w": 0.25})
flat4 = m4.freeze(z=5.0, w=8.0)
print(f"  freeze(z=5, w=8): {flat4!r}")

cvs3 = Canvas(x_max=20, y_max=15, x_label="x", y_label="y", title=r"MultiGoodCD  $z=5,\ w=8$")
cvs3.add_utility(flat4, levels=5)
cvs3.save(f"{OUTPUT_DIR}/advanced_multigd4.png")
print(f"  saved → {OUTPUT_DIR}/advanced_multigd4.png\n")

print("=== Error: bad func (scalar, not vectorised) ===")
try:
    CustomUtility(func=lambda x, y: float(x) + float(y), name="bad")
except ValueError as exc:
    print(f"  Caught ValueError: {exc}\n")

print("=== Error: freeze leaves ≠ 2 active variables ===")
try:
    m3.freeze(y=5.0, z=10.0)
except ValueError as exc:
    print(f"  Caught ValueError: {exc}\n")
