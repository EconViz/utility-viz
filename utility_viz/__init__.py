"""
utility_viz — A toolkit for producing publication-quality economic diagrams.

This package provides a declarative interface for constructing standard
microeconomic visualizations (indifference curves, budget constraints, etc.)
on a configurable canvas. Figures can be exported as raster images or as
vector graphics for publication and web workflows.
"""

from __future__ import annotations

import importlib

_MODULE_EXPORTS = {
    "levels": "utility_viz.models.analysis.levels",
    "analysis": "utility_viz.models.analysis",
    "themes": "utility_viz.core.themes",
}

_ATTR_EXPORTS = {
    "Canvas": ("utility_viz.core.canvas.base", "Canvas"),
    "Figure": ("utility_viz.core.layout.figure", "Figure"),
    "Layer": ("utility_viz.models.curves.layers", "Layer"),
    "UtilityType": ("utility_viz.enums", "UtilityType"),
    "ExportFormat": ("utility_viz.enums", "ExportFormat"),
    "Layout": ("utility_viz.enums", "Layout"),
    "ArrowStyle": ("utility_viz.enums", "ArrowStyle"),
    "LabelPosition": ("utility_viz.enums", "LabelPosition"),
    "LineStyle": ("utility_viz.enums", "LineStyle"),
    "Stroke": ("utility_viz.core.styles.stroke", "Stroke"),
    "Axis": ("utility_viz.core.styles.axis", "Axis"),
    "Config": ("utility_viz.core.config.settings", "Config"),
    "Fill": ("utility_viz.core.styles.fill", "Fill"),
    "Label": ("utility_viz.core.styles.label", "Label"),
    "Legend": ("utility_viz.core.styles.legend", "Legend"),
    "Marker": ("utility_viz.core.styles.marker", "Marker"),
    "Effect": ("utility_viz.core.styles.effect", "Effect"),
    "UtilityVizError": ("utility_viz.core.errors.exceptions", "UtilityVizError"),
    "EconVizError": ("utility_viz.core.errors.exceptions", "EconVizError"),
    "UtilityVizDeprecationWarning": ("utility_viz.core.errors.deprecation", "UtilityVizDeprecationWarning"),
    "ExportError": ("utility_viz.core.errors.exceptions", "ExportError"),
    "InvalidParameterError": ("utility_viz.core.errors.exceptions", "InvalidParameterError"),
    "OptimizationError": ("utility_viz.core.errors.exceptions", "OptimizationError"),
    "ParseError": ("utility_viz.core.errors.exceptions", "ParseError"),
    "Theme": ("utility_viz.core.themes.theme", "Theme"),
    "Equilibrium": ("utility_viz.models.optimization", "Equilibrium"),
    "solve": ("utility_viz.models.optimization", "solve"),
    "solution_tex": ("utility_viz.models.optimization", "solution_tex"),
    "ComparativeStatics": ("utility_viz.models.optimization", "ComparativeStatics"),
    "DecompositionMethod": ("utility_viz.models.optimization", "DecompositionMethod"),
    "PriceEffectDecomposition": ("utility_viz.models.optimization", "PriceEffectDecomposition"),
    "comparative_statics": ("utility_viz.models.optimization", "comparative_statics"),
    "decompose_price_effect": ("utility_viz.models.optimization", "decompose_price_effect"),
    "SlutskyMatrix": ("utility_viz.models.optimization", "SlutskyMatrix"),
    "slutsky_matrix": ("utility_viz.models.optimization", "slutsky_matrix"),
    "IndifferenceCurves": ("utility_viz.core.diagrams.components", "IndifferenceCurves"),
    "BudgetConstraint": ("utility_viz.core.diagrams.components", "BudgetConstraint"),
    "EquilibriumPoint": ("utility_viz.core.diagrams.components", "EquilibriumPoint"),
    "parse_latex": ("utility_viz.models.utility", "parse_latex"),
    "CustomUtility": ("utility_viz.models.utility.advanced", "CustomUtility"),
    "MultiGoodCD": ("utility_viz.models.utility.advanced", "MultiGoodCD"),
    "ConsumptionPath": ("utility_viz.models.consumer", "ConsumptionPath"),
    "LinearBudget": ("utility_viz.models.consumer", "LinearBudget"),
    "PricePath": ("utility_viz.models.consumer", "PricePath"),
    "IncomePath": ("utility_viz.models.consumer", "IncomePath"),
    "DemandDiagram": ("utility_viz.core.diagrams.consumer", "DemandDiagram"),
    "EdgeworthBox": ("utility_viz.core.diagrams.consumer", "EdgeworthBox"),
    "EquilibriumFocusConfig": ("utility_viz.core.diagrams.consumer", "EquilibriumFocusConfig"),
    "EdgeworthState": ("utility_viz.models.consumer", "EdgeworthState"),
    "get_logger": ("utility_viz.utils.logging", "get_logger"),
}

__all__ = [
    "Canvas",
    "Layer",
    "UtilityType",
    "ExportFormat",
    "Layout",
    "ArrowStyle",
    "LabelPosition",
    "LineStyle",
    "Stroke",
    "Axis",
    "Config",
    "Fill",
    "Label",
    "Legend",
    "Marker",
    "Effect",
    "UtilityVizError",
    "EconVizError",
    "UtilityVizDeprecationWarning",
    "OptimizationError",
    "InvalidParameterError",
    "ExportError",
    "ParseError",
    "levels",
    "analysis",
    "themes",
    "Theme",
    "Equilibrium",
    "solve",
    "solution_tex",
    "ComparativeStatics",
    "DecompositionMethod",
    "PriceEffectDecomposition",
    "comparative_statics",
    "decompose_price_effect",
    "SlutskyMatrix",
    "slutsky_matrix",
    "IndifferenceCurves",
    "BudgetConstraint",
    "EquilibriumPoint",
    "parse_latex",
    "CustomUtility",
    "MultiGoodCD",
    "Figure",
    "ConsumptionPath",
    "LinearBudget",
    "PricePath",
    "IncomePath",
    "DemandDiagram",
    "EdgeworthBox",
    "EquilibriumFocusConfig",
    "EdgeworthState",
    "get_logger",
]


def __getattr__(name: str):
    if name in _MODULE_EXPORTS:
        mod = importlib.import_module(_MODULE_EXPORTS[name])
        globals()[name] = mod
        return mod
    if name in _ATTR_EXPORTS:
        module_name, attr_name = _ATTR_EXPORTS[name]
        mod = importlib.import_module(module_name)
        value = getattr(mod, attr_name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
