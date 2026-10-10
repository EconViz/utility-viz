"""Backend-neutral scene factories (mosaickit layers) for the economic components.

Each factory turns a solved/derived economic object into immutable mosaickit layers with
concept-local roles (``utility.budget``, ``utility.equilibrium``, ``utility.indifference``).
Nothing here imports Matplotlib or the legacy drawing modules; rendering is done by
mosaickit (``Canvas.save``) with :data:`UTILITY_THEME`, or export TikZ with
:func:`canvas_to_tikz` (curves are native Bezier paths from bezierkit).
"""

from utility_viz.core.scenes.budget import budget_layers
from utility_viz.core.scenes.decomposition import decomposition_layers
from utility_viz.core.scenes.equilibrium import equilibrium_layers
from utility_viz.core.scenes.indifference import indifference_layers
from utility_viz.core.scenes.roles import Budget, Equilibrium, Indifference
from utility_viz.core.scenes.styles import (
    to_mosaic_fill,
    to_mosaic_marker,
    to_mosaic_stroke,
    to_mosaic_text,
    to_mosaic_theme,
)
from utility_viz.core.scenes.theme import (
    UTILITY_THEME,
    UtilityColors,
    register_utility_theme,
    utility_roles,
    utility_theme,
)
from utility_viz.core.scenes.tikz import canvas_to_tikz

__all__ = [
    "UTILITY_THEME",
    "Budget",
    "Equilibrium",
    "Indifference",
    "UtilityColors",
    "budget_layers",
    "decomposition_layers",
    "canvas_to_tikz",
    "equilibrium_layers",
    "indifference_layers",
    "register_utility_theme",
    "to_mosaic_fill",
    "to_mosaic_marker",
    "to_mosaic_stroke",
    "to_mosaic_text",
    "to_mosaic_theme",
    "utility_roles",
    "utility_theme",
]
