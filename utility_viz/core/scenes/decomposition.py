"""Backend-neutral scene factory for Hicks/Slutsky price decompositions."""

from __future__ import annotations

from collections.abc import Sequence

from mosaickit import ArrowPlacement, Layer, Marker, MarkerLayer, PathLayer, Stroke, TextLayer, TextStyle

from utility_viz.core.scenes.budget import budget_layers


def decomposition_layers(
    decomposition,
    *,
    y_max: float,
    budget_strokes: Sequence[Stroke | None],
    bundle_marker: Marker | None = None,
    bundle_text: TextStyle | None = None,
    bundle_text_offset: tuple[float, float] = (6, 6),
    bundle_text_anchor: str = "bottom-left",
    bundle_text_visible: bool = True,
    substitution_stroke: Stroke | None = None,
    income_stroke: Stroke | None = None,
    projection_stroke: Stroke | None = None,
    guide_stroke: Stroke | None = None,
    range_strokes: tuple[Stroke | None, Stroke | None] = (None, None),
    substitution_label: tuple[str | None, TextStyle | None, tuple[float, float], str, bool] = (
        None,
        None,
        (5, 5),
        "bottom-left",
        True,
    ),
    income_label: tuple[str | None, TextStyle | None, tuple[float, float], str, bool] = (
        None,
        None,
        (5, 5),
        "bottom-left",
        True,
    ),
    range_y: tuple[float | None, float | None] = (None, None),
    show_arrows: bool = True,
    show_x_projections: bool = False,
    label_effects: bool = True,
) -> tuple[Layer, ...]:
    """Build budgets, bundles, and price-effect arrows without a renderer object."""
    layers: list[Layer] = []
    budgets = (
        ("original", decomposition.px_before, decomposition.income),
        ("compensated", decomposition.px_after, decomposition.compensated_income),
        ("final", decomposition.px_after, decomposition.income),
    )
    for (name, px, income), stroke in zip(budgets, budget_strokes, strict=True):
        layers.extend(
            budget_layers(
                px,
                decomposition.py,
                income,
                layer_id=f"decomposition.budget.{name}",
                role=f"utility.decomposition.budget.{name}",
                stroke=stroke,
                z_index=2,
            )
        )

    points = tuple((eq.x, eq.y) for eq in (decomposition.A, decomposition.B, decomposition.C))
    layers.append(
        MarkerLayer(
            points,
            marker=bundle_marker,
            id="decomposition.bundles",
            role="utility.decomposition.bundle",
            z_index=7,
        )
    )
    for name, point in zip(("A", "B", "C"), points, strict=True):
        layers.append(
            TextLayer(
                point,
                name,
                style=bundle_text,
                math=True,
                offset=bundle_text_offset,
                anchor=bundle_text_anchor,
                visible=bundle_text_visible,
                id=f"decomposition.bundle.{name}.label",
                role="utility.decomposition.bundle.label",
                z_index=8,
            )
        )

    if not show_arrows:
        return tuple(layers)

    effects = (
        ("substitution", points[0], points[1], decomposition.substitution_effect, substitution_stroke),
        ("income", points[1], points[2], decomposition.income_effect, income_stroke),
    )
    if show_x_projections:
        layers.extend(
            _projected_effect_layers(
                effects,
                points,
                y_max,
                range_y,
                substitution_label,
                income_label,
                label_effects,
                projection_stroke,
                guide_stroke,
                range_strokes,
            )
        )
    else:
        layers.extend(_direct_effect_layers(effects, substitution_label, income_label, label_effects))
    return tuple(layers)


def _projected_effect_layers(
    effects,
    points,
    y_max,
    range_y,
    substitution_label,
    income_label,
    label_effects,
    projection_stroke,
    guide_stroke,
    range_strokes,
):
    layers: list[Layer] = []
    range_ys = (
        range_y[0] * y_max if range_y[0] is not None else -0.10 * y_max,
        range_y[1] * y_max if range_y[1] is not None else -0.17 * y_max,
    )
    for name, point in zip(("A", "B", "C"), points, strict=True):
        layers.append(
            PathLayer(
                (point, (point[0], 0.0)),
                stroke=projection_stroke,
                id=f"decomposition.projection.{name}",
                role="utility.decomposition.projection",
                z_index=3,
            )
        )
        layers.append(
            PathLayer(
                ((point[0], 0.0), (point[0], min(range_ys))),
                stroke=guide_stroke,
                id=f"decomposition.guide.{name}",
                role="utility.decomposition.guide",
                clip=False,
                z_index=3,
            )
        )
    labels = (substitution_label, income_label)
    for effect, y, label, range_stroke in zip(effects, range_ys, labels, range_strokes, strict=True):
        name, start, end, delta, _ = effect
        if abs(end[0] - start[0]) <= 1e-3:
            continue
        layers.append(
            PathLayer(
                ((start[0], y), (end[0], y)),
                stroke=range_stroke,
                arrow_placement=ArrowPlacement.END,
                clip=False,
                id=f"decomposition.range.{name}",
                role=f"utility.decomposition.effect.{name}",
                legend=_effect_legend(name, delta) if label_effects else None,
                z_index=8,
            )
        )
        layers.extend(_effect_label_layers(name, start, end, label, y=y, prefix="range"))
    return layers


def _direct_effect_layers(effects, substitution_label, income_label, label_effects):
    layers: list[Layer] = []
    for effect, label in zip(effects, (substitution_label, income_label), strict=True):
        name, start, end, delta, stroke = effect
        layers.append(
            PathLayer(
                (start, end),
                stroke=stroke,
                arrow_placement=ArrowPlacement.END,
                id=f"decomposition.effect.{name}",
                role=f"utility.decomposition.effect.{name}",
                legend=_effect_legend(name, delta) if label_effects else None,
                z_index=8,
            )
        )
        layers.extend(_effect_label_layers(name, start, end, label, prefix="effect"))
    return layers


def _effect_label_layers(name, start, end, label, *, prefix, y=None):
    if not label[0]:
        return []
    position = ((start[0] + end[0]) / 2, y if y is not None else (start[1] + end[1]) / 2)
    return [
        TextLayer(
            position,
            label[0],
            style=label[1],
            offset=label[2],
            anchor=label[3],
            visible=label[4],
            id=f"decomposition.{prefix}.{name}.label",
            role=f"utility.decomposition.effect.{name}.label",
            z_index=9,
        )
    ]


def _effect_legend(name: str, delta: tuple[float, float]) -> str:
    title = "Sub" if name == "substitution" else "Inc"
    return rf"{title}: \Delta x={delta[0]:+.2f}, \Delta y={delta[1]:+.2f}"
