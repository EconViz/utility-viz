"""UtilityViz's BezierKit adapter for MosaicKit's scene-level TikZ exporter."""

from bezierkit.bezier.path import PiecewiseBezier
from bezierkit.export.tikz import to_tikz
from mosaickit.rendering.tikz import canvas_to_tikz, register_path_serializer


def _serialize_bezier(path: PiecewiseBezier, options: str) -> str:
    return to_tikz(path, options=options)


register_path_serializer(PiecewiseBezier, _serialize_bezier, replace=True)

__all__ = ["canvas_to_tikz"]
