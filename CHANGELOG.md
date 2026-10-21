# CHANGELOG

<!-- version list -->

## Unreleased

### Breaking changes

- Fonts behave as in every diagram package built on MosaicKit. `font` is `"sans"` (the default),
  `"serif"` or `"mono"`, not the name of an installed font family: any other value raises
  `InvalidParameterError`. Pass `fonts=TextFonts(...)` to replace any of the three with your font
  files; the rest keep the defaults.
- `math_font` takes a `mosaickit.MathFont` or the path of an OpenType math font file, and math is set
  through GlyphKit; without it math is set by Matplotlib. The names `dejavusans`, `dejavuserif`, `cm`,
  `stix` and `stixsans` are no longer accepted.
- `utility-viz.toml`: `[font] text` is a generic font, `[font] math` is a math font file, and a new
  `[fonts]` table lists the font files (`sans`, `serif`, `mono`); relative paths follow the config
  file. `Config.fonts` and `Canvas(fonts=...)`, `Figure(fonts=...)` are new.
- Requires `mosaickit>=0.9.1,<0.10.0` (TikZ export of the generic font needs 0.9.2).

## v2.0.0b3 (2026-10-20)

### Changes

- Use MosaicKit's `DashStyle` and `ArrowStyle` instead of keeping copies:
  `LineStyle` is now `DashStyle` under its old name, and `ArrowStyle` is
  MosaicKit's (`ArrowStyle.SIMPLE` is `OPEN`; `"->"` and `"-|>"` are still
  accepted). Require `mosaickit>=0.8.0,<0.9`.
- Delegate GIF encoding to KineticKit and whole-scene or grid TikZ export to
  MosaicKit. UtilityViz now retains only its economic scene construction and a
  small BezierKit path-serialization adapter.
- Stop probing system fonts in UtilityViz; font-family hints are passed to the
  renderer-owned compatibility path unchanged.

## v2.0.0b2 (2026-10-10)

### Breaking changes

- Complete the MosaicKit/BezierKit migration: `Canvas`, `Figure`, animation,
  interactive widgets, demand diagrams, and Edgeworth boxes now compose backend-neutral
  scenes. The renderer-owned `Canvas.fig` and `Canvas.ax` escape hatches and `fig=`/`ax=`
  injection are no longer available; compose panels with `Figure` instead.

### Bug fixes

- Require the stable `bezierkit>=1.0.1,<2.0.0` release instead of the obsolete
  `0.5.0rc1` release-candidate range, so a normal `uv add utility-viz` no longer
  installs a pre-release BezierKit.

### Maintenance

- Verify the stable BezierKit 1.x API against level-set tracing, sampled scene
  paths, native TikZ export, and the complete UtilityViz test suite.

- Remove the legacy axes-mutating drawing modules and the direct Matplotlib dependency.
  PNG/PDF/SVG output is rendered through MosaicKit, while TikZ serializes the same scene
  and preserves native BezierKit curves.

## v2.0.0b1 (2026-10-03)

### Breaking changes

- Rename the distribution to `utility-viz`, the import package to `utility_viz`, the CLI to `utility-viz`, and the default config file to `utility-viz.toml`; a 2.x `econ_viz` compatibility package, `econ-viz` command, and `econ-viz.toml` lookup remain until 3.0.0 (#132). The compatibility package and command are shipped by a separate `econ-viz` distribution (`packages/econ-viz`, released in lockstep and depending on `utility-viz==<same version>`), not by `utility-viz`: `pip install utility-viz` has no `econ_viz`, and `pip install --upgrade econ-viz` on a 1.x installation no longer deletes files shared with `utility-viz` (#154)

- Reorganise internals into `core/` (styles, themes, rendering, canvas, layout, diagrams, export, config, errors, constants, animation, interactive) and `models/` (utility, curves, consumer, optimization, analysis); deep `core` imports are advanced/internal APIs (#131)

### Behaviour notes

- `import econ_viz` emits one `UtilityVizDeprecationWarning` per process; `econ_viz.Canvas`, `Figure` and `Animator` additionally warn on construction and `econ_viz.Layout` on access. `isinstance`/`issubclass` against these legacy classes accept instances and classes of the 2.x counterparts, and vice versa

- `Config.load()` with no argument looks up `utility-viz.toml`, then legacy `econ-viz.toml` (with a warning) and raises `InvalidParameterError` ("config file not found") if neither exists, as in 1.x; `Config.discover()` falls back to the built-in defaults instead

- `utility-viz plot` without `--config` now reads `utility-viz.toml` (or legacy `econ-viz.toml`, with a warning; the new file wins if both exist) from the current directory, otherwise uses the defaults. An explicit `--config` still wins. Previously no file was read unless `--config` was passed

- `core/styles` no longer imports Matplotlib: `Fill` colour and `Marker` shape checks are now registered by the rendering layer, and an architecture test keeps styles and themes Matplotlib-free (#154)

### Features

- Add `utility_viz.core.scenes`: backend-neutral mosaickit layer factories for the budget constraint (`budget_layers`), equilibrium bundle (`equilibrium_layers`) and Cobb-Douglas-class indifference curves (`indifference_layers`), concept-local `utility.*` theme roles and `UTILITY_THEME`, plus `models.curves.trace_level_sets` (bezierkit marching-squares tracing) and `core.scenes.canvas_to_tikz` (native Bezier TikZ export from the same scene). Additive: legacy drawing modules are unchanged. `mosaickit>=0.5.1,<0.6.0` and `bezierkit>=0.5.0rc1,<0.6.0` are new dependencies (Refs #150)

- Add `UtilityVizError` as the canonical base exception; `EconVizError` remains as an alias of the same class (#154)

- Add `UtilityVizDeprecationWarning` (a `FutureWarning`) stating deprecated-since, removal version, and replacement

- Add `Config.discover()` and a lookup order of explicit path, `utility-viz.toml`, legacy `econ-viz.toml`, defaults

- Add `utility-viz init --migrate`

- Add architecture and public-API tests that enforce package layering and the root facade

- Split long functions and the Edgeworth box module into private helpers and `edgeworth_style`, `edgeworth_focus` and `edgeworth_exchange` modules without changing the public API or rendered output (#154)

### Changes

- Make the whole repository (library, tests, examples) pass `mypy .`, split `apply_strokes` into helpers to satisfy the complexity limit, clear remaining long-line and commented-out-code lint findings, and run `mypy .` in CI (#154)

### Maintenance

- The repository is now a uv workspace: development uses `uv sync --all-packages`, the release workflow builds and publishes both distributions with `uv build --all-packages` after checking that the tag matches both versions, and `scripts/release.sh` bumps both versions and the `utility-viz==` pin together (#154)

- Split `core/canvas/base.py` into cohesive modules (`style`, `layers`, `decomposition`, `legend`, `output`) and break long methods into private helpers; `Canvas` and its public API are unchanged (#154)

- Enable Ruff `E501` (line length 120), `C901` (complexity 10) and `PLR0915` (50 statements) in the lint config, wrapping one long docstring line and splitting `repair_corners` and `canvas_to_tikz` into private helpers with identical output (#154)

### Bug fixes

- Indifference curves of kinked utilities (Leontief, piecewise `min`/`max` `CustomUtility`, ...) now keep exact right-angle corners instead of a chamfered diagonal, in Matplotlib and TikZ output; the TikZ exporter also drops repeated consecutive vertices

- Turn `utility_viz.core.diagrams.consumer.edgeworth` into a subpackage (`box`, `style/`, `focus/`, `exchange/`, `plotting/`, `methods/`) with no module over 250 lines; `EdgeworthBox` and `EquilibriumFocusConfig` import from the same path and rendered output is unchanged (#154)

## v1.12.0 (2026-09-26)

### Features

- Add `highlight_level` to `Canvas.add_utility(...)` so one focal indifference curve can be emphasized while the remaining levels are drawn as a subdued secondary set

- Add `secondary_stroke` plus theme-level secondary curve colour, linewidth, and opacity controls

- Add numeric and textbook-style ordinal curve labels (`u_1`, `u_2`, ...) with tangent-aligned placement that stays inside the visible plotting area

- Add a before/after/ordinal example for the indifference-curve hierarchy workflow

### Changes

- Apply indifference-curve label styling consistently to focal and secondary labels, while preserving smooth, linear, kinked, and satiation preferences

## v1.11.0 (2026-09-26)

### Features

- Complete the theme system so Canvas, Figure, decomposition diagrams, and Edgeworth boxes consistently use theme-defined backgrounds, labels, strokes, markers, and auxiliary economic lines

- Add four purpose-built themes: `paper` for journal figures, `monochrome` for black-and-white printing, `presentation` for projected slides, and `dark` for dark interfaces

- Add theme-level `background_color` and `label_scale` controls, plus defaults for titles, boxes, paths, kinks, bliss points, contract curves, cores, endowments, prices, and Walrasian equilibria

### Changes

- Make CLI/config theme resolution recognize every built-in theme and preserve visual semantics across Canvas, Figure, DemandDiagram, and EdgeworthBox

## v1.10.1 (2026-09-26)

### Maintenance

- Add Ruff linting and formatting checks plus Mypy type checking to local contributor tooling and CI

- Publish `econ-viz` as a PEP 561 typed package with an included `py.typed` marker

- Standardize the remaining public exception messages in English

### Bug Fixes

- Import NumPy in `analysis.levels`, fixing the unresolved `np.ndarray` annotation

- Bind the Pareto-search weight in each Edgeworth objective closure, preventing every objective from reusing the final loop value

## v1.10.0 (2026-09-26)

### Features

- Add `Config`, which loads diagram settings from an `econ-viz.toml` file: section names map to Theme properties (`[stroke.budget]`, `[label.point]`, `[marker.equilibrium]`, `[fill.budget]`, `[legend]`), plus `[color]`, `[font]`, and a `base` theme; `Config.load(...).use()` makes it the default for later diagrams

- Add `econ-viz init`, which writes a commented settings template, and `econ-viz plot --config FILE`

### Changes

- `Canvas`, `Figure`, and `EdgeworthBox` take their theme and fonts from the active `Config` when none is passed; with no config the output is unchanged

- Add `tomli` as a dependency on Python 3.10

## v1.9.0 (2026-09-26)

### Features

- Draw the indifference curves of a price-effect decomposition by default: U0 through A, U1 through C, and the curve through B under Slutsky; `show_curves=False` restores the previous figure, and `curve_stroke` / `curve_label` restyle and label them

- Add the `Haagsma` utility model (Haagsma, 2012), whose good x is always inferior and Giffen at high enough income, with closed-form `demand()` and `is_giffen()`

- Add `Legend`, placed automatically where it covers the least of the diagram (moving outside the plot area when every corner is taken), or at a chosen inside corner or outside side

- Accept `Label` for every text element: axis labels, the origin, titles, effect labels, and Edgeworth box text

- Add `opacity` to `Stroke`, `Marker`, `Label`, `Legend`, `Effect`, and `Fill`

### Changes

- Existing decomposition figures now include their indifference curves; pass `show_curves=False` if you already draw them with `add_utility`

- Effect range arrows below the x-axis point one way (A to B, B to C), and a zero effect draws no range arrow

- `Fill.alpha` becomes shorthand for `Fill.opacity`

### Bug Fixes

- Solve utility maximisation to a much tighter tolerance, so comparative statics and Slutsky matrices are accurate

- Draw indifference curves at negative utility levels as solid lines

- Make `scripts/release.sh` work on macOS

## v1.8.0 (2026-09-26)

### Features

- Add `Effect` to set the colour, range-arrow height, and label (text and position) of each price-effect decomposition effect

- Add `Marker` for point colour, size, and shape across `Canvas`, `DemandDiagram`, and `EdgeworthBox`

- Add `Label` for point-label text, position (four sides and four corners), offset, colour, size, and visibility; labels follow their point's `Marker` colour, and the decomposition's A/B/C labels can be hidden

- Add `Fill` so the budget-set shading can have its own colour and opacity

- Add `Axis` to set one axis's label, label position, and stroke in `Canvas`, `Figure`, `DemandDiagram`, and `EdgeworthBox`

- Add theme defaults for markers, labels, and fills, such as `theme.eq_marker`, `theme.point_label`, and `theme.budget_fill`

### Changes

- Reduce the default equilibrium point size from `6` to `4`

- Document `Stroke` as the preferred way to style lines; the separate `color` / `linewidth` / `linestyle` arguments remain as shorthand

### Bug Fixes

- Draw wedge arrowheads at a fixed on-screen size instead of stretching them along the whole line

- Apply `stroke_a` / `stroke_b` in `EdgeworthBox.add_equilibrium_indifference` and `add_indifference_curves_from_equilibrium`

## v1.7.0 (2026-09-25)

### Features

- Add independent axis-label positions, line styles, and arrowhead styles to `Canvas` and `Figure`

- Add per-figure `font` and `math_font` controls without changing Matplotlib's global configuration

- Add `Stroke` for per-line width, style, colour, and arrowheads across `Canvas`, `Figure`, `DemandDiagram`, and `EdgeworthBox`

- Add `econ-viz --version`

### Bug Fixes

- Validate utility-model parameter domains, correct the asymmetric CES expansion path and Cobb-Douglas limit, and allow satiation optima to leave budget unspent

- Make contour levels robust around zero and negative utility values

- Use one-sided finite differences when comparative statics approach price, income, or subsistence boundaries

- Make every example script runnable from a clean checkout

- Require tests to pass before tagged releases publish and include complete package licence metadata

### Maintenance

- Migrate package management and builds to `uv`

- Centralize shared numerical, rendering, and logging defaults

- Test Python 3.10 through 3.13, enforce branch coverage, and smoke-test all runnable examples in CI

- Document and automate the release workflow

## v1.6.0 (2026-04-24)

### Features

- Adopt a color-blind-friendly default palette and expose reusable `themes.COLORBLIND_CYCLE_RGB` / `themes.COLORBLIND_CYCLE_HEX`

- Reduce default IC linewidth from `2.0` to `1.8` for improved visual balance

### Documentation

- Add explicit palette/citation references in README and backfill missing changelog entries for `v1.3.2` and `v1.5.0`

### Chores

- Move animation example from `examples/animation.py` to `examples/scripts/animation.py` so `examples/` root only contains `__init__.py` and `scripts/`

- Stop tracking generated outputs under `examples/output/**` and remove tracked `examples/output/tikz/main.tex`

### Tests

- Update TikZ axis-spine regression assertion to avoid hard-coded color-index coupling

## v1.5.0 (2026-04-21)

### Features

- Add pure TikZ export backend (`econ_viz.io.backend_tikz`) and `.tex` support in `Canvas.save(...)` / `Figure.save(...)`

- Add price-effect decomposition APIs:
  - `decompose_price_effect(...)` / `PriceEffectDecomposition`
  - `Canvas.add_decomposition(...)` for A/B/C bundles, budget lines, and substitution/income overlays

- Expose decomposition interfaces at package root (`econ_viz.__init__`) for direct imports

- Expand examples with dedicated scripts for decomposition, demand diagrams, PCC/ICC paths, multi-layout figures, and multi-case TikZ export

### Refactors

- Improve axis-label placement and visibility toggling behavior for shared-panel layouts

### Tests

- Add dedicated regression tests for TikZ rendering/export and decomposition flows (`tests/test_tikz_backend.py`, `tests/test_optimizer.py`, `tests/test_canvas.py`)

### Bug Fixes

- Make notebook Colab install flow restart-safe

## v1.4.0 (2026-04-09)

### Features

- Add `Animator` class (`econ_viz.animation`) for parameter-sweep GIF export via Pillow — no ffmpeg required (closes #44)

- Add `WidgetViewer` class (`econ_viz.interactive`) for Jupyter notebook slider controls via ipywidgets (closes #45)

- Add optional dependency extras: `pip install econ-viz[animation]`, `pip install econ-viz[interactive]`, `pip install econ-viz[all]`

- Expand `examples/animation.py` with parameter, price, income, and budget-only GIF sweeps across common utility families

- Improve GIF export reliability by compositing frames onto a solid background and using restore-to-background disposal

- Extend notebook and widget examples so parameters can be adjusted by slider or direct numeric input in live Jupyter sessions

### Tests

- Add test coverage for Animator (init validation, GIF output, Pillow guard, frame disposal)

- Add test coverage for WidgetViewer (init validation, slider builder, numeric inputs, dependency guards)

## v1.3.2 (2026-04-03)

### Bug Fixes

- Enforce dashed black defaults for Edgeworth contract curves and price lines

### Chores

- Update publish workflow to skip uploading versions that already exist on PyPI

## v1.3.1 (2026-04-03)

### Features

- Add modular `Edgeworth` internals with dedicated compute/state/plotter helpers (`edgeworth_compute`, `edgeworth_state`, `edgeworth_plotter`)

- Add model registry (`models.registry`) and route CLI model construction through the registry

### Refactors

- Decouple CLI argument resolution from process exit flow:
  - introduce `CliConfigError`
  - centralize stderr/exit handling in `cli.main`

- Introduce shared contour level policies under `contours.level_policies` and reuse them across analysis/components/consumer paths

- Introduce shared figure exporter (`io.exporter`) and unify save logic across `Canvas`, `Figure`, and `EdgeworthBox`

- Split Canvas rendering responsibilities with renderer modules (`canvas.renderers.*`) and low-level primitives (`canvas.primitives`)

- Convert package root exports in `econ_viz.__init__` to lazy loading while preserving the public API surface

### Documentation

- Expand playground notebook with a complete Edgeworth Box section and export examples

## v1.3.0 (2026-04-03)

### Features

- Add `EdgeworthBox` and `EquilibriumFocusConfig` APIs for two-consumer exchange diagrams

- Add contract-curve construction (`mrs` / Pareto fallback), core rendering, Walrasian equilibrium overlay, and equilibrium-focused indifference-curve rendering

- Add `examples/edgeworth_box.py` covering common utility-function combinations

- Add dedicated Edgeworth test coverage in `tests/test_edgeworth.py`

## v1.2.3 (2026-03-31)

### Features

- Extend `SlutskyMatrix` with symmetry, negative-semidefiniteness, and homogeneity checks, plus validation warnings for failed theoretical conditions

- Expand CLI model coverage to include `QuasiLinear`, `StoneGeary`, and `Translog`

## v1.2.2 (2026-03-31)

### Bug Fixes

- Smooth PCC/ICC paths by default, extend endpoints slightly, and hide path markers unless requested

- Separate PCC/ICC path colours from indifference-curve colours and widen goods-space padding in demand diagrams

- Add a dedicated PCC/ICC example generator and coverage for path defaults and rendering

## v1.2.0 (2026-03-30)

### Features

- Add multi-panel `Figure` layouts and `Layout` enum (closes #7)

- Add linked `DemandDiagram` for Marshallian demand teaching figures (closes #31)

- Add `PricePath` / `IncomePath` helpers and `Canvas.add_path()` for PCC/ICC plots (closes #5)

## v1.1.0 (2026-03-30)

### Features

- Add comparative_statics helper (closes #12) ([#29](https://github.com/EconViz/econ-viz/pull/29),
  [`063def0`](https://github.com/EconViz/econ-viz/commit/063def0ee9677ca6dcf1bce8926fa4a4f248a021))

- Add HomogeneityAnalyzer and ReturnsToScale to analysis submodule (closes #14)
  ([#29](https://github.com/EconViz/econ-viz/pull/29),
  [`063def0`](https://github.com/EconViz/econ-viz/commit/063def0ee9677ca6dcf1bce8926fa4a4f248a021))

- Add Translog model (#9) and legend/IC label support
  ([#29](https://github.com/EconViz/econ-viz/pull/29),
  [`063def0`](https://github.com/EconViz/econ-viz/commit/063def0ee9677ca6dcf1bce8926fa4a4f248a021))


## v1.0.2 (2026-03-29)

### Bug Fixes

- Prevent double-wrap of math axis labels (closes #2)
  ([`7ee20a2`](https://github.com/EconViz/econ-viz/commit/7ee20a2b79e64f399d65c161a9776259a7dde092))

- Remove numpy upper bound to prevent Colab environment conflicts
  ([`b2e977f`](https://github.com/EconViz/econ-viz/commit/b2e977fbc58423ff4e63fd9846d404d236fb2347))


## v1.0.1 (2026-03-29)

### Bug Fixes

- Pin numpy<2 to prevent ABI mismatch on Colab and local installs
  ([`127bc26`](https://github.com/EconViz/econ-viz/commit/127bc26a19cb1c25e16339838e9f88dd4a2e3f5f))

### Chores

- Relax python/numpy bounds, pin pytest to 8.x
  ([`8dda610`](https://github.com/EconViz/econ-viz/commit/8dda6100c8c8c085c9f2b7bb98f7842ca60aa6a1))

### Documentation

- Add Stone-Geary to README, update test count badge
  ([`112d6a6`](https://github.com/EconViz/econ-viz/commit/112d6a6f069c34a3252523a333d8ea988b5b458b))


## v1.0.0 (2026-03-28)

- Initial Release
