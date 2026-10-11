"""Highlight the equilibrium indifference curve against subdued neighbours.

Renders the same equilibrium diagram before and after highlighting, and once
more with ordinal (`u_1, u_2, u_3`) labels instead of raw utility values.
"""

from pathlib import Path

from utility_viz import Canvas, levels, solve
from utility_viz.models import CobbDouglas

OUTPUT_DIR = "examples/output/ic_hierarchy"
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

model = CobbDouglas(0.5, 0.5)
px, py, income = 2.0, 3.0, 30.0
eq = solve(model, px, py, income)
lvls = levels.around(eq.utility, n=5)

# Before: every indifference curve drawn with the same visual weight.
(
    Canvas(x_max=20, y_max=15, x_label="Pizza", y_label="Cola", title="Before highlighting")
    .add_utility(model, levels=lvls)
    .add_budget(px, py, income, fill=True)
    .add_equilibrium(eq)
    .save(f"{OUTPUT_DIR}/before_highlight.png")
)

# After: the equilibrium level is focal; the rest are subdued automatically.
(
    Canvas(x_max=20, y_max=15, x_label="Pizza", y_label="Cola", title="After highlighting")
    .add_utility(model, levels=lvls, highlight_level=eq.utility)
    .add_budget(px, py, income, fill=True)
    .add_equilibrium(eq)
    .save(f"{OUTPUT_DIR}/after_highlight.png")
)

# Ordinal labels read like a textbook figure: u_1 < u_2 < ... instead of raw values.
(
    Canvas(x_max=20, y_max=15, x_label="Pizza", y_label="Cola", title="Ordinal labels")
    .add_utility(model, levels=lvls, highlight_level=eq.utility, show_ic_labels=True, label_style="ordinal")
    .add_budget(px, py, income, fill=True)
    .add_equilibrium(eq)
    .save(f"{OUTPUT_DIR}/ordinal_labels.png")
)
