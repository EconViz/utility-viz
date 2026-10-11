"""Compare axis-label positions, arrowhead styles, and axis line styles."""

from pathlib import Path

from mosaickit import CanvasGrid
from mosaickit import Layout as MosaicLayout

from utility_viz import ArrowStyle, Canvas, LabelPosition, LineStyle

OUTPUT_DIR = Path("examples/output/customization")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

settings = [
    (ArrowStyle.TRIANGLE, LineStyle.SOLID, LabelPosition.RIGHT, LabelPosition.TOP),
    (ArrowStyle.SIMPLE, LineStyle.DASHED, LabelPosition.TOP, LabelPosition.LEFT),
    (ArrowStyle.FANCY, LineStyle.DOTTED, LabelPosition.BOTTOM, LabelPosition.RIGHT),
    (ArrowStyle.WEDGE, LineStyle.DASHDOT, LabelPosition.RIGHT, LabelPosition.RIGHT),
]

canvases = [
    Canvas(
        title=f"{arrow.name.title()} · {line.name.title()}",
        x_label_pos=x_position,
        y_label_pos=y_position,
        x_arrow_style=arrow,
        y_arrow_style=arrow,
        x_line_style=line,
        y_line_style=line,
        dpi=200,
    )
    for arrow, line, x_position, y_position in settings
]

CanvasGrid.from_layout(canvases, MosaicLayout.GRID_2X2).save(OUTPUT_DIR / "axis_customization.png", transparent=True)
