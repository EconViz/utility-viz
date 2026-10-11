"""Architecture contract: package layering, no cycles, private helpers stay local.

Dependency direction (a unit may import only from a strictly lower layer)::

    errors, constants                         layer 0
    enums, utils                              layer 1
    core.styles, models.utility               layer 2
    core.themes, core.export,
        models.optimization, models.curves    layer 3
    core.config, core.rendering,
        models.analysis, models.consumer      layer 4
    core.scenes                               layer 5
    core.diagrams.components                  layer 6
    core.canvas                               layer 7
    core.layout                               layer 8
    core.diagrams.consumer, core.animation,
        core.interactive                      layer 9
    models (facade), cli                      layer 10
    root facade                               layer 11
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PACKAGE = "utility_viz"
ROOT = Path(__file__).resolve().parent.parent / PACKAGE

LAYERS: dict[str, int] = {
    "core.errors": 0,
    "core.constants": 0,
    "enums": 1,
    "utils": 1,
    "core.styles": 2,
    "models.utility": 2,
    "core.themes": 3,
    "core.export": 3,
    "models.optimization": 3,
    "models.curves": 3,
    "core.config": 4,
    "core.rendering": 4,
    "models.analysis": 4,
    "models.consumer": 4,
    "core.scenes": 5,
    "core.diagrams.components": 6,
    "core.canvas": 7,
    "core.layout": 8,
    "core.diagrams.consumer": 9,
    "core.animation": 9,
    "core.interactive": 9,
    "models": 10,
    "cli": 10,
    "": 11,
}


def _modules() -> list[tuple[str, Path]]:
    out = []
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT).with_suffix("")
        parts = list(rel.parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        out.append((".".join(parts), path))
    return out


def _imports(path: Path) -> list[str]:
    """Return imported module names (relative to the package, '' for the root)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.level == 0, f"{path}: relative imports are not allowed"
            mod = node.module or ""
            if mod == PACKAGE or mod.startswith(PACKAGE + "."):
                base = mod[len(PACKAGE) :].lstrip(".")
                if base == "":
                    # ``from utility_viz import x`` -> importing the root facade
                    found.append("")
                else:
                    found.append(base)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == PACKAGE or alias.name.startswith(PACKAGE + "."):
                    found.append(alias.name[len(PACKAGE) :].lstrip("."))
    return found


def _unit_of_module(module: str) -> str:
    # Resolve through the longest matching unit prefix; fall back to root.
    best = None
    for unit in LAYERS:
        if not unit:
            continue
        if (module == unit or module.startswith(unit + ".")) and (best is None or len(unit) > len(best)):
            best = unit
    if best is not None:
        return best
    return "models" if module == "models" else ""


def _edges() -> dict[tuple[str, str], list[str]]:
    edges: dict[tuple[str, str], list[str]] = {}
    for module, path in _modules():
        src = _unit_of_module(module)
        for target in _imports(path):
            dst = _unit_of_module(target)
            if src != dst:
                edges.setdefault((src, dst), []).append(f"{module or PACKAGE} -> {target or PACKAGE}")
    return edges


def test_every_module_belongs_to_a_known_layer():
    """New subpackages must be added to LAYERS (and the docs) deliberately."""
    unknown = []
    for module, _ in _modules():
        if module in ("", "core", "core.diagrams"):  # namespace packages
            continue
        unit = _unit_of_module(module)
        if unit == "":
            unknown.append(module)
    # Only the root facade module itself may map to the root layer.
    assert not unknown, f"modules outside the declared layers: {unknown}"


def test_dependencies_only_point_to_lower_layers():
    violations = []
    for (src, dst), samples in _edges().items():
        if LAYERS[src] <= LAYERS[dst]:
            violations.append(f"{src or 'root'} (L{LAYERS[src]}) -> {dst or 'root'} (L{LAYERS[dst]}): {samples[:2]}")
    assert not violations, "\n".join(violations)


def test_no_circular_dependencies_between_units():
    graph: dict[str, set[str]] = {}
    for src, dst in _edges():
        graph.setdefault(src, set()).add(dst)

    visiting: set[str] = set()
    done: set[str] = set()

    def visit(node: str, trail: list[str]) -> None:
        if node in done:
            return
        assert node not in visiting, f"cycle: {' -> '.join([*trail, node])}"
        visiting.add(node)
        for nxt in graph.get(node, ()):
            visit(nxt, [*trail, node])
        visiting.discard(node)
        done.add(node)

    for node in list(graph):
        visit(node, [])


def test_no_generic_helper_package():
    assert not (ROOT / "helper").exists()
    assert not (ROOT / "helpers").exists()


def test_private_names_are_not_imported_across_units():
    """Underscore-prefixed helpers stay local to the unit that owns them."""
    offenders = []
    for module, path in _modules():
        src = _unit_of_module(module)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or not node.module:
                continue
            if not (node.module == PACKAGE or node.module.startswith(PACKAGE + ".")):
                continue
            target = node.module[len(PACKAGE) :].lstrip(".")
            if _unit_of_module(target) == src:
                continue
            private_module = any(p.startswith("_") for p in target.split(".") if p)
            private_names = [a.name for a in node.names if a.name.startswith("_")]
            if private_module or private_names:
                offenders.append(f"{module}: from {node.module} import {', '.join(a.name for a in node.names)}")
    assert not offenders, "\n".join(offenders)


@pytest.mark.parametrize("module", [m for m, _ in _modules() if m])
def test_modules_have_no_relative_imports(module):
    path = ROOT.joinpath(*module.split("."))
    path = path / "__init__.py" if path.is_dir() else path.with_suffix(".py")
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom):
            assert node.level == 0


def test_utility_viz_never_depends_on_the_legacy_package():
    """Deleting ``econ_viz`` in 3.0 must be a pure removal."""
    offenders = []
    for module, path in _modules():
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = []
            if isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            elif isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            if any(n == "econ_viz" or n.startswith("econ_viz.") for n in names):
                offenders.append(module)
    assert not offenders, offenders


_SCENE_FORBIDDEN = (
    "matplotlib",
    "utility_viz.core.canvas",
    "utility_viz.core.themes",
    "utility_viz.core.export",
    "utility_viz.core.rendering",
)


def test_scene_modules_import_no_matplotlib_or_legacy_drawing():
    """``core.scenes`` builds MosaicKit layers only, with no legacy drawing imports."""
    offenders = []
    scene_modules = [(m, p) for m, p in _modules() if m == "core.scenes" or m.startswith("core.scenes.")]
    assert scene_modules, "core.scenes package is missing"
    for module, path in scene_modules:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            elif isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            else:
                continue
            for name in names:
                if any(name == bad or name.startswith(bad + ".") for bad in _SCENE_FORBIDDEN):
                    offenders.append(f"{module}: {name}")
    assert not offenders, offenders


def test_models_curves_import_no_matplotlib():
    offenders = []
    for module, path in _modules():
        if module != "models.curves" and not module.startswith("models.curves."):
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = (
                [node.module]
                if isinstance(node, ast.ImportFrom) and node.module
                else [a.name for a in node.names]
                if isinstance(node, ast.Import)
                else []
            )
            offenders += [f"{module}: {n}" for n in names if n == "matplotlib" or n.startswith("matplotlib.")]
    assert not offenders, offenders


PURE_DATA_UNITS = ("core.styles", "core.themes")


def _third_party_roots(path: Path) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            roots.update(a.name.split(".")[0] for a in node.names)
    return roots


def test_production_code_has_no_direct_matplotlib_dependency():
    offenders = {module for module, path in _modules() if "matplotlib" in _third_party_roots(path)}
    assert not offenders, sorted(offenders)


def test_styles_and_themes_are_pure_data_without_matplotlib():
    """Styles and themes are renderer-neutral data."""
    offenders = [
        module
        for module, path in _modules()
        if _unit_of_module(module) in PURE_DATA_UNITS and "matplotlib" in _third_party_roots(path)
    ]
    assert not offenders, f"matplotlib imported by pure-data modules: {offenders}"
