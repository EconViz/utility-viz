"""GIF export from utility-viz Canvas/Figure scene factories."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from utility_viz.core.canvas.base import Canvas
    from utility_viz.core.layout.figure import Figure

    AnyFigure = Canvas | Figure


def _require_pillow() -> None:
    try:
        import PIL  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "Pillow is required for GIF export.\n"
            "Install it with:  pip install utility-viz[animation]\n"
            "              or:  pip install Pillow"
        ) from exc


def _saved_scene_to_pil(drawable, target: Path, dpi: int):
    """Render through the drawable's MosaicKit save path and load an RGB frame."""
    from PIL import Image

    canvases = getattr(drawable, "canvases", (drawable,))
    previous = []
    for canvas in canvases:
        previous.append(canvas.spec)
        canvas.spec = canvas.spec.replace(dpi=dpi)
    try:
        drawable.save(target, transparent=False)
        return Image.open(target).copy().convert("RGB")
    finally:
        for canvas, spec in zip(canvases, previous, strict=True):
            canvas.spec = spec


class Animator:
    """Generate a GIF by rendering each factory result through MosaicKit."""

    def __init__(
        self,
        figure_factory: Callable[[float], AnyFigure],
        frames: Sequence[float] | np.ndarray,
    ) -> None:
        self._factory = figure_factory
        self._frames = np.asarray(frames, dtype=float)
        if self._frames.ndim != 1 or len(self._frames) == 0:
            raise ValueError("`frames` must be a non-empty 1-D array-like.")

    def save(
        self,
        path: str | Path,
        fps: int = 10,
        dpi: int = 150,
        loop: int = 0,
    ) -> None:
        _require_pillow()
        images = self._render_frames(dpi=dpi)
        self._write_gif(images, path=Path(path), fps=fps, loop=loop)

    def _render_frames(self, dpi: int) -> list:
        images = []
        with TemporaryDirectory(prefix="utility-viz-animation-") as directory:
            root = Path(directory)
            for index, value in enumerate(self._frames):
                drawable = self._factory(float(value))
                images.append(_saved_scene_to_pil(drawable, root / f"frame-{index:06d}.png", dpi))
        return images

    @staticmethod
    def _write_gif(images: list, path: Path, fps: int, loop: int) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        duration_ms = int(1000 / max(fps, 1))
        images[0].save(
            str(path),
            save_all=True,
            append_images=images[1:],
            loop=loop,
            duration=duration_ms,
            optimize=False,
            disposal=2,
        )
