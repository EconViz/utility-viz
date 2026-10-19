"""Root facade and models facade import contract (#131)."""

from __future__ import annotations

import importlib

import pytest

import utility_viz
import utility_viz.models as models_facade

AGREED_ROOT_EXPORTS = [
    # canvas / layout / configuration
    "Canvas", "Figure", "Config", "Layer",
    # themes and style objects
    "themes", "Theme", "Stroke", "Fill", "Label", "Legend", "Marker", "Axis", "Effect",
    # enums
    "UtilityType", "ExportFormat", "Layout", "ArrowStyle", "LabelPosition", "LineStyle",
    # public exceptions
    "UtilityVizError", "EconVizError", "ExportError", "InvalidParameterError", "OptimizationError", "ParseError",
    # diagrams
    "IndifferenceCurves", "BudgetConstraint", "EquilibriumPoint", "DemandDiagram", "EdgeworthBox",
    # economics (also available from utility_viz.models)
    "Equilibrium", "solve", "parse_latex", "CustomUtility", "MultiGoodCD",
]  # fmt: skip


@pytest.mark.parametrize("name", AGREED_ROOT_EXPORTS)
def test_agreed_root_export_resolves(name):
    assert hasattr(utility_viz, name)
    assert name in utility_viz.__all__


def test_every_name_in_all_resolves():
    for name in utility_viz.__all__:
        assert getattr(utility_viz, name) is not None, name


def test_root_dir_lists_public_names():
    assert set(utility_viz.__all__) <= set(dir(utility_viz))


def test_unknown_attribute_raises():
    with pytest.raises(AttributeError):
        utility_viz.DefinitelyNotAThing  # noqa: B018


def test_root_import_is_lazy():
    """Importing the root must not eagerly import heavy subpackages."""
    import subprocess
    import sys

    code = "import sys, utility_viz; sys.exit(0 if 'utility_viz.core.canvas.base' not in sys.modules else 1)"
    assert subprocess.run([sys.executable, "-c", code]).returncode == 0


@pytest.mark.parametrize("name", models_facade.__all__)
def test_models_facade_exports_resolve(name):
    assert getattr(models_facade, name) is not None


def test_models_facade_has_no_drawing_dependency():
    import subprocess
    import sys

    code = (
        "import sys, utility_viz.models; "
        "sys.exit(1 if any(m.startswith('utility_viz.core.canvas') for m in sys.modules) else 0)"
    )
    assert subprocess.run([sys.executable, "-c", code]).returncode == 0


@pytest.mark.parametrize(
    "module",
    [
        "utility_viz.core.canvas",
        "utility_viz.core.layout",
        "utility_viz.core.styles.stroke",
        "utility_viz.core.themes",
        "utility_viz.core.config",
        "utility_viz.core.errors",
        "utility_viz.core.export",
        "utility_viz.core.constants",
        "utility_viz.core.scenes",
        "utility_viz.core.diagrams.components",
        "utility_viz.core.diagrams.consumer",
        "utility_viz.core.animation",
        "utility_viz.core.interactive",
        "utility_viz.models.utility",
        "utility_viz.models.curves",
        "utility_viz.models.consumer",
        "utility_viz.models.optimization",
        "utility_viz.models.analysis",
        "utility_viz.enums",
        "utility_viz.utils",
        "utility_viz.cli",
    ],
)
def test_subpackages_import(module):
    importlib.import_module(module)


def test_econviz_error_is_alias_of_utilityviz_error():
    from utility_viz.core.errors.exceptions import EconVizError, UtilityVizError

    assert EconVizError is UtilityVizError
    assert utility_viz.EconVizError is utility_viz.UtilityVizError
    assert issubclass(utility_viz.ParseError, utility_viz.EconVizError)
