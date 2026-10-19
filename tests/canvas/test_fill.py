"""Budget fills are represented by MosaicKit FillLayer values."""

import pytest
from mosaickit import FillLayer

from utility_viz import Canvas, Fill, Stroke, Theme
from utility_viz.core.errors.exceptions import InvalidParameterError


def _fill(canvas):
    return next((layer for layer in canvas.snapshot().layers if isinstance(layer, FillLayer)), None)


def test_fill_value_validation_and_merge():
    assert Fill(alpha=0.5).merged_over(Fill(color="red", alpha=0.1)) == Fill(color="red", alpha=0.5)
    with pytest.raises(InvalidParameterError):
        Fill(alpha=2)


def test_no_fill_by_default_and_fill_true_uses_theme():
    assert _fill(Canvas().add_budget(2, 3, 30)) is None
    canvas = Canvas().add_budget(2, 3, 30, fill=True)
    layer = _fill(canvas)
    assert layer.fill.opacity == pytest.approx(canvas.legacy_theme.budget_fill_alpha)


def test_explicit_fill_color_and_opacity():
    layer = _fill(Canvas().add_budget(2, 3, 30, fill=Fill(color="#00ff00", alpha=0.25)))
    assert layer.fill.color.to_hex() == "#00FF00"
    assert layer.fill.opacity == pytest.approx(0.25)


def test_fill_without_color_follows_theme_and_explicit_stroke_does_not_replace_it():
    canvas = Canvas().add_budget(2, 3, 30, fill=True, stroke=Stroke(color="#654321"))
    layer = _fill(canvas)
    assert layer.fill.color is None
    resolved = canvas.theme.resolve(layer.role, fallback_category="fill").fill
    assert resolved.color.to_hex().lower() == canvas.legacy_theme.budget_color.lower()


def test_fill_alpha_shorthand_and_object_precedence():
    assert _fill(Canvas().add_budget(2, 3, 30, fill=True, fill_alpha=0.4)).fill.opacity == pytest.approx(0.4)
    assert _fill(Canvas().add_budget(2, 3, 30, fill=Fill(alpha=0.6), fill_alpha=0.4)).fill.opacity == pytest.approx(0.6)


def test_theme_budget_fill_is_compiled():
    class Grey(Theme):
        @property
        def budget_fill(self):
            return Fill(color="#cccccc", alpha=0.5)

    layer = _fill(Canvas(theme=Grey(name="grey")).add_budget(2, 3, 30, fill=True))
    assert layer.fill.color.to_hex() == "#CCCCCC"
    assert layer.fill.opacity == pytest.approx(0.5)
