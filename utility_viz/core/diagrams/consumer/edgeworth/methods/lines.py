"""Contract curve, core and price-line scene methods."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from mosaickit import MarkerLayer

from utility_viz.core.diagrams.consumer.edgeworth.base import BoxBase
from utility_viz.core.diagrams.consumer.edgeworth.exchange import core_allocations
from utility_viz.core.scenes.consumer.edgeworth import edgeworth_path_layer
from utility_viz.core.scenes.styles import to_mosaic_marker, to_mosaic_stroke
from utility_viz.core.styles.marker import Marker
from utility_viz.core.styles.stroke import Stroke
from utility_viz.enums import LineStyle

if TYPE_CHECKING:
    from utility_viz.core.diagrams.consumer.edgeworth.box import EdgeworthBox


class LinesMixin(BoxBase):
    """Contract curve, core and price line operations."""

    def add_contract_curve(
        self,
        *,
        n: int = 120,
        color: str | None = None,
        linewidth: float | None = None,
        linestyle: str | None = None,
        tolerance: float = 0.05,
        method: str = "auto",
        stroke: Stroke | None = None,
    ) -> EdgeworthBox:
        if method not in {"auto", "mrs", "pareto"}:
            raise ValueError("method must be one of: auto, mrs, pareto.")
        points = np.empty((0, 2), dtype=float)
        if method in {"auto", "mrs"}:
            points = self._contract_curve_mrs(n=n, tolerance=tolerance)
        if len(points) < 4 and method in {"auto", "pareto"}:
            points = self._contract_curve_pareto(n=n)
        self.contract_curve_points = points
        selected = (stroke or Stroke()).merged_over(self.legacy_theme.contract_stroke)
        selected = Stroke(
            color=color,
            width=linewidth,
            style=LineStyle(linestyle) if linestyle else None,
        ).merged_over(selected)
        self.add(
            edgeworth_path_layer(
                [tuple(point) for point in points],
                layer_id=self._next_id("contract"),
                role="utility.edgeworth.contract",
                stroke=to_mosaic_stroke(selected),
                legend="Contract curve",
            )
        )
        return self._as_box()

    def add_core(
        self,
        *,
        color: str | None = None,
        linewidth: float | None = None,
        min_points: int = 2,
        tol: float = 1e-6,
        stroke: Stroke | None = None,
        marker: Marker | None = None,
    ) -> EdgeworthBox:
        self.core_points = self._unique_points(core_allocations(self._as_box(), tol))
        selected = (stroke or Stroke()).merged_over(self.legacy_theme.core_stroke)
        selected = Stroke(color=color, width=linewidth).merged_over(selected)
        if len(self.core_points) >= min_points:
            self.add(
                edgeworth_path_layer(
                    [tuple(point) for point in self.core_points],
                    layer_id=self._next_id("core"),
                    role="utility.edgeworth.core",
                    stroke=to_mosaic_stroke(selected),
                    legend="Core",
                    z_index=4,
                )
            )
        elif len(self.core_points):
            selected_marker = (marker or Marker()).merged_over(self.legacy_theme.core_marker)
            selected_marker = Marker(color=color).merged_over(selected_marker)
            self.add(
                MarkerLayer(
                    tuple(tuple(point) for point in self.core_points),
                    marker=to_mosaic_marker(selected_marker),
                    id=self._next_id("core"),
                    role="utility.edgeworth.core",
                    legend="Core",
                    z_index=4,
                )
            )
        return self._as_box()

    def add_price_line(
        self,
        px: float,
        py: float,
        *,
        color: str | None = None,
        linewidth: float | None = None,
        linestyle: str | None = None,
        label: str = "Price line",
        stroke: Stroke | None = None,
    ) -> EdgeworthBox:
        if px <= 0 or py <= 0:
            raise ValueError("px and py must be positive.")
        if self.endowment is None:
            raise ValueError("Endowment is required. Call add_endowment(...) first.")
        ex, ey = self.endowment
        selected = (stroke or Stroke()).merged_over(self.legacy_theme.price_stroke)
        selected = Stroke(
            color=color,
            width=linewidth,
            style=LineStyle(linestyle) if linestyle else None,
        ).merged_over(selected)
        self.add(
            edgeworth_path_layer(
                self._line_box_intersections(px, py, px * ex + py * ey),
                layer_id=self._next_id("price"),
                role="utility.edgeworth.price",
                stroke=to_mosaic_stroke(selected),
                legend=label,
            )
        )
        return self._as_box()
