"""GIF export from utility-viz Canvas/Figure scene factories."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, cast

import numpy as np

if TYPE_CHECKING:
    from utility_viz.core.canvas.base import Canvas
    from utility_viz.core.layout.figure import Figure

    AnyFigure = Canvas | Figure


def _require_kinetickit():
    try:
        from kinetickit.exporters import export_png_frames
    except ImportError as exc:
        raise ImportError(
            "KineticKit is required for GIF export.\n"
            "Install it with:  pip install utility-viz[animation]\n"
            "              or:  pip install 'kinetickit[raster]'"
        ) from exc
    return export_png_frames


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
        export_png_frames = _require_kinetickit()
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        export_png_frames(self._render_frames(dpi=dpi), target, fps=fps, loop=loop, disposal=2)

    def _render_frames(self, dpi: int) -> Iterator[bytes]:
        with TemporaryDirectory(prefix="utility-viz-animation-") as directory:
            root = Path(directory)
            for index, value in enumerate(self._frames):
                drawable = self._factory(float(value))
                canvases = cast("Sequence[Canvas]", getattr(drawable, "canvases", (drawable,)))
                previous = [canvas.spec for canvas in canvases]
                target = root / f"frame-{index:06d}.png"
                try:
                    for canvas in canvases:
                        canvas.spec = canvas.spec.replace(dpi=dpi)
                    drawable.save(target, transparent=False)
                    yield target.read_bytes()
                finally:
                    for canvas, spec in zip(canvases, previous, strict=True):
                        canvas.spec = spec
