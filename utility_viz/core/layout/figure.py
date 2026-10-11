"""Multi-panel utility diagrams composed with MosaicKit CanvasGrid."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, cast

from mosaickit import Canvas as MosaicCanvas
from mosaickit import CanvasGrid, TextLayer
from mosaickit import Layout as MosaicLayout

from utility_viz.core.canvas.base import Canvas
from utility_viz.core.constants.canvas import DEFAULT_DPI
from utility_viz.core.errors.exceptions import InvalidParameterError
from utility_viz.core.scenes.styles import to_mosaic_text
from utility_viz.core.scenes.tikz import canvas_to_tikz
from utility_viz.core.styles.axis import Axis
from utility_viz.core.styles.label import Label, split_label
from utility_viz.core.styles.stroke import Stroke
from utility_viz.core.themes.theme import Theme
from utility_viz.enums import ArrowStyle, LabelPosition, Layout, LineStyle


@dataclass(frozen=True)
class _PanelSpec:
    row: int
    col: int
    rowspan: int = 1
    colspan: int = 1


_LAYOUT_SPECS: Final[dict[Layout, tuple[tuple[int, int], tuple[_PanelSpec, ...]]]] = {
    Layout.SINGLE: ((1, 1), (_PanelSpec(0, 0),)),
    Layout.STACKED: ((2, 1), (_PanelSpec(0, 0), _PanelSpec(1, 0))),
    Layout.SIDE_BY_SIDE: ((1, 2), (_PanelSpec(0, 0), _PanelSpec(0, 1))),
    Layout.TOP_TWO_BOTTOM_ONE: (
        (2, 2),
        (_PanelSpec(0, 0), _PanelSpec(0, 1), _PanelSpec(1, 0, colspan=2)),
    ),
    Layout.TOP_ONE_BOTTOM_TWO: (
        (2, 2),
        (_PanelSpec(0, 0, colspan=2), _PanelSpec(1, 0), _PanelSpec(1, 1)),
    ),
    Layout.GRID_2X2: (
        (2, 2),
        tuple(_PanelSpec(row, col) for row in range(2) for col in range(2)),
    ),
    Layout.GRID_3X3: (
        (3, 3),
        tuple(_PanelSpec(row, col) for row in range(3) for col in range(3)),
    ),
}


class Figure:
    """A fixed-layout collection of utility canvases rendered as one grid."""

    def __init__(
        self,
        layout: Layout,
        x_max: float = 10.0,
        y_max: float = 10.0,
        x_label: str = "X",
        y_label: str = "Y",
        title: str | Label | None = None,
        dpi: int = DEFAULT_DPI,
        x_label_pos: LabelPosition | str = LabelPosition.RIGHT,
        y_label_pos: LabelPosition | str = LabelPosition.TOP,
        theme: Theme | None = None,
        shared_x: bool = False,
        shared_y: bool = False,
        figsize: tuple[float, float] | None = None,
        hspace: float = 0.3,
        wspace: float = 0.25,
        x_arrow_style: ArrowStyle | str | None = None,
        y_arrow_style: ArrowStyle | str | None = None,
        font: str | Sequence[str] | None = None,
        math_font: str | None = None,
        x_line_style: LineStyle | str | None = None,
        y_line_style: LineStyle | str | None = None,
        axis_stroke: Stroke | None = None,
        x_axis_stroke: Stroke | None = None,
        y_axis_stroke: Stroke | None = None,
        x_axis: Axis | None = None,
        y_axis: Axis | None = None,
    ) -> None:
        if hspace != 0.3 or wspace != 0.25:
            raise InvalidParameterError(
                "custom hspace/wspace are unavailable in MosaicKit CanvasGrid; "
                "use the default spacing or size panels with figsize"
            )
        self.layout = Layout(layout)
        self.shared_x = shared_x
        self.shared_y = shared_y
        self.title, self.title_style = split_label(title, (theme or Theme("default")).title_label)
        self.hspace = hspace
        self.wspace = wspace
        shape, specs = _LAYOUT_SPECS[self.layout]
        rows, cols = shape
        width = (figsize[0] / cols) if figsize else 6.0
        height = (figsize[1] / rows) if figsize else 6.0
        kwargs: Any = dict(
            x_max=x_max,
            y_max=y_max,
            x_label=x_label,
            y_label=y_label,
            dpi=dpi,
            x_label_pos=x_label_pos,
            y_label_pos=y_label_pos,
            theme=theme,
            x_arrow_style=x_arrow_style,
            y_arrow_style=y_arrow_style,
            font=font,
            math_font=math_font,
            x_line_style=x_line_style,
            y_line_style=y_line_style,
            axis_stroke=axis_stroke,
            x_axis_stroke=x_axis_stroke,
            y_axis_stroke=y_axis_stroke,
            x_axis=x_axis,
            y_axis=y_axis,
        )
        self.canvases = [Canvas(**kwargs) for _ in specs]
        for canvas in self.canvases:
            canvas.spec = canvas.spec.replace(width=width, height=height)
        self._specs = specs
        self._grid_lookup = {(spec.row, spec.col): canvas for spec, canvas in zip(specs, self.canvases, strict=True)}
        self._apply_shared_axis_labels(shape)
        self._add_figure_title(shape)

    def _add_figure_title(self, shape: tuple[int, int]) -> None:
        """Represent the figure title in the scene rather than renderer state."""
        if not self.title or self.title_style.visible is False:
            return
        _, cols = shape
        center_column = cols / 2
        spec = next(
            spec for spec in self._specs if spec.row == 0 and spec.col <= center_column <= spec.col + spec.colspan
        )
        canvas = self._grid_lookup[spec.row, spec.col]
        local_midpoint = (center_column - spec.col) / spec.colspan * canvas.x_max
        canvas.add(
            TextLayer(
                (local_midpoint, canvas.y_max),
                self.title,
                id="figure.title",
                role="title",
                style=to_mosaic_text(self.title_style, family=canvas.font),
                offset=(0, 24),
                anchor="bottom",
                z_index=20,
            )
        )

    def _apply_shared_axis_labels(self, shape: tuple[int, int]) -> None:
        rows, _ = shape
        for spec, canvas in zip(self._specs, self.canvases, strict=True):
            canvas.set_axis_visibility(
                show_x_label=not self.shared_x or spec.row + spec.rowspan == rows,
                show_y_label=not self.shared_y or spec.col == 0,
            )

    @property
    def grid(self) -> CanvasGrid:
        return CanvasGrid.from_layout(cast(list[MosaicCanvas], self.canvases), MosaicLayout(self.layout.value))

    def __getitem__(self, idx: int | tuple[int, int]) -> Canvas:
        return self._grid_lookup[idx] if isinstance(idx, tuple) else self.canvases[idx]

    def __len__(self) -> int:
        return len(self.canvases)

    def render(self, **options: Any) -> Any:
        return self.grid.render(**options)

    def save(self, target: str | Path, **options: Any) -> list[Path]:
        path = Path(target)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() == ".tex":
            standalone = bool(options.pop("tikz_standalone", True))
            if options:
                names = ", ".join(sorted(options))
                raise TypeError(f"unsupported TikZ export options: {names}")
            definitions: set[str] = set()
            pictures: list[str] = []
            for canvas in self.canvases:
                source = canvas_to_tikz(canvas, standalone=False)
                picture_at = source.index(r"\begin{tikzpicture}")
                definitions.update(source[:picture_at].splitlines())
                pictures.append(source[picture_at:])
            body = "\n".join(sorted(definitions)) + "\n" + self._tikz_grid(pictures)
            if standalone:
                body = (
                    "\\documentclass[tikz,border=12pt]{standalone}\n"
                    "\\usepackage{xcolor}\n\\usetikzlibrary{arrows.meta}\n"
                    f"\\begin{{document}}\n{body}\\end{{document}}\n"
                )
            path.write_text(body, encoding="utf-8")
            return [path]
        return self.grid.save(path, **options)

    def _tikz_grid(self, pictures: list[str]) -> str:
        rows, cols = _LAYOUT_SPECS[self.layout][0]
        cells: dict[tuple[int, int], tuple[str, _PanelSpec]] = {
            (spec.row, spec.col): (picture, spec) for spec, picture in zip(self._specs, pictures, strict=True)
        }
        lines = [r"\begin{center}"]
        for row in range(rows):
            row_cells: list[str] = []
            col = 0
            while col < cols:
                picture, spec = cells[(row, col)]
                row_cells.append(picture)
                col += spec.colspan
            lines.append(f"% row {row + 1} of {rows}")
            lines.append(r"\hspace{1em}".join(row_cells))
            if row + 1 < rows:
                lines.append(r"\par\medskip")
        lines.append(r"\end{center}")
        return "\n".join(lines)

    def show(self) -> None:
        self.render().show()
