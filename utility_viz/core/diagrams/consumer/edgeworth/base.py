"""Shared state, setup and numeric helpers behind :class:`EdgeworthBox`."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

import numpy as np

from utility_viz.core.errors.exceptions import InvalidParameterError
from utility_viz.core.styles.axis import Axis
from utility_viz.core.styles.label import Label, split_label
from utility_viz.core.styles.stroke import Stroke
from utility_viz.core.themes.theme import Theme
from utility_viz.models.consumer.edgeworth_compute import (
    contract_curve_mrs,
    contract_curve_pareto,
    focus_levels,
    line_box_intersections,
    mrs,
    unique_points,
)
from utility_viz.models.consumer.edgeworth_state import EdgeworthState
from utility_viz.models.curves import around_anchor_levels

if TYPE_CHECKING:
    from utility_viz.core.diagrams.consumer.edgeworth.box import EdgeworthBox

_EPS = 1e-3


class BoxBase:
    """Attributes, state accessors and private helpers shared by the Edgeworth mixins."""

    utility_a: Callable[..., Any]
    utility_b: Callable[..., Any]
    total_x: float
    total_y: float
    x_label: str
    y_label: str
    title: str | None
    dpi: int
    legacy_theme: Theme
    add: Callable[..., Any]
    extend: Callable[..., Any]
    _next_id: Callable[[str], str]
    box_stroke: Stroke
    x_side_stroke: Stroke
    y_side_stroke: Stroke
    x_label_style: Label
    y_label_style: Label
    origin_style: Label
    title_style: Label
    utility_a_color: str
    utility_b_color: str
    _state: EdgeworthState

    def _as_box(self) -> EdgeworthBox:
        """Return ``self`` typed as the concrete diagram (for fluent returns from mixins)."""
        return cast("EdgeworthBox", self)

    # --- construction helpers -----------------------------------------------------------------

    def _setup_labels(
        self,
        theme: Theme,
        x_axis: Axis,
        y_axis: Axis,
        x_label: str,
        y_label: str,
        origin_label: Label | None,
        title: str | Label | None,
    ) -> None:
        """Resolve axis names, origin and title text plus their styles."""
        for name, axis in (("x_axis", x_axis), ("y_axis", y_axis)):
            if axis.label_position is not None:
                raise InvalidParameterError(f"EdgeworthBox {name} does not support label_position")
        x_text, self.x_label_style = split_label(x_axis.label, theme.box_label)
        y_text, self.y_label_style = split_label(y_axis.label, theme.box_label)
        self.x_label = x_text if x_text is not None else x_label
        self.y_label = y_text if y_text is not None else y_label
        _, self.origin_style = split_label(origin_label, theme.box_label)
        self.title, self.title_style = split_label(title, theme.title_label)

    def _setup_strokes(self, theme: Theme, box_stroke: Stroke | None, x_axis: Axis, y_axis: Axis) -> None:
        """Merge the box frame stroke over the theme and the per-side axis strokes."""
        self.box_stroke = (
            (box_stroke or Stroke()).merged_over(theme.box_stroke).merged_over(Stroke(color=theme.axis_color))
        )
        self.x_side_stroke = (x_axis.stroke or Stroke()).merged_over(self.box_stroke)
        self.y_side_stroke = (y_axis.stroke or Stroke()).merged_over(self.box_stroke)

    # --- state accessors ----------------------------------------------------------------------

    @property
    def endowment(self) -> tuple[float, float] | None:
        return self._state.endowment

    @endowment.setter
    def endowment(self, value: tuple[float, float] | None) -> None:
        self._state.endowment = value

    @property
    def contract_curve_points(self) -> np.ndarray:
        return self._state.contract_curve_points

    @contract_curve_points.setter
    def contract_curve_points(self, value: np.ndarray) -> None:
        self._state.contract_curve_points = value

    @property
    def core_points(self) -> np.ndarray:
        return self._state.core_points

    @core_points.setter
    def core_points(self, value: np.ndarray) -> None:
        self._state.core_points = value

    @property
    def walrasian_equilibrium(self) -> tuple[float, float] | None:
        return self._state.walrasian_equilibrium

    @walrasian_equilibrium.setter
    def walrasian_equilibrium(self, value: tuple[float, float] | None) -> None:
        self._state.walrasian_equilibrium = value

    @property
    def equilibrium_focus_levels_a(self) -> list[float]:
        return self._state.equilibrium_focus_levels_a

    @equilibrium_focus_levels_a.setter
    def equilibrium_focus_levels_a(self, value: list[float]) -> None:
        self._state.equilibrium_focus_levels_a = value

    @property
    def equilibrium_focus_levels_b(self) -> list[float]:
        return self._state.equilibrium_focus_levels_b

    @equilibrium_focus_levels_b.setter
    def equilibrium_focus_levels_b(self, value: list[float]) -> None:
        self._state.equilibrium_focus_levels_b = value

    # --- numeric helpers ----------------------------------------------------------------------

    def _grid(self, *, res: int) -> tuple[np.ndarray, np.ndarray]:
        x = np.linspace(_EPS, self.total_x - _EPS, res)
        y = np.linspace(_EPS, self.total_y - _EPS, res)
        return np.meshgrid(x, y)

    def _eval_ua(self, x: float, y: float) -> float:
        return float(self.utility_a(x, y))

    def _eval_ub(self, x: float, y: float) -> float:
        return float(self.utility_b(self.total_x - x, self.total_y - y))

    def _mrs(self, func, x: float, y: float, h: float = 1e-4) -> float:
        return mrs(func, x, y, x_max=self.total_x, y_max=self.total_y, eps=_EPS, h=h)

    def _unique_points(self, points: list[tuple[float, float]], digits: int = 4) -> np.ndarray:
        return unique_points(points, digits=digits)

    def _levels_around(self, anchor: float, n: int, spread: float) -> list[float]:
        return around_anchor_levels(anchor=float(anchor), n=n, spread=spread)

    def _focus_levels(
        self,
        *,
        anchor: float,
        u_min: float,
        u_max: float,
        n: int,
        spread: float,
        extra: float | None = None,
    ) -> list[float]:
        return focus_levels(
            anchor=anchor,
            u_min=u_min,
            u_max=u_max,
            n=n,
            spread=spread,
            extra=extra,
        )

    def _contract_curve_mrs(self, *, n: int, tolerance: float) -> np.ndarray:
        return contract_curve_mrs(
            utility_a=self.utility_a,
            utility_b=self.utility_b,
            total_x=self.total_x,
            total_y=self.total_y,
            n=n,
            tolerance=tolerance,
            eps=_EPS,
        )

    def _contract_curve_pareto(self, *, n: int) -> np.ndarray:
        return contract_curve_pareto(
            eval_ua=self._eval_ua,
            eval_ub=self._eval_ub,
            total_x=self.total_x,
            total_y=self.total_y,
            n=n,
            eps=_EPS,
        )

    def _line_box_intersections(self, px: float, py: float, income: float) -> list[tuple[float, float]]:
        return line_box_intersections(
            px=px,
            py=py,
            income=income,
            total_x=self.total_x,
            total_y=self.total_y,
        )
