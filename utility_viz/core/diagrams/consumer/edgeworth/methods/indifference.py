"""Indifference-map methods for a scene-backed Edgeworth box."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from utility_viz.core.diagrams.consumer.edgeworth.config import EquilibriumFocusConfig
from utility_viz.core.diagrams.consumer.edgeworth.focus import apply_equilibrium_focus, should_include_endowment_ic
from utility_viz.core.diagrams.consumer.edgeworth.methods.points import PointsMixin
from utility_viz.core.scenes.consumer.edgeworth import edgeworth_indifference_layers
from utility_viz.core.scenes.styles import to_mosaic_stroke
from utility_viz.core.styles.stroke import Stroke
from utility_viz.models.curves import percentile_levels

if TYPE_CHECKING:
    from utility_viz.core.diagrams.consumer.edgeworth.box import EdgeworthBox


class IndifferenceMixin(PointsMixin):
    def _utility_surfaces(self, res: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        x, y = self._grid(res=res)
        return x, y, self.utility_a(x, y), self.utility_b(self.total_x - x, self.total_y - y)

    def add_indifference_curves(
        self,
        *,
        levels_a: int | list[float] = 4,
        levels_b: int | list[float] = 4,
        color_a: str | None = None,
        color_b: str | None = None,
        linewidth: float | None = None,
        res: int = 320,
        stroke_a: Stroke | None = None,
        stroke_b: Stroke | None = None,
    ) -> EdgeworthBox:
        _, _, utility_a, utility_b = self._utility_surfaces(res)
        selected_a = percentile_levels(utility_a, n=levels_a) if isinstance(levels_a, int) else list(levels_a)
        selected_b = percentile_levels(utility_b, n=levels_b) if isinstance(levels_b, int) else list(levels_b)
        style_a = (stroke_a or Stroke()).merged_over(self.legacy_theme.ic_stroke)
        style_b = (stroke_b or Stroke()).merged_over(self.legacy_theme.path_stroke)
        style_a = Stroke(color=color_a or self.utility_a_color, width=linewidth).merged_over(style_a)
        style_b = Stroke(color=color_b or self.utility_b_color, width=linewidth).merged_over(style_b)
        self.extend(
            edgeworth_indifference_layers(
                self.utility_a,
                self.utility_b,
                self.total_x,
                self.total_y,
                levels_a=selected_a,
                levels_b=selected_b,
                stroke_a=to_mosaic_stroke(style_a),
                stroke_b=to_mosaic_stroke(style_b),
                prefix=self._next_id("indifference"),
            )
        )
        return self._as_box()

    def add_endowment_indifference(self, **kwargs) -> EdgeworthBox:
        if self.endowment is None:
            raise ValueError("Endowment is required. Call add_endowment(...) first.")
        x, y = self.endowment
        kwargs.pop("res", None)
        return self.add_indifference_curves(levels_a=[self._eval_ua(x, y)], levels_b=[self._eval_ub(x, y)], **kwargs)

    def _equilibrium_utilities(self, px: float, py: float) -> tuple[float, float]:
        if px <= 0 or py <= 0:
            raise ValueError("px and py must be positive.")
        if self.walrasian_equilibrium is None:
            self.add_walrasian_equilibrium(px=px, py=py)
        assert self.walrasian_equilibrium is not None
        x, y = self.walrasian_equilibrium
        return self._eval_ua(x, y), self._eval_ub(x, y)

    def add_indifference_curves_from_equilibrium(
        self,
        *,
        px: float,
        py: float,
        n_a: int = 4,
        n_b: int = 4,
        spread: float = 0.5,
        color_a: str | None = None,
        color_b: str | None = None,
        linewidth: float | None = None,
        res: int = 320,
        stroke_a: Stroke | None = None,
        stroke_b: Stroke | None = None,
        contract_stroke: Stroke | None = None,
    ) -> EdgeworthBox:
        utility_a, utility_b = self._equilibrium_utilities(px, py)
        _ = contract_stroke
        return self.add_indifference_curves(
            levels_a=self._levels_around(anchor=utility_a, n=n_a, spread=spread),
            levels_b=self._levels_around(anchor=utility_b, n=n_b, spread=spread),
            color_a=color_a,
            color_b=color_b,
            linewidth=linewidth,
            res=res,
            stroke_a=stroke_a,
            stroke_b=stroke_b,
        )

    def add_equilibrium_indifference(
        self,
        *,
        px: float,
        py: float,
        color_a: str | None = None,
        color_b: str | None = None,
        linewidth: float | None = None,
        res: int = 300,
        stroke_a: Stroke | None = None,
        stroke_b: Stroke | None = None,
        contract_stroke: Stroke | None = None,
    ) -> EdgeworthBox:
        utility_a, utility_b = self._equilibrium_utilities(px, py)
        _ = contract_stroke
        return self.add_indifference_curves(
            levels_a=[utility_a],
            levels_b=[utility_b],
            color_a=color_a,
            color_b=color_b,
            linewidth=linewidth,
            res=res,
            stroke_a=stroke_a,
            stroke_b=stroke_b,
        )

    def apply_equilibrium_focus(
        self, *, px: float, py: float, config: EquilibriumFocusConfig | None = None
    ) -> EdgeworthBox:
        apply_equilibrium_focus(self._as_box(), px, py, config or EquilibriumFocusConfig())
        return self._as_box()

    def _should_include_endowment_ic(self, *, min_relative_gap: float) -> bool:
        return should_include_endowment_ic(self._as_box(), min_relative_gap=min_relative_gap)
