"""Edgeworth box diagram composed as a backend-neutral MosaicKit scene."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mosaickit import Canvas as MosaicCanvas
from mosaickit import CanvasSpec, LegendLayer, LegendStyle, TextLayer

from utility_viz.core.config.settings import Config
from utility_viz.core.constants.canvas import DEFAULT_DPI, MAX_DPI, MIN_DPI
from utility_viz.core.diagrams.consumer.edgeworth.methods import IndifferenceMixin
from utility_viz.core.scenes.consumer.edgeworth import edgeworth_frame_layers
from utility_viz.core.scenes.styles import to_mosaic_stroke, to_mosaic_text, to_mosaic_theme
from utility_viz.core.scenes.tikz import canvas_to_tikz
from utility_viz.core.styles.axis import Axis
from utility_viz.core.styles.label import Label
from utility_viz.core.styles.legend import Legend
from utility_viz.core.styles.stroke import Stroke
from utility_viz.core.themes.theme import Theme
from utility_viz.models.consumer.edgeworth_state import EdgeworthState


class EdgeworthBox(IndifferenceMixin, MosaicCanvas):
    """A two-consumer exchange box whose public state contains no renderer objects."""

    def __init__(
        self,
        utility_a,
        utility_b,
        total_x: float,
        total_y: float,
        *,
        x_label: str = "x",
        y_label: str = "y",
        title: str | Label | None = None,
        dpi: int = DEFAULT_DPI,
        theme: Theme | None = None,
        utility_a_color: str | None = None,
        utility_b_color: str | None = None,
        box_stroke: Stroke | None = None,
        x_axis: Axis | None = None,
        y_axis: Axis | None = None,
        origin_label: Label | None = None,
    ) -> None:
        if total_x <= 0 or total_y <= 0:
            raise ValueError("total_x and total_y must be positive.")
        selected_theme = theme if theme is not None else Config.active().theme
        x_axis, y_axis = x_axis or Axis(), y_axis or Axis()
        self._setup_labels(selected_theme, x_axis, y_axis, x_label, y_label, origin_label, title)
        self.utility_a = utility_a
        self.utility_b = utility_b
        self.total_x = float(total_x)
        self.total_y = float(total_y)
        self.dpi = max(MIN_DPI, min(int(dpi), MAX_DPI))
        self.legacy_theme = selected_theme
        self._setup_strokes(selected_theme, box_stroke, x_axis, y_axis)
        self.utility_a_color = utility_a_color or selected_theme.ic_color
        self.utility_b_color = utility_b_color or selected_theme.path_color
        self._state = EdgeworthState()
        self._layer_counts: dict[str, int] = {}
        MosaicCanvas.__init__(
            self,
            spec=CanvasSpec(
                x_range=(0.0, self.total_x),
                y_range=(0.0, self.total_y),
                width=7.0,
                height=6.0,
                dpi=self.dpi,
                title=None,
            ),
            theme=to_mosaic_theme(selected_theme),
        )
        self.extend(
            edgeworth_frame_layers(
                self.total_x,
                self.total_y,
                x_label=self.x_label,
                y_label=self.y_label,
                x_stroke=to_mosaic_stroke(self.x_side_stroke),
                y_stroke=to_mosaic_stroke(self.y_side_stroke),
                label_style=to_mosaic_text(self.x_label_style),
                origin_style=to_mosaic_text(self.origin_style),
            )
        )
        if self.title and self.title_style.visible is not False:
            self.add(
                TextLayer(
                    (self.total_x / 2, self.total_y),
                    self.title,
                    style=to_mosaic_text(self.title_style),
                    offset=(0, 12),
                    anchor="bottom",
                    id="box.title",
                    role="title",
                    z_index=10,
                )
            )

    def _next_id(self, prefix: str) -> str:
        count = self._layer_counts.get(prefix, 0) + 1
        self._layer_counts[prefix] = count
        return prefix if count == 1 else f"{prefix}.{count}"

    def set_utility_colors(self, *, color_a: str, color_b: str) -> EdgeworthBox:
        self.utility_a_color = color_a
        self.utility_b_color = color_b
        return self

    def show_legend(self, legend: Legend | None = None, **kwargs) -> EdgeworthBox:
        if kwargs:
            raise TypeError("renderer-specific legend options are unsupported")
        selected = (legend or Legend()).merged_over(self.legacy_theme.legend)
        if selected.visible is not False:
            location = str(getattr(selected.position, "value", selected.position or "best"))
            self.add(
                LegendLayer(
                    id=self._next_id("legend"),
                    style=LegendStyle(
                        visible=selected.visible,
                        location="best" if location == "auto" else location,
                        frame=selected.frame,
                        size=selected.fontsize,
                    ),
                )
            )
        return self

    def save(self, target: str | Path, **options: Any) -> list[Path]:
        path = Path(target)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() == ".tex":
            standalone = bool(options.pop("tikz_standalone", True))
            if options:
                names = ", ".join(sorted(options))
                raise TypeError(f"unsupported TikZ export options: {names}")
            path.write_text(canvas_to_tikz(self, standalone=standalone), encoding="utf-8")
            return [path]
        return super().save(path, **options)

    def show(self) -> None:
        self.render().show()
