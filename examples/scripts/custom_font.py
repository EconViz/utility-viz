"""Draw the same consumer equilibrium with the default and a serif font."""

from pathlib import Path

from mosaickit import TextLayer

from utility_viz import Figure, Layout, levels, solve
from utility_viz.models import CobbDouglas

OUTPUT_DIR = Path("examples/output/customization")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

model = CobbDouglas(alpha=0.5, beta=0.5)
eq = solve(model, px=2.0, py=3.0, income=30.0)

# Fallback list: the first installed family is used.
fig = Figure(
    Layout.SIDE_BY_SIDE,
    x_max=20,
    y_max=15,
    title="Consumer equilibrium",
    font=["Times New Roman", "DejaVu Serif", "serif"],
    math_font="stix",
)
for panel, title in zip(fig.canvases, ["Utility map", "With budget"], strict=True):
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
    panel.add_utility(model, levels=levels.around(eq.utility, n=3), label="IC")
fig[1].add_budget(2.0, 3.0, 30.0, fill=True, label="BC").add_equilibrium(eq).show_legend()

fig.save(str(OUTPUT_DIR / "custom_font.png"))
