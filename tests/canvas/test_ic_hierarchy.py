"""Indifference hierarchy is encoded by semantic roles and layer styles."""

import pytest
from mosaickit import PathLayer, TextLayer

from utility_viz import Canvas, Stroke
from utility_viz.models.utility import CobbDouglas, Leontief, PerfectSubstitutes, Satiation

MODEL = CobbDouglas()


def _paths(canvas, role):
    return [layer for layer in canvas.snapshot().layers if isinstance(layer, PathLayer) and layer.role == role]


def test_without_highlight_all_curves_are_primary():
    canvas = Canvas(x_max=20, y_max=15).add_utility(MODEL, levels=[3, 5, 8])
    assert len(_paths(canvas, "utility.indifference")) == 3
    assert not _paths(canvas, "utility.indifference.secondary")


def test_highlight_selects_nearest_level_and_subdues_the_rest():
    canvas = Canvas(x_max=20, y_max=15).add_utility(MODEL, levels=[3, 5, 8], highlight_level=5.3)
    assert len(_paths(canvas, "utility.indifference")) == 1
    secondary = _paths(canvas, "utility.indifference.secondary")
    assert len(secondary) == 2
    assert all(layer.stroke.opacity < 1 for layer in secondary)


def test_explicit_secondary_stroke_overrides_theme():
    canvas = Canvas(x_max=20, y_max=15).add_utility(
        MODEL,
        levels=[3, 5, 8],
        highlight_level=5,
        secondary_stroke=Stroke(width=2.5, opacity=0.2),
    )
    assert all(
        layer.stroke.width == 2.5 and layer.stroke.opacity == 0.2
        for layer in _paths(canvas, "utility.indifference.secondary")
    )


@pytest.mark.parametrize(
    ("model", "levels", "highlight"),
    [
        (Leontief(), [2, 4, 6], 4),
        (PerfectSubstitutes(), [4, 8, 12], 8),
        (Satiation(bliss_x=8, bliss_y=6), [-20, -8, -2], -8),
    ],
)
def test_utility_families_support_highlight(model, levels, highlight):
    canvas = Canvas(x_max=20, y_max=15).add_utility(model, levels=levels, highlight_level=highlight)
    assert _paths(canvas, "utility.indifference")
    assert _paths(canvas, "utility.indifference.secondary")


def test_numeric_and_ordinal_labels_are_text_layers():
    numeric = Canvas(x_max=20, y_max=15).add_utility(MODEL, levels=[3, 5], show_ic_labels=True)
    ordinal = Canvas(x_max=20, y_max=15).add_utility(MODEL, levels=[3, 5], show_ic_labels=True, label_style="ordinal")
    assert {layer.text for layer in numeric.snapshot().layers if isinstance(layer, TextLayer)} >= {"3", "5"}
    assert {layer.text for layer in ordinal.snapshot().layers if isinstance(layer, TextLayer)} >= {"u_{1}", "u_{2}"}
