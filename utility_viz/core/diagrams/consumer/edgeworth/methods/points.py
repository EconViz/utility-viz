"""Endowment and Walrasian-equilibrium scene methods."""

from __future__ import annotations

from typing import TYPE_CHECKING

from utility_viz.core.diagrams.consumer.edgeworth.exchange import check_allocation, locate_walrasian
from utility_viz.core.diagrams.consumer.edgeworth.methods.lines import LinesMixin
from utility_viz.core.scenes.consumer.edgeworth import edgeworth_point_layers
from utility_viz.core.scenes.styles import to_mosaic_marker, to_mosaic_text
from utility_viz.core.styles.label import Label, split_label
from utility_viz.core.styles.marker import Marker
from utility_viz.core.styles.placement import placement
from utility_viz.core.styles.stroke import Stroke
from utility_viz.enums import LabelPosition

if TYPE_CHECKING:
    from utility_viz.core.diagrams.consumer.edgeworth.box import EdgeworthBox


class PointsMixin(LinesMixin):
    def add_endowment(
        self,
        x_endowment: float,
        y_endowment: float,
        *,
        label: str | Label = "e",
        color: str | None = None,
        marker: Marker | None = None,
    ) -> EdgeworthBox:
        if not (0.0 <= x_endowment <= self.total_x and 0.0 <= y_endowment <= self.total_y):
            raise ValueError("Endowment must lie inside the Edgeworth box.")
        self.endowment = (float(x_endowment), float(y_endowment))
        text, label_style = split_label(label, self.legacy_theme.edgeworth_label, "e")
        selected = Marker(color=color).merged_over(self.legacy_theme.endowment_marker)
        selected = (marker or Marker()).merged_over(selected)
        label_offset, label_anchor = _label_placement(label_style)
        self.extend(
            edgeworth_point_layers(
                self.endowment,
                layer_id=self._next_id("endowment"),
                label=text or "e",
                marker=to_mosaic_marker(selected),
                text=to_mosaic_text(label_style),
                text_offset=label_offset,
                text_anchor=label_anchor,
                text_visible=label_style.visible is not False,
            )
        )
        return self._as_box()

    def add_walrasian_equilibrium(
        self,
        px: float,
        py: float,
        *,
        color: str | None = None,
        marker: str | Marker | None = None,
        markersize: float | None = None,
        label: str | Label = r"X^*",
        contract_stroke: Stroke | None = None,
    ) -> EdgeworthBox:
        point = locate_walrasian(self._as_box(), px, py)
        self.walrasian_equilibrium = point
        text, label_style = split_label(label, self.legacy_theme.edgeworth_label, r"X^*")
        marker_value = marker if isinstance(marker, Marker) else Marker(shape=marker)
        selected = Marker(color=color, size=markersize).merged_over(self.legacy_theme.walrasian_marker)
        selected = marker_value.merged_over(selected)
        label_offset, label_anchor = _label_placement(label_style)
        self.extend(
            edgeworth_point_layers(
                point,
                layer_id=self._next_id("walrasian"),
                label=text or r"X^*",
                marker=to_mosaic_marker(selected),
                text=to_mosaic_text(label_style),
                text_offset=label_offset,
                text_anchor=label_anchor,
                text_visible=label_style.visible is not False,
            )
        )
        _ = contract_stroke
        return self._as_box()

    def check_point(
        self,
        x: float,
        y: float,
        *,
        px: float | None = None,
        py: float | None = None,
        tol: float = 1e-3,
    ) -> dict[str, bool]:
        return check_allocation(self._as_box(), x, y, px, py, tol)


def _label_placement(style: Label) -> tuple[tuple[float, float], str]:
    offset, horizontal, vertical = placement(
        LabelPosition(style.position or LabelPosition.TOP_RIGHT), style.offset or 5
    )
    anchor = "-".join(part for part in (vertical, horizontal) if part != "center") or "center"
    return offset, anchor
