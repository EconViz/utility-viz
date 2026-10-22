"""trace_level_sets evaluates the grid in one call when it can, and agrees with the scalar path."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest
from bezierkit.implicit import trace_implicit

from utility_viz.models import CES, CobbDouglas, Leontief, PerfectSubstitutes, QuasiLinear, StoneGeary
from utility_viz.models.curves import level_paths
from utility_viz.models.curves.level_paths import trace_level_sets

X_RANGE, Y_RANGE = (0.0, 20.0), (0.0, 15.0)
MODELS: dict[str, Any] = {
    "cobb-douglas": CobbDouglas(alpha=0.3, beta=0.7),
    "ces-0.5": CES(alpha=0.4, rho=0.5),
    "ces-negative": CES(alpha=0.5, rho=-1.0),
    "substitutes": PerfectSubstitutes(a=1.0, b=2.0),
    "leontief": Leontief(a=2.0, b=3.0),
    "quasi-linear": QuasiLinear(),
    "stone-geary": StoneGeary(alpha=0.5, beta=0.5, bar_x=2.0, bar_y=1.0),
}


def scalar_trace(func, levels):
    def field(x: float, y: float) -> float:
        with np.errstate(all="ignore"):
            value = float(func(np.float64(x), np.float64(y)))
        return value if math.isfinite(value) else level_paths._UNDEFINED

    return trace_implicit(
        field,
        levels=list(levels),
        viewport=(*X_RANGE, *Y_RANGE),
        resolution=(161, 161),
        tolerance=0.005,
    )


def coordinates(contours):
    return np.array([c for path in contours.paths for point in path.control_points for p in point for c in p.coords])


@pytest.mark.parametrize("name", MODELS)
def test_grid_evaluation_agrees_with_the_scalar_path(name: str) -> None:
    model = MODELS[name]
    grid = np.meshgrid(*[np.linspace(*r, 9) for r in (X_RANGE, Y_RANGE)])
    with np.errstate(all="ignore"):
        values = np.asarray(model(*grid), dtype=float)
    levels = [float(v) for v in np.quantile(values[np.isfinite(values)], [0.3, 0.5, 0.7])]
    vector = trace_level_sets(model, levels, X_RANGE, Y_RANGE)
    scalar = scalar_trace(model, levels)
    assert len(vector.paths) == len(scalar.paths) > 0
    # the last bit of a power function may differ between array and scalar calls
    assert np.allclose(coordinates(vector), coordinates(scalar), rtol=0, atol=1e-9)


@pytest.mark.skipif(level_paths.trace_sampled is None, reason="needs bezierkit >= 1.1")
def test_models_that_take_arrays_are_evaluated_in_one_call() -> None:
    calls = []

    def utility(x, y):
        calls.append(np.shape(x))
        return x * y

    trace_level_sets(utility, [10.0], X_RANGE, Y_RANGE, resolution=(31, 21))
    assert (21, 31) in calls and len(calls) == 1 + 3  # one grid call, three scalar probes


def test_functions_that_reject_arrays_fall_back_to_per_point_calls() -> None:
    def utility(x, y):
        return math.sqrt(x * y)  # fails on arrays

    contours = trace_level_sets(utility, [3.0], X_RANGE, Y_RANGE, resolution=(41, 41))
    assert len(contours.paths) == 1


def test_functions_whose_array_result_disagrees_with_the_scalar_one_fall_back() -> None:
    def utility(x, y):
        return x * y if np.ndim(x) == 0 else x + y  # inconsistent on purpose

    contours = trace_level_sets(utility, [3.0], X_RANGE, Y_RANGE, resolution=(41, 41))
    reference = scalar_trace_with(utility, [3.0], (41, 41))
    assert contours == reference


def scalar_trace_with(func, levels, resolution):
    def field(x: float, y: float) -> float:
        return float(func(np.float64(x), np.float64(y)))

    return trace_implicit(field, levels=levels, viewport=(*X_RANGE, *Y_RANGE), resolution=resolution, tolerance=0.005)


@pytest.mark.parametrize(
    ("x_range", "resolution"),
    [((5.0, 5.0), (31, 31)), ((0.0, 20.0), (1, 31)), ((0.0, float("inf")), (31, 31))],
)
def test_invalid_input_raises_the_same_errors_as_before(x_range, resolution) -> None:
    with pytest.raises(ValueError):
        trace_level_sets(lambda x, y: x * y, [1.0], x_range, Y_RANGE, resolution=resolution)
