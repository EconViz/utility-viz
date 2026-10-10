"""Marshallian demand curves as backend-neutral MosaicKit layers."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from mosaickit import Layer, Marker, MarkerLayer, PathLayer, Stroke

from utility_viz.enums import UtilityType


def marshallian_demand_layers(
    path,
    quantity_axis: str,
    *,
    stroke: Stroke | None = None,
    boundary_stroke: Stroke | None = None,
    marker: Marker | None = None,
) -> tuple[Layer, ...]:
    """Build connected demand segments, preserving corner/boundary semantics."""
    quantities = np.asarray(path.quantity_values(quantity_axis), dtype=float)
    prices = np.asarray(path.parameter_values, dtype=float)
    if getattr(path.func, "utility_type", None) is UtilityType.LINEAR:
        return _linear_demand_layers(
            path,
            quantity_axis,
            quantities,
            prices,
            stroke=stroke,
            boundary_stroke=boundary_stroke,
            marker=marker,
        )
    bundle_types = [equilibrium.bundle_type for equilibrium in path.equilibria]
    layers: list[Layer] = []
    start = 0
    segment = 1
    for index in range(1, len(quantities) + 1):
        boundary = index == len(quantities)
        disconnected = not boundary and not (np.isfinite(quantities[index - 1]) and np.isfinite(quantities[index]))
        if not (boundary or disconnected):
            continue
        if index > start:
            is_boundary = bundle_types[start] in {"corner", "boundary"}
            layers.append(
                PathLayer(
                    tuple(zip(quantities[start:index], prices[start:index], strict=True)),
                    stroke=boundary_stroke if is_boundary else stroke,
                    id=f"demand.curve.{segment}",
                    role="utility.demand.boundary" if is_boundary else "utility.demand",
                    legend="Marshallian demand" if segment == 1 else None,
                    z_index=3,
                )
            )
            segment += 1
        start = index
    return tuple(layers)


def _linear_demand_layers(
    path,
    quantity_axis: str,
    quantities: np.ndarray,
    prices: np.ndarray,
    *,
    stroke: Stroke | None,
    boundary_stroke: Stroke | None,
    marker: Marker | None,
) -> tuple[Layer, ...]:
    func = path.func
    if quantity_axis == "x":
        preferred = ["x" if func(b.income / b.px, 0) > func(0, b.income / b.py) else "y" for b in path.budgets]
        chosen = np.asarray([side == "x" for side in preferred])
        tie_price = func.a * path.base_budget.py / func.b
    else:
        preferred = ["y" if func(0, b.income / b.py) > func(b.income / b.px, 0) else "x" for b in path.budgets]
        chosen = np.asarray([side == "y" for side in preferred])
        tie_price = func.b * path.base_budget.px / func.a
    tie_quantity = path.base_budget.income / tie_price
    layers: list[Layer] = []
    if np.any(chosen):
        branch = list(zip(quantities[chosen], prices[chosen], strict=True))
        if prices.min() <= tie_price <= prices.max():
            branch.append((tie_quantity, tie_price))
        branch.sort(key=lambda point: point[1])
        layers.append(
            PathLayer(
                branch,
                stroke=boundary_stroke or stroke,
                id="demand.curve.1",
                role="utility.demand.boundary",
                legend="Marshallian demand",
                z_index=3,
            )
        )
    if prices.min() <= tie_price <= prices.max():
        layers.append(
            PathLayer(
                ((0.0, tie_price), (tie_quantity, tie_price)),
                stroke=stroke,
                id="demand.curve.tie",
                role="utility.demand.tie",
                z_index=4,
            )
        )
        layers.append(
            MarkerLayer(
                ((tie_quantity, tie_price),),
                marker=marker,
                id="demand.tie",
                role="utility.demand.tie",
                z_index=6,
            )
        )
    return tuple(layers)


def demand_marker_layers(
    points: Sequence[tuple[float, float]],
    *,
    marker: Marker | None = None,
    guide_stroke: Stroke | None = None,
) -> tuple[Layer, ...]:
    """Selected demand points and their axis guides."""
    layers: list[Layer] = []
    for index, (quantity, price) in enumerate(points, 1):
        layers.extend(
            (
                PathLayer(
                    ((quantity, 0.0), (quantity, price)),
                    stroke=guide_stroke,
                    id=f"demand.guide.{index}.vertical",
                    role="utility.demand.guide",
                    z_index=1,
                ),
                PathLayer(
                    ((0.0, price), (quantity, price)),
                    stroke=guide_stroke,
                    id=f"demand.guide.{index}.horizontal",
                    role="utility.demand.guide",
                    z_index=1,
                ),
            )
        )
    if points:
        layers.append(
            MarkerLayer(
                tuple(points),
                marker=marker,
                id="demand.points",
                role="utility.demand.point",
                z_index=6,
            )
        )
    return tuple(layers)


__all__ = ["demand_marker_layers", "marshallian_demand_layers"]
