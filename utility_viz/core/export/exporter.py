"""Scene-owned export dispatch without renderer-specific figure objects."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from utility_viz.core.errors.exceptions import ExportError
from utility_viz.enums import ExportFormat


def save_figure(
    drawable: Any,
    *,
    path: str | Path,
    dpi: int | None = None,
    close: bool = False,
    unsupported_as_value_error: bool = False,
    transparent: bool = True,
    **options: Any,
) -> list[Path]:
    """Save a Canvas/Figure through its MosaicKit-backed public API.

    ``dpi`` is applied to canvas specs for this save only. ``close`` remains an
    accepted compatibility argument but is unnecessary because render results
    are created and closed inside MosaicKit's save operation.
    """
    target = Path(path)
    try:
        ExportFormat.from_path(str(target))
    except ExportError as exc:
        if unsupported_as_value_error:
            raise ValueError(str(exc)) from None
        raise
    if not hasattr(drawable, "save"):
        raise ExportError("save_figure expects a utility_viz Canvas or Figure, not a backend figure")

    canvases = getattr(drawable, "canvases", (drawable,))
    previous = []
    if dpi is not None:
        for canvas in canvases:
            previous.append(canvas.spec)
            canvas.spec = canvas.spec.replace(dpi=dpi)
    try:
        return drawable.save(target, transparent=transparent, **options)
    except OSError as exc:
        raise ExportError(f"Failed to write '{target}': {exc}") from exc
    finally:
        if dpi is not None:
            for canvas, spec in zip(canvases, previous, strict=True):
                canvas.spec = spec
        _ = close
