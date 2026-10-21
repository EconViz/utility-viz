"""Public utility canvas backed by a backend-neutral MosaicKit scene."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from mosaickit import ArrowPlacement, CanvasSpec, MathFont, PathLayer, TextFonts, TextLayer
from mosaickit import Canvas as MosaicCanvas
from mosaickit import Config as MosaicConfig

from utility_viz.core.canvas._labels import _axis_stroke, _label_position
from utility_viz.core.canvas.layers import LayerMixin
from utility_viz.core.config.fonts import resolve_font, resolve_fonts, resolve_math_font
from utility_viz.core.config.settings import Config
from utility_viz.core.constants.canvas import DEFAULT_DPI, MAX_DPI, MIN_DPI
from utility_viz.core.errors.exceptions import InvalidParameterError
from utility_viz.core.scenes.styles import to_mosaic_stroke, to_mosaic_text, to_mosaic_theme
from utility_viz.core.styles.axis import Axis
from utility_viz.core.styles.label import Label, split_label
from utility_viz.core.styles.stroke import Stroke
from utility_viz.core.themes.theme import Theme
from utility_viz.enums import ArrowStyle, LabelPosition, LineStyle

_LABEL_LAYOUT = {
    LabelPosition.TOP: ((0.0, 8.0), "bottom"),
    LabelPosition.RIGHT: ((8.0, 0.0), "left"),
    LabelPosition.BOTTOM: ((0.0, -8.0), "top"),
    LabelPosition.LEFT: ((-8.0, 0.0), "right"),
}


class Canvas(LayerMixin, MosaicCanvas):
    """First-quadrant economic diagram composed from MosaicKit layers."""

    def __init__(
        self,
        x_max: float = 10.0,
        y_max: float = 10.0,
        x_label: str = "X",
        y_label: str = "Y",
        title: str | Label | None = None,
        dpi: int = DEFAULT_DPI,
        x_label_pos: LabelPosition | str = LabelPosition.RIGHT,
        y_label_pos: LabelPosition | str = LabelPosition.TOP,
        theme: Theme | None = None,
        fig: Any = None,
        ax: Any = None,
        x_arrow_style: ArrowStyle | str | None = None,
        y_arrow_style: ArrowStyle | str | None = None,
        font: str | None = None,
        fonts: TextFonts | None = None,
        math_font: MathFont | str | os.PathLike[str] | None = None,
        x_line_style: LineStyle | str | None = None,
        y_line_style: LineStyle | str | None = None,
        axis_stroke: Stroke | None = None,
        x_axis_stroke: Stroke | None = None,
        y_axis_stroke: Stroke | None = None,
        x_axis: Axis | None = None,
        y_axis: Axis | None = None,
        origin_label: str | Label | None = None,
    ) -> None:
        if fig is not None or ax is not None:
            raise InvalidParameterError(
                "fig/ax injection is unavailable with the MosaicKit canvas; "
                "compose canvases with utility_viz.Figure instead"
            )
        if x_max <= 0 or y_max <= 0:
            raise InvalidParameterError("Canvas x_max and y_max must be positive")

        active = Config.active()
        legacy_theme = theme if theme is not None else active.theme
        selected_font = resolve_font(font if font is not None else active.font)
        self.fonts = resolve_fonts(fonts if fonts is not None else active.fonts)
        self.math_font = resolve_math_font(math_font if math_font is not None else active.math_font)
        self.legacy_theme = legacy_theme
        self.font = selected_font

        x_axis, y_axis = x_axis or Axis(), y_axis or Axis()
        x_text, self.x_label_style = split_label(x_axis.label, legacy_theme.axis_label)
        y_text, self.y_label_style = split_label(y_axis.label, legacy_theme.axis_label)
        self.title, self.title_style = split_label(title, legacy_theme.title_label)
        origin_text, self.origin_style = split_label(
            origin_label, legacy_theme.origin_label, legacy_theme.origin_label.text
        )
        self.origin_text = origin_text or legacy_theme.origin_label.text or "0"
        self.x_max = float(x_max)
        self.y_max = float(y_max)
        self.x_label = x_text if x_text is not None else x_label
        self.y_label = y_text if y_text is not None else y_label
        self.dpi = max(MIN_DPI, min(int(dpi), MAX_DPI))
        self.x_label_pos = _label_position(
            x_axis.label_position or self.x_label_style.position or x_label_pos, axis="x"
        )
        self.y_label_pos = _label_position(
            y_axis.label_position or self.y_label_style.position or y_label_pos, axis="y"
        )
        self.x_axis_stroke = _axis_stroke(
            legacy_theme, x_line_style, x_arrow_style, axis_stroke, x_axis_stroke, x_axis.stroke
        )
        self.y_axis_stroke = _axis_stroke(
            legacy_theme, y_line_style, y_arrow_style, axis_stroke, y_axis_stroke, y_axis.stroke
        )
        self.x_line_style = self.x_axis_stroke.style
        self.y_line_style = self.y_axis_stroke.style
        self.x_arrow_style = self.x_axis_stroke.arrow
        self.y_arrow_style = self.y_axis_stroke.arrow
        self._layer_counts: dict[str, int] = {}

        spec = CanvasSpec(
            x_range=(0.0, self.x_max),
            y_range=(0.0, self.y_max),
            dpi=self.dpi,
            x_label="",
            y_label="",
            title=None,
        )
        super().__init__(
            spec=spec,
            theme=to_mosaic_theme(legacy_theme, font=selected_font),
            config=MosaicConfig(fonts=self.fonts, math_font=self.math_font),
        )
        self.extend(self._axis_layers())

    def _next_id(self, prefix: str) -> str:
        count = self._layer_counts.get(prefix, 0) + 1
        self._layer_counts[prefix] = count
        return prefix if count == 1 else f"{prefix}.{count}"

    def _axis_layers(self) -> tuple:
        x_offset, x_anchor = _LABEL_LAYOUT[self.x_label_pos]
        y_offset, y_anchor = _LABEL_LAYOUT[self.y_label_pos]
        if self.x_label_style.offset is not None:
            x_offset = (
                x_offset[0] / 8 * self.x_label_style.offset,
                x_offset[1] / 8 * self.x_label_style.offset,
            )
        if self.y_label_style.offset is not None:
            y_offset = (
                y_offset[0] / 8 * self.y_label_style.offset,
                y_offset[1] / 8 * self.y_label_style.offset,
            )
        layers: list = [
            PathLayer(
                ((0, 0), (self.x_max, 0)),
                id="axes.x",
                role="axes",
                stroke=to_mosaic_stroke(self.x_axis_stroke),
                arrow_placement=ArrowPlacement.END,
                clip=False,
            ),
            PathLayer(
                ((0, 0), (0, self.y_max)),
                id="axes.y",
                role="axes",
                stroke=to_mosaic_stroke(self.y_axis_stroke),
                arrow_placement=ArrowPlacement.END,
                clip=False,
            ),
        ]
        if self.x_label_style.visible is not False:
            layers.append(
                TextLayer(
                    (self.x_max, 0),
                    self.x_label,
                    id="axes.x.label",
                    role="axes",
                    style=to_mosaic_text(self.x_label_style, font=self.font),
                    offset=x_offset,
                    anchor=x_anchor,
                    math=True,
                )
            )
        if self.y_label_style.visible is not False:
            layers.append(
                TextLayer(
                    (0, self.y_max),
                    self.y_label,
                    id="axes.y.label",
                    role="axes",
                    style=to_mosaic_text(self.y_label_style, font=self.font),
                    offset=y_offset,
                    anchor=y_anchor,
                    math=True,
                )
            )
        if self.origin_style.visible is not False:
            layers.append(
                TextLayer(
                    (0, 0),
                    self.origin_text,
                    id="axes.origin.label",
                    role="axes",
                    style=to_mosaic_text(self.origin_style, font=self.font),
                    offset=(-4, -4),
                    anchor="top-right",
                )
            )
        if self.title and self.title_style.visible is not False:
            layers.append(
                TextLayer(
                    (self.x_max / 2, self.y_max),
                    self.title,
                    id="canvas.title",
                    role="title",
                    style=to_mosaic_text(self.title_style, font=self.font),
                    offset=(0, 12),
                    anchor="bottom",
                    z_index=10,
                )
            )
        return tuple(layers)

    def set_axis_visibility(self, *, show_x_label: bool = True, show_y_label: bool = True) -> Canvas:
        hidden = {
            layer_id
            for layer_id, show in (
                ("axes.x.label", show_x_label),
                ("axes.y.label", show_y_label),
            )
            if not show
        }
        for layer_id in hidden:
            if layer_id in {layer.id for layer in self.snapshot().layers}:
                self.remove(layer_id)
        return self

    def show(self) -> None:
        self.render().show()

    def save(self, target: str | Path, **options: Any) -> list[Path]:
        path = Path(target)
        path.parent.mkdir(parents=True, exist_ok=True)
        return super().save(path, **options)
