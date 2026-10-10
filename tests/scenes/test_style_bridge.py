from mosaickit import (
    ArrowStyle as MosaicArrowStyle,
)
from mosaickit import (
    DashStyle,
    TextStyle,
)
from mosaickit import (
    Fill as MosaicFill,
)
from mosaickit import (
    Marker as MosaicMarker,
)
from mosaickit import (
    Stroke as MosaicStroke,
)

from utility_viz import Fill, Label, Marker, Stroke
from utility_viz.core.scenes.styles import (
    to_mosaic_fill,
    to_mosaic_marker,
    to_mosaic_stroke,
    to_mosaic_text,
    to_mosaic_theme,
)
from utility_viz.core.themes import Theme
from utility_viz.enums import ArrowStyle, LineStyle


def test_stroke_conversion_preserves_every_public_field():
    converted = to_mosaic_stroke(
        Stroke(
            width=2.5,
            style=LineStyle.DASHED,
            color="#123456",
            arrow=ArrowStyle.TRIANGLE,
            opacity=0.4,
        )
    )

    assert isinstance(converted, MosaicStroke)
    assert converted.color.to_hex().upper() == "#123456"
    assert converted.width == 2.5
    assert converted.dash is DashStyle.DASHED
    assert converted.arrow is MosaicArrowStyle.TRIANGLE
    assert converted.opacity == 0.4


def test_fill_conversion_uses_normalized_opacity():
    converted = to_mosaic_fill(Fill(color="#ABCDEF", alpha=0.25))

    assert isinstance(converted, MosaicFill)
    assert converted.color.to_hex().upper() == "#ABCDEF"
    assert converted.opacity == 0.25


def test_marker_conversion_translates_diameter_to_area():
    converted = to_mosaic_marker(Marker(color="#112233", size=5, shape="s", opacity=0.75))

    assert isinstance(converted, MosaicMarker)
    assert converted.color.to_hex().upper() == "#112233"
    assert converted.size == 25
    assert converted.shape == "s"
    assert converted.opacity == 0.75


def test_label_conversion_preserves_text_style_fields():
    converted = to_mosaic_text(Label(color="#334455", fontsize=13, opacity=0.6), family="Avenir")

    assert isinstance(converted, TextStyle)
    assert converted.color.to_hex().upper() == "#334455"
    assert converted.size == 13
    assert converted.family == "Avenir"
    assert converted.opacity == 0.6


def test_theme_conversion_compiles_legacy_values_to_utility_roles():
    converted = to_mosaic_theme(
        Theme(
            name="paper",
            budget_color="#102030",
            budget_linewidth=2.25,
            eq_color="#405060",
            eq_markersize=7,
            ic_color="#708090",
        )
    )

    budget = converted.resolve("utility.budget", fallback_category="primary")
    equilibrium = converted.resolve("utility.equilibrium", fallback_category="point")
    indifference = converted.resolve("utility.indifference", fallback_category="primary")
    assert converted.name == "paper"
    assert budget.stroke.color.to_hex().upper() == "#102030"
    assert budget.stroke.width == 2.25
    assert equilibrium.marker.color.to_hex().upper() == "#405060"
    assert equilibrium.marker.size == 49
    assert indifference.stroke.color.to_hex().upper() == "#708090"
