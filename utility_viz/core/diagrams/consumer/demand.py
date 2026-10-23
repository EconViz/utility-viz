"""Linked goods-space and Marshallian-demand scenes."""

from __future__ import annotations

from mosaickit import TextLayer

from utility_viz.core.canvas.base import Canvas
from utility_viz.core.layout.figure import Figure
from utility_viz.core.scenes.consumer.demand import demand_marker_layers, marshallian_demand_layers
from utility_viz.core.scenes.styles import to_mosaic_marker, to_mosaic_nudge, to_mosaic_stroke, to_mosaic_text
from utility_viz.core.styles.axis import Axis
from utility_viz.core.styles.label import Label, split_label
from utility_viz.core.styles.legend import Legend
from utility_viz.core.styles.marker import Marker
from utility_viz.core.styles.placement import placement
from utility_viz.core.styles.stroke import Stroke
from utility_viz.enums import LabelPosition, Layout, LineStyle
from utility_viz.models.consumer.paths import LinearBudget, PricePath, QuantityAxis
from utility_viz.models.optimization import solve
from utility_viz.models.optimization.solver import Equilibrium

_GOODS_SPACE_PADDING = 1.18
_PRICE_SYMBOL = {"px": r"p_{x}", "py": r"p_{y}"}


class DemandDiagram(Figure):
    """Two-panel diagram linking utility maximisation to Marshallian demand."""

    def __init__(
        self,
        path: PricePath,
        x_max: float | None = None,
        y_max: float | None = None,
        demand_x_max: float | None = None,
        demand_y_max: float | None = None,
        x_label: str = "x",
        y_label: str = "y",
        title: str | None = None,
        x_axis: Axis | None = None,
        y_axis: Axis | None = None,
        **kwargs,
    ) -> None:
        if path.parameter_name not in {"px", "py"}:
            raise ValueError("DemandDiagram requires a price sweep path.")
        self.path = path
        self.func = path.func
        top_x_max, top_y_max = self._goods_space_bounds(x_max=x_max, y_max=y_max)
        super().__init__(
            Layout.STACKED,
            x_max=top_x_max,
            y_max=top_y_max,
            x_label=x_label,
            y_label=y_label,
            title=title,
            x_axis=x_axis,
            y_axis=y_axis,
            **kwargs,
        )
        self.utility_canvas = self[0]
        quantity_axis = self._quantity_axis()
        self.demand_canvas = Canvas(
            x_max=demand_x_max or max(path.quantity_values(quantity_axis)) * 1.15 or 1.0,
            y_max=demand_y_max or max(path.parameter_values) * 1.15,
            x_label=quantity_axis,
            y_label=_PRICE_SYMBOL[path.parameter_name],
            dpi=self.utility_canvas.dpi,
            theme=self.utility_canvas.legacy_theme,
            x_axis=Axis(stroke=x_axis.stroke if x_axis else None),
            y_axis=Axis(stroke=y_axis.stroke if y_axis else None),
            font=self.utility_canvas.font,
            fonts=self.utility_canvas.fonts,
            math_font=self.utility_canvas.math_font,
        )
        self.canvases[1] = self.demand_canvas
        self._grid_lookup[(1, 0)] = self.demand_canvas

    def add_marshallian_panel(
        self,
        price_markers: list[float] | None = None,
        show_pcc: bool = False,
        show_demand_guides: bool = True,
        show_legend: bool = True,
        curve_stroke: Stroke | None = None,
        budget_stroke: Stroke | None = None,
        drop_stroke: Stroke | None = None,
        path_stroke: Stroke | None = None,
        demand_stroke: Stroke | None = None,
        guide_stroke: Stroke | None = None,
        point_marker: Marker | None = None,
        point_label: Label | None = None,
        legend: Legend | None = None,
    ) -> DemandDiagram:
        """Populate both panels using only MosaicKit layers."""
        self._clear_content(self.utility_canvas)
        self._clear_content(self.demand_canvas)
        markers = price_markers or [self.path.parameter_values[len(self.path.parameter_values) // 2]]
        solved = [self._solve_at_parameter(price) for price in markers]
        levels = sorted({equilibrium.utility for _, equilibrium in solved})
        self.utility_canvas.add_utility(self.func, levels=levels, label="IC", stroke=curve_stroke)

        demand_points: list[tuple[float, float]] = []
        quantity_axis = self._quantity_axis()
        for index, (price, (budget, equilibrium)) in enumerate(zip(markers, solved, strict=True)):
            label = chr(ord("A") + index)
            selected_budget = (budget_stroke or Stroke()).merged_over(self.utility_canvas.legacy_theme.budget_stroke)
            if index > 0 and (budget_stroke is None or budget_stroke.style is None):
                selected_budget = Stroke(style=LineStyle.DASHED).merged_over(selected_budget)
            self.utility_canvas.add_budget(
                budget.px,
                budget.py,
                budget.income,
                label=rf"{label}: {_PRICE_SYMBOL[self.path.parameter_name]}={price:.2g}",
                stroke=selected_budget,
            )
            self.utility_canvas.add_equilibrium(
                equilibrium,
                label=label if point_label is None else point_label,
                marker=point_marker,
                drop_stroke=drop_stroke,
            )
            quantity = equilibrium.x if quantity_axis == "x" else equilibrium.y
            demand_points.append((quantity, price))

        if show_pcc:
            self.utility_canvas.add_path(self.path, label="PCC", show_points=False, stroke=path_stroke)

        theme = self.demand_canvas.legacy_theme
        selected_demand = (demand_stroke or Stroke()).merged_over(theme.ic_stroke)
        boundary = Stroke(style=LineStyle.DASHED).merged_over(selected_demand)
        selected_marker = (point_marker or Marker()).merged_over(theme.eq_marker)
        self.demand_canvas.extend(
            marshallian_demand_layers(
                self.path,
                quantity_axis,
                stroke=to_mosaic_stroke(selected_demand),
                boundary_stroke=to_mosaic_stroke(boundary),
                marker=to_mosaic_marker(selected_marker),
            )
        )
        selected_guide = (guide_stroke or Stroke()).merged_over(theme.drop_stroke)
        self.demand_canvas.extend(
            demand_marker_layers(
                demand_points,
                marker=to_mosaic_marker(selected_marker),
                guide_stroke=to_mosaic_stroke(selected_guide) if show_demand_guides else None,
            )
            if show_demand_guides
            else demand_marker_layers(demand_points, marker=to_mosaic_marker(selected_marker))[-1:]
        )
        for index, point in enumerate(demand_points):
            _add_demand_label(self.demand_canvas, point, chr(ord("A") + index), point_label, selected_marker)
        if show_legend:
            self.utility_canvas.show_legend(legend)
            self.demand_canvas.show_legend(legend)
        return self

    @staticmethod
    def _clear_content(canvas: Canvas) -> None:
        for layer in tuple(canvas.snapshot().layers):
            if not layer.id.startswith("axes."):
                canvas.remove(layer.id)

    def _quantity_axis(self) -> QuantityAxis:
        return "x" if self.path.parameter_name == "px" else "y"

    def _goods_space_bounds(self, *, x_max: float | None, y_max: float | None) -> tuple[float, float]:
        x_values = [budget.income / budget.px for budget in self.path.budgets]
        y_values = [budget.income / budget.py for budget in self.path.budgets]
        return (
            x_max or max([*x_values, *(eq.x for eq in self.path.equilibria), 1.0]) * _GOODS_SPACE_PADDING,
            y_max or max([*y_values, *(eq.y for eq in self.path.equilibria), 1.0]) * _GOODS_SPACE_PADDING,
        )

    def _solve_at_parameter(self, value: float) -> tuple[LinearBudget, Equilibrium]:
        budget = self.path.base_budget.with_update(**{self.path.parameter_name: value})
        return budget, solve(self.func, px=budget.px, py=budget.py, income=budget.income)


def _add_demand_label(canvas: Canvas, point, fallback_text: str, label: Label | None, marker: Marker) -> None:
    text, style = split_label(
        label if label is not None else fallback_text, canvas.legacy_theme.point_label, fallback_text
    )
    if not text:
        return
    if style.color is None and marker.color is not None:
        style = Label(color=marker.color).merged_over(style)
    position = LabelPosition(style.position or LabelPosition.TOP_RIGHT)
    offset, horizontal, vertical = placement(position, style.offset or 5)
    anchor = "-".join(part for part in (vertical, horizontal) if part != "center") or "center"
    canvas.add(
        TextLayer(
            point,
            text,
            id=f"demand.point.{fallback_text}.label",
            role="utility.demand.point",
            style=to_mosaic_text(style, font=canvas.font),
            offset=offset,
            anchor=anchor,
            math=True,
            visible=style.visible is not False,
            z_index=7,
            nudge=to_mosaic_nudge(style),
        )
    )
