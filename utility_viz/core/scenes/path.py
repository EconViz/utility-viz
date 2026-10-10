"""BezierKit geometry for sampled economic paths."""

from __future__ import annotations

from collections.abc import Sequence

from bezierkit import CubicBezierSegment, PiecewiseBezier, Point

from utility_viz.models.curves import sample_path


def smooth_path(points: Sequence[tuple[float, float]]) -> tuple[list[tuple[float, float]], PiecewiseBezier | None]:
    """Interpolate points with a Catmull-Rom-style cubic Bezier path."""
    if len(points) < 2:
        return list(points), None
    values = [Point(float(x), float(y)) for x, y in points]
    segments: list[CubicBezierSegment] = []
    for index, (start, end) in enumerate(zip(values, values[1:], strict=False)):
        previous = values[index - 1] if index else start
        following = values[index + 2] if index + 2 < len(values) else end
        c1 = Point(
            start.coords[0] + (end.coords[0] - previous.coords[0]) / 6,
            start.coords[1] + (end.coords[1] - previous.coords[1]) / 6,
        )
        c2 = Point(
            end.coords[0] - (following.coords[0] - start.coords[0]) / 6,
            end.coords[1] - (following.coords[1] - start.coords[1]) / 6,
        )
        segments.append(CubicBezierSegment(start, c1, c2, end))
    model = PiecewiseBezier(segments)
    return sample_path(model), model


__all__ = ["smooth_path"]
