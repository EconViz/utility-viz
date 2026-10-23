"""Theme data structure for controlling diagram appearance."""

from dataclasses import dataclass

from utility_viz.core.styles.fill import Fill
from utility_viz.core.styles.label import Label
from utility_viz.core.styles.legend import Legend
from utility_viz.core.styles.marker import Marker
from utility_viz.core.styles.stroke import Stroke
from utility_viz.enums import ArrowStyle, LabelPosition, LegendPosition, LineStyle


@dataclass(frozen=True)
class Theme:
    """Colour and style specification for economic diagrams.

    Every visual element reads its default appearance from the active
    theme.  Per-call overrides are still possible via method arguments
    on :class:`~utility_viz.core.canvas.base.Canvas`.

    Parameters
    ----------
    name : str
        Human-readable theme identifier.
    axis_color : str
        Colour for axis spines, ticks, and arrow terminators.
    label_color : str
        Colour for axis labels and the origin marker.
    background_color : str, optional
        Figure/axes background. ``None`` keeps the fully transparent default
        (the previous, only, behaviour); set it for themes meant to be
        viewed against a fixed backdrop, such as a dark theme.
    label_scale : float
        Multiplier applied to the font size of every :class:`Label` property
        below that has one (``title_label`` and ``box_label`` follow
        the renderer's own default size instead, so this doesn't reach them).
    ic_color : str
        Default colour for indifference curves.
    ic_linewidth : float
        Default stroke width for indifference curves.
    secondary_ic_color : str, optional
        Colour of subdued indifference curves drawn alongside a highlighted
        focal level. ``None`` follows ``ic_color``.
    secondary_ic_linewidth : float
        Stroke width of subdued indifference curves.
    secondary_ic_opacity : float
        Opacity of subdued indifference curves.
    path_color : str
        Default colour for PCC / ICC path lines.
    path_linewidth : float
        Default stroke width for PCC / ICC path lines.
    budget_color : str
        Default colour for budget constraint lines.
    budget_linewidth : float
        Default stroke width for budget constraint lines.
    budget_fill_alpha : float
        Opacity of the feasible-set shading.
    eq_color : str
        Default colour for equilibrium markers and drop-lines.
    eq_markersize : float
        Default marker size for equilibrium points.
    ray_color : str
        Default colour for expansion-path / kink-locus rays.
    ray_linewidth : float
        Default stroke width for rays.
    kink_color : str
        Default colour for kink-point markers.
    kink_markersize : float
        Marker size of kink points.
    bliss_markersize : float
        Marker size of the bliss point of satiation preferences.
    sub_effect_color : str
        Default colour for substitution-effect arrows/labels.
    inc_effect_color : str
        Default colour for income-effect arrows/labels.
    effect_arrow_linewidth : float
        Default stroke width for decomposition arrows.
    compensated_budget_color : str
        Default colour for compensated budget lines.
    compensated_budget_linewidth : float
        Default stroke width for compensated budget lines.
    compensated_budget_linestyle : str
        Default line style for compensated budget lines.
    axis_stroke : Stroke
        Axis lines and their arrowheads. Colour ``None`` uses *axis_color*.
    drop_stroke : Stroke
        Dashed guides from an equilibrium point to the axes. Colour ``None``
        uses *eq_color*.
    projection_stroke : Stroke
        Vertical guides from decomposition bundles down to the x-axis.
    guide_stroke : Stroke
        Guides below the x-axis in decomposition diagrams.
    box_stroke : Stroke
        Frame of an Edgeworth box. Colour ``None`` uses *axis_color*.

    Default strokes
    ---------------
    Every line has a default :class:`Stroke`; a Stroke passed to a Canvas
    method only overrides the fields it sets.

    ========================== =========================================
    Line                       Default
    ========================== =========================================
    axes                       ``axis_stroke``: 0.8 pt, solid, ``-|>``
    indifference curves        ``ic_stroke``: *ic_linewidth*, solid
    budget line                ``budget_stroke``: *budget_linewidth*, solid
    rays                       ``ray_stroke``: *ray_linewidth*, dashed
    equilibrium drop lines     ``drop_stroke``: 0.8 pt, dotted
    PCC / ICC paths            ``path_stroke``: *path_linewidth*, solid
    compensated budget         ``compensated_budget_stroke``
    final budget               ``final_budget_stroke``: dashdot
    substitution / income      ``substitution_stroke`` / ``income_stroke``:
                               *effect_arrow_linewidth*, solid, ``->``
    decomposition projections  ``projection_stroke``: 0.8 pt, dotted
    guides below the x-axis    ``guide_stroke``: 0.8 pt, dashed
    Edgeworth box frame        ``box_stroke``: 1.2 pt, solid
    ========================== =========================================

    Point markers have defaults too (see :class:`Marker`): ``eq_marker``,
    ``point_marker``, ``kink_marker``, ``bliss_marker``, ``path_marker``,
    ``core_marker``, ``endowment_marker``, and ``walrasian_marker``; so do
    text labels (see :class:`Label`): ``point_label``, ``bundle_label``,
    ``bliss_label``, ``ic_label``, and ``edgeworth_label``. Auxiliary lines
    without their own colour/width fields have :class:`Stroke` defaults too:
    ``subsistence_stroke``, ``contract_stroke``, ``core_stroke``, and
    ``price_stroke``.
    """

    name: str

    # Axes & labels
    axis_color: str = "#222222"
    label_color: str = "#222222"
    background_color: str | None = None
    label_scale: float = 1.0

    # Indifference curves
    ic_color: str = "#377EB8"
    ic_linewidth: float = 1.8

    # Secondary (subdued) indifference curves, used alongside a highlighted level
    secondary_ic_color: str | None = None
    secondary_ic_linewidth: float = 1.0
    secondary_ic_opacity: float = 0.45

    # PCC / ICC paths
    path_color: str = "#4DAF4A"
    path_linewidth: float = 2.0

    # Budget constraint
    budget_color: str = "#984EA3"
    budget_linewidth: float = 1.5
    budget_fill_alpha: float = 0.08

    # Equilibrium
    eq_color: str = "#E41A1C"
    eq_markersize: float = 4.0

    # Rays
    ray_color: str = "#999999"
    ray_linewidth: float = 0.8

    # Kink markers
    kink_color: str = "#A65628"
    kink_markersize: float = 4.0

    # Bliss point of satiation preferences
    bliss_markersize: float = 12.0

    # Price decomposition visuals
    sub_effect_color: str = "#FF7F00"
    inc_effect_color: str = "#4DAF4A"
    effect_arrow_linewidth: float = 1.6
    compensated_budget_color: str = "#777777"
    compensated_budget_linewidth: float = 1.5
    compensated_budget_linestyle: str = "--"
    # Stone-Geary subsistence reference lines
    subsistence_color: str = "gray"
    subsistence_linewidth: float = 0.8

    # Edgeworth box: contract curve, core, price line, Walrasian equilibrium
    contract_color: str = "#000000"
    contract_linewidth: float = 1.2
    core_color: str = "#C0392B"
    core_linewidth: float = 3.0
    price_color: str = "#000000"
    price_linewidth: float = 1.2
    walrasian_color: str = "#2E86AB"
    walrasian_markersize: float = 10.0

    # Lines without their own width/colour fields
    axis_stroke: Stroke = Stroke(width=0.8, style=LineStyle.SOLID, arrow=ArrowStyle.TRIANGLE)
    drop_stroke: Stroke = Stroke(width=0.8, style=LineStyle.DOTTED)
    projection_stroke: Stroke = Stroke(width=0.8, style=LineStyle.DOTTED, color="#888888")
    guide_stroke: Stroke = Stroke(width=0.8, style=LineStyle.DASHED, color="#777777")
    box_stroke: Stroke = Stroke(width=1.2, style=LineStyle.SOLID)

    @property
    def eq_marker(self) -> Marker:
        """Equilibrium points, and decomposition bundles A, B, C."""
        return Marker(color=self.eq_color, size=self.eq_markersize, shape="o")

    @property
    def point_marker(self) -> Marker:
        """Points drawn with ``Canvas.add_point``."""
        return Marker(color=self.eq_color, size=self.eq_markersize, shape="o")

    @property
    def kink_marker(self) -> Marker:
        """Kink points of Leontief-type indifference curves."""
        return Marker(color=self.kink_color, size=self.kink_markersize, shape="o")

    @property
    def bliss_marker(self) -> Marker:
        """Bliss point of satiation preferences. Colour ``None`` uses the curve colour."""
        return Marker(size=self.bliss_markersize, shape="*")

    @property
    def path_marker(self) -> Marker:
        """Points on PCC / ICC paths. Colour ``None`` uses the path colour."""
        return Marker(size=max(self.eq_markersize - 1, 3), shape="o")

    @property
    def legend(self) -> Legend:
        """Legend placement and look: automatic position, no frame, 11 pt."""
        return Legend(position=LegendPosition.AUTO, fontsize=11, frame=False, visible=True)

    @property
    def budget_fill(self) -> Fill:
        """Shading of the budget set. Colour ``None`` follows the budget line."""
        return Fill(alpha=self.budget_fill_alpha)

    @property
    def axis_label(self) -> Label:
        """Axis labels at the arrow tips. Colour ``None`` uses ``label_color``."""
        return Label(offset=8, fontsize=round(14 * self.label_scale))

    @property
    def origin_label(self) -> Label:
        """The ``0`` at the origin. Colour ``None`` uses ``label_color``."""
        return Label(text="0", fontsize=round(12 * self.label_scale))

    @property
    def title_label(self) -> Label:
        """Diagram titles. Font size ``None`` keeps the renderer's title size."""
        return Label()

    @property
    def box_label(self) -> Label:
        """Edgeworth box text: good names and the O_A / O_B origins. ``None`` keeps the renderer's size."""
        return Label()

    @property
    def effect_label(self) -> Label:
        """Labels beside decomposition effect arrows. Colour ``None`` follows the effect."""
        return Label(fontsize=round(10 * self.label_scale))

    @property
    def point_label(self) -> Label:
        """Labels of equilibria and ``add_point`` points. Colour ``None`` follows the marker."""
        return Label(position=LabelPosition.TOP_RIGHT, offset=5, fontsize=round(12 * self.label_scale))

    @property
    def bundle_label(self) -> Label:
        """Labels of decomposition bundles A, B, C."""
        return Label(position=LabelPosition.TOP_RIGHT, offset=6, fontsize=round(12 * self.label_scale))

    @property
    def bliss_label(self) -> Label:
        """Label of the bliss point of satiation preferences."""
        return Label(
            text=r"\mathbf{x}^*", position=LabelPosition.TOP_RIGHT, offset=5, fontsize=round(12 * self.label_scale)
        )

    @property
    def ic_label(self) -> Label:
        """Utility-level labels at the right end of indifference curves; *text* is a format string."""
        return Label(text="{:.2g}", position=LabelPosition.RIGHT, offset=4, fontsize=round(9 * self.label_scale))

    @property
    def edgeworth_label(self) -> Label:
        """Labels of Edgeworth endowment and Walrasian equilibrium points."""
        return Label(position=LabelPosition.TOP_RIGHT, offset=5, fontsize=round(11 * self.label_scale))

    @property
    def ic_stroke(self) -> Stroke:
        return Stroke(width=self.ic_linewidth, style=LineStyle.SOLID, color=self.ic_color)

    @property
    def secondary_ic_stroke(self) -> Stroke:
        """Subdued curves drawn alongside a highlighted focal level (``Canvas.add_utility(highlight_level=...)``)."""
        return Stroke(
            width=self.secondary_ic_linewidth,
            style=LineStyle.SOLID,
            color=self.secondary_ic_color or self.ic_color,
            opacity=self.secondary_ic_opacity,
        )

    @property
    def budget_stroke(self) -> Stroke:
        return Stroke(width=self.budget_linewidth, style=LineStyle.SOLID, color=self.budget_color)

    @property
    def ray_stroke(self) -> Stroke:
        return Stroke(width=self.ray_linewidth, style=LineStyle.DASHED, color=self.ray_color)

    @property
    def path_stroke(self) -> Stroke:
        return Stroke(width=self.path_linewidth, style=LineStyle.SOLID, color=self.path_color)

    @property
    def compensated_budget_stroke(self) -> Stroke:
        return Stroke(
            width=self.compensated_budget_linewidth,
            style=self.compensated_budget_linestyle,
            color=self.compensated_budget_color,
        )

    @property
    def final_budget_stroke(self) -> Stroke:
        return Stroke(width=self.budget_linewidth, style=LineStyle.DASHDOT, color=self.budget_color)

    @property
    def substitution_stroke(self) -> Stroke:
        return Stroke(
            width=self.effect_arrow_linewidth,
            style=LineStyle.SOLID,
            color=self.sub_effect_color,
            arrow=ArrowStyle.SIMPLE,
        )

    @property
    def income_stroke(self) -> Stroke:
        return Stroke(
            width=self.effect_arrow_linewidth,
            style=LineStyle.SOLID,
            color=self.inc_effect_color,
            arrow=ArrowStyle.SIMPLE,
        )

    @property
    def subsistence_stroke(self) -> Stroke:
        """Stone-Geary subsistence reference lines."""
        return Stroke(width=self.subsistence_linewidth, style=LineStyle.DASHED, color=self.subsistence_color)

    @property
    def contract_stroke(self) -> Stroke:
        """Edgeworth contract curve."""
        return Stroke(width=self.contract_linewidth, style=LineStyle.DASHED, color=self.contract_color)

    @property
    def core_stroke(self) -> Stroke:
        """Edgeworth core segment."""
        return Stroke(width=self.core_linewidth, style=LineStyle.SOLID, color=self.core_color)

    @property
    def core_marker(self) -> Marker:
        """The core when it collapses to a single point."""
        return Marker(color=self.core_color, shape="o")

    @property
    def price_stroke(self) -> Stroke:
        """Edgeworth price line through the endowment."""
        return Stroke(width=self.price_linewidth, style=LineStyle.DASHED, color=self.price_color)

    @property
    def endowment_marker(self) -> Marker:
        """Edgeworth endowment point."""
        return Marker(color=self.eq_color, size=max(self.eq_markersize, 6.0), shape="o")

    @property
    def walrasian_marker(self) -> Marker:
        """Edgeworth Walrasian equilibrium point."""
        return Marker(color=self.walrasian_color, size=self.walrasian_markersize, shape="*")
