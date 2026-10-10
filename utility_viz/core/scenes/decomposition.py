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
    substitution_stroke: Stroke | None = None,
    income_stroke: Stroke | None = None,
    effect_text: TextStyle | None = None,
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
                offset=(6, 6),
                anchor="bottom-left",
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
        range_ys = (-0.10 * y_max, -0.17 * y_max)
        for name, point in zip(("A", "B", "C"), points, strict=True):
            layers.append(
                PathLayer(
                    (point, (point[0], min(range_ys))),
                    stroke=None,
                    id=f"decomposition.projection.{name}",
                    role="utility.decomposition.projection",
                    clip=False,
                    z_index=3,
                )
            )
        for (name, start, end, delta, stroke), y in zip(effects, range_ys, strict=True):
            if abs(end[0] - start[0]) <= 1e-3:
                continue
            layers.append(
                PathLayer(
                    ((start[0], y), (end[0], y)),
                    stroke=stroke,
                    arrow_placement=ArrowPlacement.END,
                    clip=False,
                    id=f"decomposition.range.{name}",
                    role=f"utility.decomposition.effect.{name}",
                    legend=_effect_legend(name, delta) if label_effects else None,
                    z_index=8,
                )
            )
            if label_effects:
                layers.append(
                    TextLayer(
                        ((start[0] + end[0]) / 2, y),
                        f"{delta[0]:+.2f}",
                        style=effect_text,
                        offset=(0, -5),
                        anchor="top",
                        id=f"decomposition.range.{name}.label",
                        role=f"utility.decomposition.effect.{name}.label",
                        z_index=9,
                    )
                )
        return tuple(layers)

    for name, start, end, delta, stroke in effects:
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
    return tuple(layers)


def _effect_legend(name: str, delta: tuple[float, float]) -> str:
    title = "Sub" if name == "substitution" else "Inc"
    return rf"{title}: \Delta x={delta[0]:+.2f}, \Delta y={delta[1]:+.2f}"
