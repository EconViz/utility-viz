"""Backend-neutral level curves: bezierkit traces them, utility-viz chooses the levels."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from typing import Any

import numpy as np
from bezierkit import implicit
from bezierkit.bezier.path import PiecewiseBezier
from bezierkit.implicit import ContourSet, trace_implicit
from bezierkit.sampling.uniform import UniformSampler

# bezierkit >= 1.1 traces a grid that is already sampled; older releases keep the per-point path.
trace_sampled: Callable[..., ContourSet] | None = getattr(implicit, "trace_sampled", None)

Point = tuple[float, float]

# Value substituted where a utility is undefined (e.g. Stone-Geary below subsistence), so
# the marching-squares grid stays finite. It is far below any real level, so a level
# crossing only ever lands next to the finite side of an undefined cell.
_UNDEFINED = -1e12


def trace_level_sets(
    func: Callable[..., Any],
    levels: Sequence[float],
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    *,
    resolution: tuple[int, int] = (161, 161),
    tolerance: float = 0.005,
) -> ContourSet:
    """Trace ``func(x, y) == level`` for each level as cubic Bezier paths.

    Wraps :func:`bezierkit.implicit.trace_implicit`. Level *selection* stays with the
    caller (``percentile_levels`` and friends); this only converts levels to geometry.
    Handles non-monotone and kinked utilities (Leontief kinks are rounded to within
    *tolerance*; a level that is not present inside the box gives an empty path tuple).
    Disconnected components come back as separate paths.
    """

    def field(x: float, y: float) -> float:
        with np.errstate(all="ignore"):
            value = float(func(np.float64(x), np.float64(y)))
        return value if math.isfinite(value) else _UNDEFINED

    grid = _sample_on_grid(func, x_range, y_range, resolution) if trace_sampled else None
    if grid is not None and trace_sampled is not None:
        xs, ys, values = grid
        return trace_sampled(xs, ys, values, levels=list(levels), tolerance=tolerance)
    return trace_implicit(
        field,
        levels=list(levels),
        viewport=(x_range[0], x_range[1], y_range[0], y_range[1]),
        resolution=resolution,
        tolerance=tolerance,
    )


def _sample_on_grid(
    func: Callable[..., Any],
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    resolution: tuple[int, int],
) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    """Evaluate ``func`` on the whole grid in one call, or ``None`` if it cannot be.

    ``None`` means the caller falls back to one call per grid point: the viewport or
    resolution is invalid (that path raises the usual errors), ``func`` does not accept
    arrays, or its array result disagrees with its scalar value at three probe points.
    """
    x0, x1, y0, y1 = (float(v) for v in (*x_range, *y_range))
    nx, ny = resolution
    if not (math.isfinite(x0 + x1 + y0 + y1) and x0 < x1 and y0 < y1 and nx >= 2 and ny >= 2):
        return None
    xs = np.linspace(x0, x1, nx)
    ys = np.linspace(y0, y1, ny)
    grid_x, grid_y = np.meshgrid(xs, ys)
    try:
        with np.errstate(all="ignore"):
            values = np.asarray(func(grid_x, grid_y), dtype=float)
            if values.shape != grid_x.shape:
                return None
            for row, column in ((0, 0), (ny // 2, nx // 2), (ny - 1, nx - 1)):
                scalar = float(func(np.float64(xs[column]), np.float64(ys[row])))
                if not _agree(scalar, float(values[row, column])):
                    return None
    except Exception:  # noqa: BLE001 - any model that cannot take arrays keeps the scalar path
        return None
    return xs, ys, np.where(np.isfinite(values), values, _UNDEFINED)


def _agree(scalar: float, vector: float) -> bool:
    """Equal, both undefined, or equal to far more digits than a contour can show."""
    if math.isfinite(scalar) != math.isfinite(vector):
        return False
    return not math.isfinite(scalar) or math.isclose(scalar, vector, rel_tol=1e-9, abs_tol=1e-12)


def sample_path(path: PiecewiseBezier, points_per_segment: int = 16) -> list[Point]:
    """Sample a Bezier path to an ordered polyline (what a raster backend draws)."""
    count = max(2, points_per_segment * len(path.segments))
    sample = UniformSampler(count).sample(path)
    return [(float(x), float(y)) for x, y in zip(sample.x, sample.y, strict=True)]
