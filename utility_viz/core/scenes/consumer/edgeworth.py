"""Edgeworth-box primitives represented as MosaicKit layers."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from mosaickit import Layer, Marker, MarkerLayer, PathLayer, Stroke, TextLayer, TextStyle

from utility_viz.core.scenes.indifference import indifference_layers


def edgeworth_frame_layers(
    total_x: float,
    total_y: float,
    *,
    x_label: str,
    y_label: str,
    x_stroke: Stroke | None,
    y_stroke: Stroke | None,
    label_style: TextStyle | None,
    origin_style: TextStyle | None,
) -> tuple[Layer, ...]:
    """Four box sides plus the two opposed origins and goods labels."""
    return (
        PathLayer(((0, 0), (total_x, 0)), stroke=x_stroke, id="box.bottom", role="utility.edgeworth.frame"),
        PathLayer(((0, total_y), (total_x, total_y)), stroke=x_stroke, id="box.top", role="utility.edgeworth.frame"),
        PathLayer(((0, 0), (0, total_y)), stroke=y_stroke, id="box.left", role="utility.edgeworth.frame"),
        PathLayer(((total_x, 0), (total_x, total_y)), stroke=y_stroke, id="box.right", role="utility.edgeworth.frame"),
        TextLayer(
            (total_x / 2, 0), rf"{x_label}_A", style=label_style, math=True, offset=(0, -8), anchor="top", id="box.x_a"
        ),
        TextLayer(
            (total_x / 2, total_y),
            rf"{x_label}_B",
            style=label_style,
            math=True,
            offset=(0, 8),
            anchor="bottom",
            id="box.x_b",
        ),
        TextLayer(
            (0, total_y / 2),
            rf"{y_label}_A",
            style=label_style,
            math=True,
            offset=(-8, 0),
            anchor="right",
            id="box.y_a",
        ),
        TextLayer(
            (total_x, total_y / 2),
            rf"{y_label}_B",
            style=label_style,
            math=True,
            offset=(8, 0),
            anchor="left",
            id="box.y_b",
        ),
        TextLayer((0, 0), "O_A", style=origin_style, math=True, offset=(-5, -5), anchor="top-right", id="box.origin_a"),
        TextLayer(
            (total_x, total_y),
            "O_B",
            style=origin_style,
            math=True,
            offset=(5, 5),
            anchor="bottom-left",
            id="box.origin_b",
        ),
    )


def edgeworth_indifference_layers(
    utility_a: Callable,
    utility_b: Callable,
    total_x: float,
    total_y: float,
    *,
    levels_a: Sequence[float],
    levels_b: Sequence[float],
    stroke_a: Stroke | None,
    stroke_b: Stroke | None,
    prefix: str,
) -> tuple[Layer, ...]:
    """Both consumers' curves in A-origin coordinates."""
    a_layers, _ = indifference_layers(
        utility_a, levels_a, total_x, total_y, layer_id=f"{prefix}.a", stroke=stroke_a, z_index=2
    )

    def utility_b_from_a(x, y):
        return utility_b(total_x - x, total_y - y)

    b_layers, _ = indifference_layers(
        utility_b_from_a, levels_b, total_x, total_y, layer_id=f"{prefix}.b", stroke=stroke_b, z_index=2
    )
    return (*a_layers, *b_layers)


def edgeworth_point_layers(
    point: tuple[float, float],
    *,
    layer_id: str,
    label: str,
    marker: Marker | None,
    text: TextStyle | None,
) -> tuple[Layer, ...]:
    return (
        MarkerLayer((point,), marker=marker, id=layer_id, role=f"utility.edgeworth.{layer_id}", z_index=6),
        TextLayer(
            point,
            label,
            style=text,
            math=True,
            offset=(6, 6),
            anchor="bottom-left",
            id=f"{layer_id}.label",
            role=f"utility.edgeworth.{layer_id}.label",
            z_index=7,
        ),
    )


def edgeworth_path_layer(
    points: Sequence[tuple[float, float]],
    *,
    layer_id: str,
    role: str,
    stroke: Stroke | None,
    legend: str | None = None,
    z_index: float = 3,
) -> PathLayer:
    return PathLayer(tuple(points), stroke=stroke, id=layer_id, role=role, legend=legend, z_index=z_index)


__all__ = [
    "edgeworth_frame_layers",
    "edgeworth_indifference_layers",
    "edgeworth_path_layer",
    "edgeworth_point_layers",
]
