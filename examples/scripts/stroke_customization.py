"""Restyle every line with Stroke: theme defaults on the left, custom strokes on the right."""

from pathlib import Path

from mosaickit import CanvasGrid
from mosaickit import Layout as MosaicLayout

from utility_viz import ArrowStyle, Canvas, Stroke, levels, solve
from utility_viz.models import CobbDouglas

OUTPUT_DIR = Path("examples/output/customization")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

model = CobbDouglas(alpha=0.5, beta=0.5)
eq = solve(model, px=2.0, py=3.0, income=30.0)
lvls = levels.around(eq.utility, n=3)

left = (
    Canvas(x_max=20, y_max=15, title="Theme defaults", dpi=200)
    .add_utility(model, levels=lvls)
    .add_budget(2.0, 3.0, 30.0)
    .add_equilibrium(eq, show_ray=True)
)

right = (
    Canvas(
        x_max=20,
        y_max=15,
        title="Custom strokes",
        dpi=200,
        axis_stroke=Stroke(width=1.4, arrow=ArrowStyle.SIMPLE),
    )
    .add_utility(model, levels=lvls, stroke=Stroke(width=1.0, style="dashed", arrow=ArrowStyle.TRIANGLE))
    .add_budget(2.0, 3.0, 30.0, stroke=Stroke(width=3.0, color="black"))
    .add_equilibrium(
        eq,
        show_ray=True,
        drop_stroke=Stroke(width=1.2, style="dashdot"),
        ray_stroke=Stroke(width=1.2, style="solid", arrow=ArrowStyle.WEDGE),
    )
)

CanvasGrid.from_layout([left, right], MosaicLayout.SIDE_BY_SIDE).save(
    OUTPUT_DIR / "stroke_customization.png", transparent=True
)
