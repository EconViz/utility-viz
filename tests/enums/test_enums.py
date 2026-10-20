"""Tests for utility_viz.enums — ExportFormat and UtilityType."""

import pytest

from utility_viz.core.errors.exceptions import ExportError
from utility_viz.enums import ArrowStyle, ExportFormat, LabelPosition, Layout, LineStyle, UtilityType


class TestExportFormat:
    """Tests for ExportFormat.from_path() — extension inference and validation."""

    def test_from_path_png(self):
        assert ExportFormat.from_path("plot.png") is ExportFormat.PNG

    def test_from_path_pdf(self):
        assert ExportFormat.from_path("output/fig.pdf") is ExportFormat.PDF

    def test_from_path_svg(self):
        assert ExportFormat.from_path("chart.svg") is ExportFormat.SVG

    def test_from_path_tex(self):
        assert ExportFormat.from_path("diagram.tex") is ExportFormat.TEX

    def test_from_path_uppercase(self):
        assert ExportFormat.from_path("fig.PNG") is ExportFormat.PNG

    def test_from_path_unknown_raises(self):
        with pytest.raises(ExportError, match="Unsupported"):
            ExportFormat.from_path("figure.bmp")

    def test_from_path_no_extension_raises(self):
        with pytest.raises(ExportError):
            ExportFormat.from_path("noextension")


class TestUtilityType:
    """Sanity checks for the UtilityType enum members."""

    def test_members_exist(self):
        assert UtilityType.SMOOTH
        assert UtilityType.KINKED
        assert UtilityType.LINEAR

    def test_distinct(self):
        assert UtilityType.SMOOTH is not UtilityType.KINKED
        assert UtilityType.KINKED is not UtilityType.LINEAR


class TestLayout:
    def test_members_exist(self):
        assert Layout.SINGLE
        assert Layout.STACKED
        assert Layout.SIDE_BY_SIDE


class TestAxisEnums:
    def test_label_position_has_sides_and_corners(self):
        assert {member.value for member in LabelPosition} == {
            "top",
            "left",
            "bottom",
            "right",
            "top-right",
            "top-left",
            "bottom-right",
            "bottom-left",
        }

    def test_arrow_styles_accept_matplotlib_spellings(self):
        assert ArrowStyle("->") is ArrowStyle.SIMPLE
        assert ArrowStyle("-|>") is ArrowStyle.TRIANGLE
        assert ArrowStyle.FANCY.value == "fancy"
        assert ArrowStyle.WEDGE.value == "wedge"

    def test_line_and_arrow_styles_are_mosaickits(self):
        from mosaickit import ArrowStyle as MosaicArrowStyle
        from mosaickit import DashStyle

        assert LineStyle is DashStyle
        assert ArrowStyle is MosaicArrowStyle
        assert ArrowStyle.SIMPLE is ArrowStyle.OPEN

    def test_line_styles_are_matplotlib_names(self):
        assert [member.value for member in LineStyle] == ["solid", "dashed", "dotted", "dashdot"]
