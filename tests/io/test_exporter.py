"""Compatibility export dispatch remains scene-owned and renderer-neutral."""

from pathlib import Path

import pytest

from utility_viz import Canvas
from utility_viz.core.errors import ExportError
from utility_viz.core.export import save_figure


def test_save_figure_exports_canvas_and_restores_dpi(tmp_path):
    canvas = Canvas(dpi=120).add_budget(2, 3, 30)
    original_spec = canvas.spec
    target = tmp_path / "diagram.png"

    written = save_figure(canvas, path=target, dpi=180, close=True)

    assert written == [target]
    assert target.is_file() and target.stat().st_size > 0
    assert canvas.spec == original_spec


def test_save_figure_validates_extension_before_drawable():
    with pytest.raises(ExportError, match="Unsupported file extension"):
        save_figure(object(), path="diagram.bmp")
    with pytest.raises(ValueError, match="Unsupported file extension"):
        save_figure(object(), path="diagram.bmp", unsupported_as_value_error=True)


def test_save_figure_rejects_backend_objects():
    with pytest.raises(ExportError, match="Canvas or Figure"):
        save_figure(object(), path="diagram.png")


def test_save_figure_translates_write_errors(tmp_path):
    class BrokenDrawable:
        def save(self, _target: Path, **_options):
            raise OSError("disk full")

    target = tmp_path / "diagram.svg"
    with pytest.raises(ExportError, match=r"Failed to write .*disk full"):
        save_figure(BrokenDrawable(), path=target)
