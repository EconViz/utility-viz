"""Theme classes that change how elements are drawn, not their colours or sizes.

Colours come from the shared theme tokens and sizes from the size presets in
:mod:`utility_viz.core.themes.roles`; these classes only pick line styles,
arrowheads, marker shapes and title sizes.
"""

from utility_viz.core.styles.label import Label
from utility_viz.core.styles.marker import Marker
from utility_viz.core.styles.stroke import Stroke
from utility_viz.core.themes.theme import Theme
from utility_viz.enums import ArrowStyle, LineStyle


class MonochromeTheme(Theme):
    """Differentiates lines by style and points by shape, not colour, for black-and-white printing."""

    @property
    def ic_stroke(self) -> Stroke:
        return Stroke(width=self.ic_linewidth, style=LineStyle.SOLID, color=self.ic_color)

    @property
    def budget_stroke(self) -> Stroke:
        return Stroke(width=self.budget_linewidth, style=LineStyle.DASHED, color=self.budget_color)

    @property
    def ray_stroke(self) -> Stroke:
        return Stroke(width=self.ray_linewidth, style=LineStyle.DOTTED, color=self.ray_color)

    @property
    def path_stroke(self) -> Stroke:
        return Stroke(width=self.path_linewidth, style=LineStyle.DASHDOT, color=self.path_color)

    @property
    def substitution_stroke(self) -> Stroke:
        return Stroke(
            width=self.effect_arrow_linewidth,
            style=LineStyle.SOLID,
            color=self.sub_effect_color,
            arrow=ArrowStyle.TRIANGLE,
        )

    @property
    def income_stroke(self) -> Stroke:
        return Stroke(
            width=self.effect_arrow_linewidth,
            style=LineStyle.DASHED,
            color=self.inc_effect_color,
            arrow=ArrowStyle.SIMPLE,
        )

    @property
    def eq_marker(self) -> Marker:
        return Marker(color=self.eq_color, size=self.eq_markersize, shape="o")

    @property
    def point_marker(self) -> Marker:
        return Marker(color=self.eq_color, size=self.eq_markersize, shape="s")

    @property
    def kink_marker(self) -> Marker:
        return Marker(color=self.kink_color, size=self.kink_markersize, shape="^")

    @property
    def path_marker(self) -> Marker:
        return Marker(size=max(self.eq_markersize - 1, 3), shape="D")

    @property
    def core_marker(self) -> Marker:
        # A plus, the accepted shape closest to Matplotlib's filled plus "P".
        return Marker(color=self.core_color, shape="+")

    @property
    def endowment_marker(self) -> Marker:
        return Marker(color=self.eq_color, size=max(self.eq_markersize, 6.0), shape="s")

    @property
    def walrasian_marker(self) -> Marker:
        return Marker(color=self.walrasian_color, size=self.walrasian_markersize, shape="D")


class PresentationTheme(Theme):
    """Larger titles and Edgeworth box text for projected slides."""

    @property
    def title_label(self) -> Label:
        return Label(fontsize=22)

    @property
    def box_label(self) -> Label:
        return Label(fontsize=16)


__all__ = ["MonochromeTheme", "PresentationTheme"]
