"""Tests for multi-panel figures, paths, and linked demand diagrams."""

import shutil
import subprocess

import numpy as np
import pytest
from bezierkit import PiecewiseBezier
from mosaickit import FillLayer, LegendLayer, MarkerLayer, PathLayer, TextLayer

from utility_viz import (
    ArrowStyle,
    Canvas,
    DemandDiagram,
    Figure,
    IncomePath,
    LabelPosition,
    Layout,
    LinearBudget,
    PricePath,
)
from utility_viz.core.errors.exceptions import InvalidParameterError
from utility_viz.models.utility import CES, CobbDouglas, Leontief, PerfectSubstitutes, QuasiLinear, StoneGeary


class TestFigure:
    @pytest.mark.parametrize(
        "layout,expected",
        [
            (Layout.SINGLE, 1),
            (Layout.SIDE_BY_SIDE, 2),
            (Layout.TOP_TWO_BOTTOM_ONE, 3),
            (Layout.TOP_ONE_BOTTOM_TWO, 3),
            (Layout.GRID_2X2, 4),
            (Layout.GRID_3X3, 9),
        ],
    )
    def test_all_required_layouts_create_expected_panel_count(self, layout, expected):
        fig = Figure(layout, x_max=12, y_max=10)
        assert len(fig) == expected

    def test_side_by_side_creates_two_canvases(self):
        fig = Figure(Layout.SIDE_BY_SIDE, x_max=12, y_max=10)
        assert len(fig) == 2
        assert isinstance(fig[0], Canvas)
        assert isinstance(fig[1], Canvas)

    def test_grid_lookup(self):
        fig = Figure(Layout.GRID_2X2)
        assert fig[1, 0] is fig[2]

    def test_save_png(self, tmp_path):
        out = tmp_path / "multi.png"
        fig = Figure(Layout.SIDE_BY_SIDE, x_max=10, y_max=10)
        fig[0].add_utility(CobbDouglas(), levels=3)
        fig[1].add_utility(CobbDouglas(alpha=0.3, beta=0.7), levels=3)
        fig.save(str(out))
        assert out.exists()

    def test_panel_canvas_uses_existing_api(self):
        fig = Figure(Layout.SIDE_BY_SIDE, x_max=20, y_max=15)
        fig[0].add_utility(CobbDouglas(), levels=3)
        fig[0].add_budget(px=2.0, py=3.0, income=30.0, fill=True)
        fig[1].add_point(2.0, 3.0, label="A")
        assert any(isinstance(layer, FillLayer) for layer in fig[0].snapshot().layers)
        assert any(isinstance(layer, PathLayer) for layer in fig[0].snapshot().layers)
        assert any(isinstance(layer, MarkerLayer) for layer in fig[1].snapshot().layers)

    def test_shared_axes_share_ranges_and_hide_duplicate_labels(self):
        fig = Figure(Layout.SIDE_BY_SIDE, shared_x=True, shared_y=True)
        assert fig[0].spec.x_range == fig[1].spec.x_range
        assert fig[0].spec.y_range == fig[1].spec.y_range
        assert "axes.y.label" in {layer.id for layer in fig[0].snapshot().layers}
        assert "axes.y.label" not in {layer.id for layer in fig[1].snapshot().layers}

    def test_axis_customization_is_forwarded_to_every_panel(self):
        fig = Figure(
            Layout.SIDE_BY_SIDE,
            x_label_pos=LabelPosition.TOP,
            y_label_pos=LabelPosition.RIGHT,
            x_arrow_style=ArrowStyle.SIMPLE,
            y_arrow_style=ArrowStyle.WEDGE,
        )

        for canvas in fig.canvases:
            assert canvas.x_label_pos is LabelPosition.TOP
            assert canvas.y_label_pos is LabelPosition.RIGHT
            assert canvas.x_arrow_style is ArrowStyle.SIMPLE
            assert canvas.y_arrow_style is ArrowStyle.WEDGE

    def test_save_tex(self, tmp_path):
        out = tmp_path / "multi.tex"
        Figure(Layout.SINGLE).save(str(out))
        assert out.exists()
        assert r"\begin{tikzpicture}" in out.read_text(encoding="utf-8")

    def test_title_is_a_scene_layer_and_tikz_preserves_layout(self, tmp_path):
        out = tmp_path / "multi.tex"
        fig = Figure(Layout.TOP_TWO_BOTTOM_ONE, title="Welfare")
        titles = [layer for canvas in fig.canvases for layer in canvas.snapshot().layers if layer.id == "figure.title"]
        assert len(titles) == 1 and isinstance(titles[0], TextLayer)
        fig.save(out)
        source = out.read_text(encoding="utf-8")
        assert source.count(r"\begin{tikzpicture}") == 3
        assert r"\begin{center}" in source
        assert r"\hspace{1em}" in source
        assert "% row 2 of 2" in source

    def test_non_default_grid_spacing_fails_instead_of_becoming_a_noop(self):
        with pytest.raises(InvalidParameterError, match="hspace/wspace"):
            Figure(Layout.SINGLE, hspace=0.5)

    def test_tikz_rejects_unknown_renderer_options(self, tmp_path):
        with pytest.raises(TypeError, match="unsupported TikZ"):
            Figure(Layout.SINGLE).save(tmp_path / "bad.tex", transparent=True)

    @pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex is not installed")
    def test_multi_panel_tikz_compiles(self, tmp_path):
        target = tmp_path / "multi.tex"
        Figure(Layout.TOP_TWO_BOTTOM_ONE, title="Welfare").save(target)
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", target.name],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, result.stdout[-2000:]
        assert (tmp_path / "multi.pdf").stat().st_size > 0


class TestConsumptionPaths:
    def test_price_path_collects_px_values(self):
        budget = LinearBudget(px=2.0, py=2.0, income=40.0)
        path = PricePath(CobbDouglas(alpha=0.5, beta=0.5), budget=budget, price="px", price_range=(1.0, 4.0), n=4)
        assert path.parameter_name == "px"
        assert path.parameter_values == pytest.approx((1.0, 2.0, 3.0, 4.0))
        assert len(path.equilibria) == 4

    def test_price_path_can_vary_py(self):
        budget = LinearBudget(px=2.0, py=2.0, income=40.0)
        path = PricePath(CobbDouglas(alpha=0.5, beta=0.5), budget=budget, price="py", price_range=(1.0, 4.0), n=4)
        assert path.parameter_name == "py"
        assert path.py_values == pytest.approx((1.0, 2.0, 3.0, 4.0))

    def test_income_path_collects_income_values(self):
        budget = LinearBudget(px=2.0, py=2.0, income=40.0)
        path = IncomePath(CobbDouglas(alpha=0.5, beta=0.5), budget=budget, income_range=(10.0, 40.0), n=4)
        assert path.parameter_name == "income"
        assert path.parameter_values == pytest.approx((10.0, 20.0, 30.0, 40.0))
        assert len(path.equilibria) == 4

    def test_cobb_douglas_price_path_matches_closed_form(self):
        budget = LinearBudget(px=2.0, py=2.0, income=40.0)
        path = PricePath(CobbDouglas(alpha=0.5, beta=0.5), budget=budget, price="px", price_range=(1.0, 4.0), n=4)
        for px, eq in zip(path.px_values, path.equilibria, strict=True):
            assert eq.x == pytest.approx(20.0 / px, rel=1e-3)

    def test_price_path_defaults_to_single_smooth_curve_without_markers(self):
        budget = LinearBudget(px=2.0, py=2.0, income=40.0)
        path = PricePath(CobbDouglas(alpha=0.5, beta=0.5), budget=budget, price="px", price_range=(1.0, 4.0), n=4)
        canvas = Canvas(x_max=25, y_max=25)
        canvas.add_path(path)
        layer = next(layer for layer in canvas.snapshot().layers if layer.id == "path")
        assert isinstance(layer, PathLayer)
        assert isinstance(layer.model, PiecewiseBezier)
        assert len(layer.path) > len(path.equilibria)
        assert not any(
            isinstance(item, MarkerLayer) and item.id.startswith("path") for item in canvas.snapshot().layers
        )

    def test_income_path_defaults_to_single_smooth_curve_without_markers(self):
        budget = LinearBudget(px=2.0, py=2.0, income=40.0)
        path = IncomePath(CobbDouglas(alpha=0.5, beta=0.5), budget=budget, income_range=(10.0, 40.0), n=4)
        canvas = Canvas(x_max=25, y_max=25)
        canvas.add_path(path)
        layer = next(layer for layer in canvas.snapshot().layers if layer.id == "path")
        assert isinstance(layer.model, PiecewiseBezier)
        assert len(layer.path) > len(path.equilibria)


class TestDemandDiagram:
    @pytest.mark.parametrize(
        "model,budget,price,price_range",
        [
            (CobbDouglas(alpha=0.5, beta=0.5), LinearBudget(px=2.0, py=2.0, income=40.0), "px", (1.0, 4.0)),
            (CES(alpha=0.5, beta=0.5, rho=0.25), LinearBudget(px=2.0, py=2.0, income=40.0), "px", (1.0, 4.0)),
            (Leontief(a=1.0, b=1.0), LinearBudget(px=2.0, py=2.0, income=40.0), "px", (1.0, 4.0)),
            (PerfectSubstitutes(a=1.0, b=2.0), LinearBudget(px=2.0, py=2.0, income=40.0), "py", (1.0, 4.0)),
            (
                StoneGeary(alpha=0.5, beta=0.5, bar_x=1.0, bar_y=1.0),
                LinearBudget(px=2.0, py=2.0, income=20.0),
                "px",
                (1.0, 4.0),
            ),
        ],
    )
    def test_save_png_common_models(self, tmp_path, model, budget, price, price_range):
        out = tmp_path / f"demand_{price}.png"
        path = PricePath(
            model,
            budget=budget,
            price=price,
            price_range=price_range,
            n=20,
        )
        fig = DemandDiagram(path)
        fig.add_marshallian_panel(price_markers=[1.5, 3.0]).save(str(out))
        assert out.exists()

    def test_selected_markers_lie_on_curve(self):
        path = PricePath(
            CobbDouglas(alpha=0.5, beta=0.5),
            budget=LinearBudget(px=2.0, py=2.0, income=40.0),
            price="px",
            price_range=(1.0, 4.0),
            n=20,
        )
        fig = DemandDiagram(path)
        fig.add_marshallian_panel(price_markers=[2.0, 4.0])
        expected_x = [10.0, 5.0]
        for px, x in zip([2.0, 4.0], expected_x, strict=True):
            assert x == pytest.approx(20.0 / px, rel=1e-3)

    @pytest.mark.parametrize(
        "price,expected",
        [
            ("px", r"p_{x}"),
            ("py", r"p_{y}"),
        ],
    )
    def test_demand_canvas_uses_math_price_symbols(self, price, expected):
        path = PricePath(
            CobbDouglas(alpha=0.5, beta=0.5),
            budget=LinearBudget(px=2.0, py=2.0, income=40.0),
            price=price,
            price_range=(1.0, 4.0),
            n=20,
        )
        fig = DemandDiagram(path)
        assert fig.demand_canvas.y_label == expected

    def test_quasi_linear_demand_example_renders(self, tmp_path):
        path = PricePath(
            QuasiLinear(v_func=np.log, linear_in="y"),
            budget=LinearBudget(px=2.0, py=1.0, income=2.0),
            price="px",
            price_range=(0.4, 5.0),
            n=20,
        )
        fig = DemandDiagram(path)
        fig.add_marshallian_panel(price_markers=[0.8, 1.8])
        fig.save(str(tmp_path / "ql.png"))
        assert (tmp_path / "ql.png").exists()

    def test_demand_panel_draws_axis_guides_for_markers(self):
        path = PricePath(
            CobbDouglas(alpha=0.5, beta=0.5),
            budget=LinearBudget(px=2.0, py=2.0, income=40.0),
            price="px",
            price_range=(1.0, 4.0),
            n=20,
        )
        fig = DemandDiagram(path)
        fig.add_marshallian_panel(price_markers=[2.0, 4.0], show_demand_guides=True)
        guides = [layer for layer in fig.demand_canvas.snapshot().layers if layer.id.startswith("demand.guide.")]
        assert len(guides) == 4
        assert all(isinstance(layer, PathLayer) for layer in guides)

    def test_selected_demand_points_are_emitted_once_and_labeled(self):
        path = PricePath(
            CobbDouglas(),
            budget=LinearBudget(px=2.0, py=2.0, income=40.0),
            price="px",
            price_range=(1.0, 4.0),
            n=20,
        )
        fig = DemandDiagram(path).add_marshallian_panel(price_markers=[2.0, 4.0])
        markers = [layer for layer in fig.demand_canvas.snapshot().layers if isinstance(layer, MarkerLayer)]
        assert [layer.id for layer in markers].count("demand.points") == 1
        assert sum(len(layer.points) for layer in markers if layer.id == "demand.points") == 2
        assert {layer.text for layer in fig.demand_canvas.snapshot().layers if layer.id.endswith(".label")} >= {
            "A",
            "B",
        }

    def test_selected_budgets_use_solid_then_dashed_styles(self):
        path = PricePath(
            CobbDouglas(),
            budget=LinearBudget(px=2.0, py=2.0, income=40.0),
            price="px",
            price_range=(1.0, 4.0),
            n=20,
        )
        fig = DemandDiagram(path).add_marshallian_panel(price_markers=[2.0, 4.0])
        budgets = [
            layer
            for layer in fig.utility_canvas.snapshot().ordered_layers
            if isinstance(layer, PathLayer) and layer.id.startswith("budget")
        ]
        assert [layer.stroke.dash.value for layer in budgets] == ["solid", "dashed"]

    def test_perfect_substitutes_demand_breaks_at_tie(self):
        path = PricePath(
            PerfectSubstitutes(a=1.0, b=1.0),
            budget=LinearBudget(px=2.0, py=2.0, income=40.0),
            price="px",
            price_range=(0.8, 5.0),
            n=21,
        )
        fig = DemandDiagram(path)
        fig.add_marshallian_panel(price_markers=[1.2, 3.0])
        layers = {layer.id: layer for layer in fig.demand_canvas.snapshot().layers}
        assert tuple(layers["demand.curve.tie"].path) == ((0.0, 2.0), (20.0, 2.0))
        assert isinstance(layers["demand.tie"], MarkerLayer)
        assert layers["demand.tie"].points == ((20.0, 2.0),)
        assert layers["demand.tie"].z_index > layers["demand.curve.tie"].z_index

    def test_demand_markers_are_not_clipped_and_draw_above_lines(self):
        path = PricePath(
            PerfectSubstitutes(a=1.0, b=1.0),
            budget=LinearBudget(px=2.0, py=2.0, income=40.0),
            price="px",
            price_range=(0.8, 5.0),
            n=21,
        )
        fig = DemandDiagram(path)
        fig.add_marshallian_panel(price_markers=[3.0])
        layers = fig.demand_canvas.snapshot().layers
        point_markers = [layer for layer in layers if isinstance(layer, MarkerLayer) and layer.id == "demand.points"]
        curves = [layer for layer in layers if isinstance(layer, PathLayer) and layer.id.startswith("demand.curve")]
        assert point_markers and curves
        assert point_markers[0].z_index > max(layer.z_index for layer in curves)

    def test_marshallian_panel_can_hide_legends(self):
        path = PricePath(
            CobbDouglas(alpha=0.5, beta=0.5),
            budget=LinearBudget(px=2.0, py=2.0, income=40.0),
            price="px",
            price_range=(1.0, 4.0),
            n=20,
        )
        fig = DemandDiagram(path)
        fig.add_marshallian_panel(price_markers=[2.0, 4.0], show_legend=False)
        assert not any(isinstance(layer, LegendLayer) for layer in fig.utility_canvas.snapshot().layers)
        assert not any(isinstance(layer, LegendLayer) for layer in fig.demand_canvas.snapshot().layers)

    def test_goods_canvas_uses_wider_padding(self):
        path = PricePath(
            CobbDouglas(alpha=0.5, beta=0.5),
            budget=LinearBudget(px=2.0, py=2.0, income=40.0),
            price="px",
            price_range=(1.0, 4.0),
            n=20,
        )
        fig = DemandDiagram(path)
        assert fig.utility_canvas.x_max == pytest.approx(40.0 * 1.18)
        assert fig.utility_canvas.y_max == pytest.approx(20.0 * 1.18)

    def test_show_pcc_uses_path_color_not_ic_color(self):
        path = PricePath(
            CobbDouglas(alpha=0.5, beta=0.5),
            budget=LinearBudget(px=2.0, py=2.0, income=40.0),
            price="px",
            price_range=(1.0, 4.0),
            n=20,
        )
        fig = DemandDiagram(path)
        fig.add_marshallian_panel(show_pcc=True)
        pcc = next(layer for layer in fig.utility_canvas.snapshot().layers if layer.id == "path")
        assert pcc.stroke.color.to_hex().lower() == fig.utility_canvas.legacy_theme.path_color.lower()
        assert fig.utility_canvas.legacy_theme.path_color != fig.utility_canvas.legacy_theme.ic_color


def test_figure_forwards_axis_line_styles():
    from utility_viz import LineStyle

    fig = Figure(Layout.SIDE_BY_SIDE, x_line_style="dashed", y_line_style=LineStyle.DOTTED)
    for panel in fig.canvases:
        assert panel.x_line_style is LineStyle.DASHED
        assert panel.y_line_style is LineStyle.DOTTED
