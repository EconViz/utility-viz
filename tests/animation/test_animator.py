"""Tests for the utility_viz.core.animation submodule (issue #44).

All rendering uses the non-interactive 'Agg' backend so tests can run
headlessly in CI.
"""

import numpy as np
import pytest

from utility_viz import Canvas
from utility_viz.models.utility import CobbDouglas

# ------------------------------------------------------------------
# Animator initialisation
# ------------------------------------------------------------------


class TestAnimatorInit:
    """Animator constructor validation."""

    def test_valid_frames(self):
        from utility_viz.core.animation import Animator

        def _factory(val):
            return Canvas(x_max=10, y_max=10)

        anim = Animator(_factory, frames=np.linspace(1, 5, 10))
        assert len(anim._frames) == 10

    def test_empty_frames_raises(self):
        from utility_viz.core.animation import Animator

        with pytest.raises(ValueError, match="non-empty 1-D"):
            Animator(lambda v: Canvas(), frames=[])

    def test_2d_frames_raises(self):
        from utility_viz.core.animation import Animator

        with pytest.raises(ValueError, match="non-empty 1-D"):
            Animator(lambda v: Canvas(), frames=np.ones((3, 3)))


# ------------------------------------------------------------------
# GIF export
# ------------------------------------------------------------------


class TestAnimatorSave:
    """Animator.save() produces a valid GIF file."""

    @staticmethod
    def _draw(p1: float) -> Canvas:
        c = Canvas(x_max=10, y_max=10, x_label="X_1", y_label="X_2")
        c.add_budget(px=max(p1, 0.1), py=2.0, income=20.0)
        c.add_utility(CobbDouglas(0.5, 0.5), levels=3)
        return c

    def test_save_creates_gif(self, tmp_path):
        from utility_viz.core.animation import Animator

        out = tmp_path / "test.gif"
        Animator(self._draw, frames=np.linspace(1, 5, 5)).save(str(out), fps=5, dpi=72)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_gif_starts_with_magic_bytes(self, tmp_path):
        from utility_viz.core.animation import Animator

        out = tmp_path / "magic.gif"
        Animator(self._draw, frames=[2.0, 3.0]).save(str(out), fps=5, dpi=72)
        with open(out, "rb") as f:
            header = f.read(6)
        assert header in (b"GIF87a", b"GIF89a")

    def test_save_creates_parent_dirs(self, tmp_path):
        from utility_viz.core.animation import Animator

        out = tmp_path / "subdir" / "nested" / "anim.gif"
        Animator(self._draw, frames=[1.0, 2.0]).save(str(out), fps=5, dpi=72)
        assert out.exists()

    def test_gif_uses_restore_to_background_disposal(self, tmp_path):
        from PIL import Image

        from utility_viz.core.animation import Animator

        out = tmp_path / "disposal.gif"
        Animator(self._draw, frames=[1.0, 2.0, 3.0]).save(str(out), fps=5, dpi=72)

        img = Image.open(out)
        disposal_methods = []
        try:
            while True:
                disposal_methods.append(getattr(img, "disposal_method", None))
                img.seek(img.tell() + 1)
        except EOFError:
            pass

        assert disposal_methods
        assert all(method == 2 for method in disposal_methods)


# ------------------------------------------------------------------
# KineticKit guard
# ------------------------------------------------------------------


class TestRequireKineticKit:
    """_require_kinetickit() raises a helpful ImportError."""

    def test_import_error_message(self, monkeypatch):
        import builtins

        real_import = builtins.__import__

        def _mock_import(name, *args, **kwargs):
            if name.startswith("kinetickit"):
                raise ImportError("no kinetickit")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", _mock_import)

        from utility_viz.core.animation.animator import _require_kinetickit

        with pytest.raises(ImportError, match="KineticKit is required"):
            _require_kinetickit()
