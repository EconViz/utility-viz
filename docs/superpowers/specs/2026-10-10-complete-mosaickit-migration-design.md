# Complete MosaicKit Migration Design

## Intent

Make `utility-viz` an economics-domain package that constructs backend-neutral MosaicKit
scenes and delegates curve geometry to BezierKit.  Matplotlib remains an implementation
detail of MosaicKit's renderer; no `utility_viz` production module may import it.

## Goals

- Keep the documented 2.0 names and ordinary fluent calls (`Canvas(...).add_*().save(...)`).
- Make the public `Canvas` a MosaicKit canvas and make every drawing operation add immutable
  MosaicKit layers.
- Use BezierKit as the source of truth for implicit utility curves and native curve export.
- Move multi-panel composition to `mosaickit.CanvasGrid`.
- Preserve config, themes, CLI commands, numerical models, and the `econ_viz` compatibility
  distribution where they do not expose Matplotlib objects.
- Remove the direct `matplotlib` dependency and enforce the boundary with architecture tests.

## Non-goals

- Removing Matplotlib from MosaicKit's own renderer dependency graph.
- Preserving direct access to `.ax`, `.fig`, Matplotlib artists, contour sets, or arbitrary
  Matplotlib keyword arguments. Those were backend leaks rather than the supported 2.0 API.
- Making `principle-viz` depend directly on BezierKit when it has no curved geometry requiring it.

## Compatibility policy

The public names, constructor arguments, chaining behavior, economic results, and supported
PNG/PDF/SVG/TikZ outputs remain. Existing utility-viz style objects remain accepted and are
translated at the MosaicKit boundary. Backend-specific return values and escape hatches are
removed. Unsupported Matplotlib-only arguments fail clearly rather than being silently ignored.

## Architecture

`models` remains rendering-independent and owns utility functions, optimization, and economic
calculations. `core.scenes` owns factories that translate those results to MosaicKit layers;
BezierKit paths remain attached to `PathLayer.model`. The public `Canvas` subclasses or wraps
MosaicKit's canvas while exposing utility-specific fluent methods. Figure, animation, widgets,
CLI, and compatibility shims consume this public scene API only.

Legacy `core.rendering`, Matplotlib renderers, and drawing-oriented component modules are deleted
after their last caller moves. TikZ is generated from the same scene used for raster/vector
rendering, avoiding a second drawing implementation.

## Constraints

- Python `>=3.10,<4.0`.
- `mosaickit>=0.5.1,<0.6.0` and `bezierkit>=1.0.1,<2.0.0`.
- Production `utility_viz` must contain zero direct or dynamic Matplotlib imports.
- Economic-domain modules must not import MosaicKit.
- Every migration slice is test-first and leaves the full suite green before the next slice.
- The final wheel must not declare Matplotlib directly.

## Completion criteria

- `rg '^(from|import) matplotlib' utility_viz` returns no matches.
- The root `utility_viz.Canvas` is a MosaicKit `Canvas` and has no `.ax`/`.fig` state.
- All public diagram families render through scene layers.
- PNG, PDF, SVG, and TikZ smoke tests pass from public APIs.
- Architecture tests ban Matplotlib across all production modules.
- The complete test suite, Ruff, and mypy pass.

