"""Demonstrate multi-panel Figure layouts."""

from pathlib import Path

from mosaickit import TextLayer

from utility_viz import Figure, Layout, levels, solve
from utility_viz.models import CobbDouglas

OUTPUT_DIR = "examples/output/layouts"
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

base = CobbDouglas(alpha=0.5, beta=0.5)
alt = CobbDouglas(alpha=0.3, beta=0.7)
params = [(2.0, 3.0, 30.0), (4.0, 3.0, 30.0)]

fig = Figure(
    Layout.SIDE_BY_SIDE,
    x_max=20,
    y_max=15,
    x_label="x",
    y_label="y",
    title="Before/After Price Change",
    shared_y=True,
)

for idx, (model, (px, py, income), title) in enumerate(
    [
        (base, params[0], r"Before: $p_x=2$"),
        (alt, params[1], r"After: $p_x=4$"),
    ]
):
    eq = solve(model, px=px, py=py, income=income)
    lvls = levels.around(eq.utility, n=5)
    panel = fig[idx]
    panel.add(
        TextLayer(
            (panel.x_max / 2, panel.y_max),
            title,
            id="panel.title",
            role="title",
            offset=(0, 12),
            anchor="bottom",
        )
    )
    panel.add_utility(model, levels=lvls, label="IC")
    panel.add_budget(px, py, income, fill=True, label="BC")
    panel.add_equilibrium(eq, show_ray=True)

fig[0].show_legend()
fig.save(f"{OUTPUT_DIR}/figure_side_by_side.png")
