# Complete MosaicKit Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace every utility-viz-owned drawing path with MosaicKit scenes and BezierKit geometry while retaining the documented 2.0 API.

**Architecture:** Numerical models remain independent. Utility-specific scene factories produce MosaicKit layers, and a compatibility-oriented public Canvas composes those layers without exposing renderer objects. MosaicKit owns rendering and grids; BezierKit owns implicit curves and native curve export.

**Tech Stack:** Python 3.10+, MosaicKit 0.5.x, BezierKit 1.x, pytest, Ruff, mypy.

**Spec:** `docs/superpowers/specs/2026-10-10-complete-mosaickit-migration-design.md`

## Global Constraints

- Preserve documented 2.0 public names and fluent calls.
- Do not preserve `.ax`, `.fig`, Matplotlib artists, or arbitrary Matplotlib kwargs.
- No production module under `utility_viz` may import Matplotlib.
- Models do not import MosaicKit; scene factories own presentation translation.
- Use the same scene for raster/vector and TikZ output.

## Review Focus

- Kinked and disconnected implicit curves retain exact components and Bezier models.
- Configured colors, dash styles, arrows, markers, labels, fonts, and opacity survive style conversion.
- Multiple canvases render with the declared layout and without shared mutable scene state.
- Legacy `econ_viz` imports resolve to the same new public objects with the documented warnings.
- Unsupported backend-specific arguments produce actionable utility-viz errors.

---

### Task 1: Enforce the target boundary and add style conversion

**Files:**
- Modify: `tests/test_architecture.py`
- Create: `tests/scenes/test_style_bridge.py`
- Create: `utility_viz/core/scenes/styles.py`
- Modify: `utility_viz/core/scenes/theme.py`

**Interfaces:**
- Produces: `to_mosaic_stroke`, `to_mosaic_fill`, `to_mosaic_marker`, `to_mosaic_text`, and `to_mosaic_theme`.

- [ ] Add failing tests that ban Matplotlib across the package and pin every public style conversion.
- [ ] Run the focused tests and verify failures identify current Matplotlib modules/missing converters.
- [ ] Implement style and theme conversion without importing rendering backends.
- [ ] Run focused scene/style tests and commit the green slice.

### Task 2: Replace the public Canvas and basic diagram operations

**Files:**
- Rewrite: `utility_viz/core/canvas/base.py`
- Rewrite: `utility_viz/core/canvas/layers.py`
- Rewrite: `utility_viz/core/canvas/output.py`
- Extend: `utility_viz/core/scenes/{budget,equilibrium,indifference}.py`
- Create: `utility_viz/core/scenes/primitives.py`
- Rewrite: `tests/canvas/test_canvas.py` and focused canvas tests as scene assertions

**Interfaces:**
- Produces: `Canvas(MosaicCanvas)` with `add_utility`, `add_budget`, `add_equilibrium`, `add_point`, `add_path`, `show_legend`, `show`, and `save`.

- [ ] Add failing public-Canvas identity and scene-content tests.
- [ ] Verify they fail because the root Canvas is still Matplotlib-backed.
- [ ] Implement the MosaicKit Canvas facade and basic operations using scene factories.
- [ ] Run all canvas, scene, public API, and compatibility tests; commit the green slice.

### Task 3: Move Figure, export, animation, and widgets to MosaicKit

**Files:**
- Rewrite: `utility_viz/core/layout/figure.py`
- Rewrite: `utility_viz/core/animation/animator.py`
- Rewrite: `utility_viz/core/interactive/widgets.py`
- Replace: `utility_viz/core/export/*` with scene-based export adapters
- Modify corresponding tests under `tests/canvas`, `tests/animation`, `tests/interactive`, and `tests/io`

**Interfaces:**
- Produces: Figure backed by `CanvasGrid`; animation backed by MosaicKit parameters/animation; `save_figure` dispatching Canvas/Grid or TikZ scene export.

- [ ] Add failing tests asserting no renderer objects are retained and all formats use scene snapshots.
- [ ] Implement grid, output, animation, and widget adapters one behavior at a time.
- [ ] Run focused tests and commit the green slice.

### Task 4: Migrate decomposition and consumer diagrams

**Files:**
- Create scene factories under `utility_viz/core/scenes/decomposition.py` and `utility_viz/core/scenes/consumer/`
- Rewrite callers under `utility_viz/core/diagrams/consumer/`
- Remove superseded `core/canvas/renderers/` modules
- Rewrite tests in `tests/canvas/test_decomposition_curves.py` and `tests/consumer/test_edgeworth.py`

**Interfaces:**
- Produces: MosaicKit layers for price decomposition, demand paths, Edgeworth frames, indifference pairs, contract/core/price lines, endowment, and Walrasian equilibrium.

- [ ] Add failing scene-structure and numerical-coordinate tests for each diagram family.
- [ ] Implement factories incrementally, retaining Bezier models on curved paths.
- [ ] Switch public callers and remove each dead legacy renderer after its tests pass.
- [ ] Run consumer and full canvas suites; commit the green slice.

### Task 5: Remove the legacy drawing stack and direct dependency

**Files:**
- Delete dead modules under `utility_viz/core/rendering`, legacy export backend, and legacy drawing components
- Modify: `utility_viz/__init__.py`, `pyproject.toml`, `uv.lock`, README, CONTRIBUTING, CHANGELOG
- Modify: `tests/test_architecture.py`, `tests/test_public_api.py`, compatibility and CLI tests

**Interfaces:**
- Produces: a single public scene pipeline with no utility-viz-owned backend code.

- [ ] Tighten the architecture test to reject Matplotlib anywhere in production code and verify it fails before deletion.
- [ ] Remove dead imports/modules and the direct dependency; update lockfile and documentation.
- [ ] Build both `utility-viz` and the `econ-viz` shim and inspect wheel contents/metadata.
- [ ] Run pytest, Ruff, mypy, package builds, and public render smoke tests.
- [ ] Commit the completed migration.

