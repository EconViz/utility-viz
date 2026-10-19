"""Kinked indifference curves retain their economic corner in the shared scene."""

import re

import numpy as np
import pytest
from mosaickit import PathLayer

from utility_viz import Canvas
from utility_viz.models.utility import CustomUtility, Leontief


def _curve(canvas: Canvas) -> PathLayer:
    return next(
        layer
        for layer in canvas.snapshot().ordered_layers
        if isinstance(layer, PathLayer) and layer.role == "utility.indifference"
    )


def test_leontief_path_has_exact_kink_and_stays_on_both_arms():
    level = 6.0
    curve = _curve(Canvas().add_utility(Leontief(2, 3), levels=[level]))
    points = np.asarray(curve.path)
    kx, ky = Leontief(2, 3).kink_points([level])[0]
    assert np.min(np.hypot(points[:, 0] - kx, points[:, 1] - ky)) < 0.08
    assert np.all(
        (np.isclose(points[:, 0], kx, atol=0.08) & (points[:, 1] >= ky - 0.08))
        | (np.isclose(points[:, 1], ky, atol=0.08) & (points[:, 0] >= kx - 0.08))
    )
    assert curve.model is not None


@pytest.mark.parametrize(
    "fn",
    [
        lambda x, y: np.maximum(2 * x + y, x + 3 * y),
        lambda x, y: np.minimum(2 * x + y, x + 3 * y),
    ],
    ids=["max", "min"],
)
def test_piecewise_custom_utility_stays_on_level_set(fn):
    curve = _curve(Canvas().add_utility(CustomUtility(fn), levels=[6.0]))
    points = np.asarray(curve.path)
    assert np.allclose(fn(points[:, 0], points[:, 1]), 6.0, atol=0.08)


def test_tikz_uses_bezierkit_curve_with_corner(tmp_path):
    output = tmp_path / "leontief.tex"
    Canvas().add_utility(Leontief(2, 3), levels=[6.0]).save(output)
    source = output.read_text(encoding="utf-8")
    assert "controls" in source
    assert re.search(r"\(3\.0+,2\.0[12]\d+\)", source)
