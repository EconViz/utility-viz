# Contributing to utility-viz

Thank you for your interest in contributing! This guide covers everything you need to get started.

## Setting up the development environment

```bash
git clone https://github.com/EconViz/utility-viz.git
cd utility-viz
uv sync --all-packages --all-extras
```

The repository is a uv workspace with two distributions released in lockstep:
`utility-viz` (the root, `utility_viz/`) and `econ-viz` (`packages/econ-viz/`), the deprecated
1.x name that ships the `econ_viz` compat package and the `econ-viz` command. `--all-packages`
installs both in editable mode, which `tests/compat` needs.

Run the complete local quality gate:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy .
```

Tests are grouped by package domain under `tests/`. The default command
measures statement and branch coverage and enforces the project coverage floor.
Use `uv run ruff format .` to apply formatting before rerunning the check.

## How to contribute

- **Bug reports** — open an issue with a minimal reproducible example
- **Feature requests** — open an issue describing the use case
- **Pull requests** — fork the repo, create a branch, and open a PR against `main`

Please make sure all tests pass before submitting a PR.

## Before you start — check the Project board

All planned work is tracked on the **[utility-viz Roadmap](https://github.com/orgs/EconViz/projects/1)**.

Before picking up an issue:

1. Check the board to see what is already **In Progress** — don't duplicate work.
2. Find an unassigned issue in **Todo** that you want to tackle.
3. Leave a comment on the issue saying you're working on it, then move it to **In Progress**.

This keeps everyone from stepping on each other.

## Good first issues

Issues labelled [`good first issue`](https://github.com/EconViz/utility-viz/issues?q=label%3A%22good+first+issue%22) are a great starting point. They are self-contained and well-documented.

## Package architecture

The package is organised into a small number of cohesive subpackages. Imports
must point **down** the layer table below (enforced by `tests/test_architecture.py`,
which also forbids cycles and relative imports).

```
utility_viz/
  __init__.py      root facade (public API, lazy)               layer 11
  cli/             command-line interface                      layer 10
  models/          facade re-exporting the economic models     layer 10
    utility/ curves/ consumer/ optimization/ analysis/          layers 2-4  (never import utility_viz.core drawing code)
  core/            drawing, styling, export, runtime (advanced/internal API)
    errors/ constants/                                          layer 0
    styles/ themes/ export/ config/ rendering/                  layers 2-4
    scenes/                                                     layer 5
    diagrams/components/                                       layer 6
    canvas/ layout/                                             layers 7-8
    diagrams/consumer/ animation/ interactive/                  layer 9
  enums/ utils/    shared internal areas                        layer 1
```

- Public API = the root facade (`from utility_viz import Canvas, ...`) and `utility_viz.models`.
  Deep `utility_viz.core.*` imports are advanced/internal and may move between minor releases.
- Helpers live beside the feature that owns them and are underscore-prefixed
  (`_color.py`, `_require_pillow`). Do not add a generic top-level `helper/` package.
- Adding a subpackage? Register it (with a layer) in `tests/test_architecture.py`.

## Adding a component on mosaickit scenes (2.0 pattern)

New and migrated economic components build backend-neutral
[mosaickit](https://pypi.org/project/mosaickit/) layers instead of mutating renderer-owned axes.
`utility_viz/core/scenes/` is the reference slice (budget, equilibrium, Cobb-Douglas
indifference curves):

1. **Economics stays in utility-viz.** Solving, contour-level selection and curve tracing
   live under `models/` (no renderer dependency: bezierkit's `trace_implicit` via
   `models.curves.trace_level_sets`, `percentile_levels` for level choice). A scene factory only receives results.
2. **One factory per component** in `core/scenes/<component>.py`, returning a tuple of
   immutable layers (`PathLayer`, `FillLayer`, `MarkerLayer`, `TextLayer`) with stable ids
   (`budget`, `budget.fill`, `equilibrium.drop`, `ic.2.label`) so callers can `Canvas.remove`
   or reference them in a legend. Attach the economic object via `model=`. Take sparse
   `Stroke`/`Marker`/`Fill` overrides, never colours as positional arguments.
3. **Concept-local dotted roles** in `core/scenes/roles.py` (`utility.budget`,
   `utility.budget.compensated`, ...). A child role inherits its parent's fields, so only
   state what differs. Defaults go in `core/scenes/theme.py` (`utility_roles`), restating the
   legacy theme values; `tests/scenes/test_scene_theme.py` pins the parity.
4. **No direct renderer imports and no legacy drawing stack.** Production code builds
   MosaicKit scenes, while `models/curves` traces geometry with BezierKit;
   `tests/test_architecture.py` enforces the boundary. Render with MosaicKit:

   ```python
   canvas = Canvas(CanvasSpec(x_range=(0, 18), y_range=(0, 12)), theme=UTILITY_THEME)
   canvas.extend(quadrant_axes(18, 12)).extend(budget_layers(2, 3, 30, fill=True))
   canvas.save("diagram.png")
   ```
5. **Test** the factory's layers (ids, roles, geometry) and add the component to the
   end-to-end scene in `tests/scenes/test_scene_end_to_end.py`.

Geometry belongs to bezierkit and mosaickit stays curve-agnostic: curves are traced as
`PiecewiseBezier` paths, sampled to points for the mosaickit `PathLayer`, and the source path
is kept as `layer.model`. `core.scenes.canvas_to_tikz(canvas)` exports the same scene to TikZ
(native `.. controls ..` paths via `bezierkit.export.tikz`, theme-resolved styles). Limits: the
traced field must be finite (undefined values are floored), traced kinks follow the grid tolerance,
and only path, fill, marker and text layers are exported.

## Code style

- Python 3.10+
- Ruff enforces lint rules and formatting, including a 120-column line limit (`E501`), a McCabe
  complexity cap of 10 (`C901`) and at most 50 statements per function (`PLR0915`); split long
  functions into private helpers
- Mypy checks the `utility_viz` package
- Add tests for any new behaviour

## Releasing

Merging to `main` never publishes a release. PyPI publishing runs only when a `v*` tag is pushed.

1. Open the release PR:

   ```bash
   scripts/release.sh prepare X.Y.Z
   ```

2. On the release branch, add a `## vX.Y.Z (YYYY-MM-DD)` section to the top of `CHANGELOG.md`.
3. In [econ-viz-docs](https://github.com/EconViz/econ-viz-docs), add a row for the release to the changelog page in all three languages, leaving out documentation-only changes:
   - `docs/project/changelog.md`
   - `docs/zh-TW/project/changelog.md`
   - `docs/zh-CN/project/changelog.md`

   Also update any guides that cover features added in this release. Publish these docs changes only after the release is on PyPI.
4. Merge the release PR, then tag and publish:

   ```bash
   scripts/release.sh finalize X.Y.Z
   ```

## License

By contributing you agree that your work will be released under the [MIT License](LICENSE).
