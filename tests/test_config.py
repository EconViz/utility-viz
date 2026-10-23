"""Tests for Config: TOML settings mapped onto Theme properties (#112)."""

from pathlib import Path

import matplotlib
import pytest
from mosaickit import FillLayer, MarkerLayer, MathFont, PathLayer, TextFonts

from utility_viz import Canvas, Config, Figure, Layout, themes
from utility_viz.core.config.settings import template
from utility_viz.core.diagrams.consumer.edgeworth import EdgeworthBox
from utility_viz.core.errors.exceptions import InvalidParameterError
from utility_viz.enums import LabelPosition, LegendPosition, LineStyle
from utility_viz.models.utility import CobbDouglas

FONT_DIR = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
MATH_FILE = FONT_DIR / "DejaVuSerif.ttf"  # has an OpenType MATH table

EXAMPLE = f"""
base = "default"

[font]
text = "serif"
math = "{MATH_FILE}"

[fonts]
mono = ["{FONT_DIR / "DejaVuSansMono.ttf"}", "{FONT_DIR / "DejaVuSansMono-Bold.ttf"}"]

[color]
ic = "#2E86AB"
equilibrium = "#C0392B"

[stroke.budget]
width = 3.0
style = "dashed"

[stroke.axis]
opacity = 0.5

[marker.equilibrium]
size = 7

[label.point]
fontsize = 15
position = "left"

[label.origin]
visible = false

[fill.budget]
color = "lightgrey"
opacity = 0.3

[legend]
position = "bottom"
"""


@pytest.fixture(autouse=True)
def reset_config():
    yield
    Config.reset()


@pytest.fixture
def example(tmp_path):
    path = tmp_path / "econ-viz.toml"
    path.write_text(EXAMPLE, encoding="utf-8")
    return path


class TestLoad:
    def test_sections_map_to_theme(self, example):
        config = Config.load(example)
        t = config.theme
        assert (t.ic_color, t.eq_color) == ("#2E86AB", "#C0392B")
        assert (t.budget_stroke.width, t.budget_stroke.style) == (3.0, LineStyle.DASHED)
        assert t.budget_stroke.color == t.budget_color  # unset fields keep the default
        assert t.axis_stroke.opacity == 0.5 and t.axis_stroke.width == themes.default.axis_stroke.width
        assert t.eq_marker.size == 7 and t.eq_marker.color == "#C0392B"
        assert (t.point_label.fontsize, t.point_label.position) == (15, LabelPosition.LEFT)
        assert t.point_label.offset == themes.default.point_label.offset
        assert t.origin_label.visible is False
        assert (t.budget_fill.color, t.budget_fill.opacity) == ("lightgrey", 0.3)
        assert t.legend.position is LegendPosition.BOTTOM
        assert config.font == "serif"
        assert config.math_font == MathFont(MATH_FILE)
        assert config.fonts == TextFonts(mono=(FONT_DIR / "DejaVuSansMono.ttf", FONT_DIR / "DejaVuSansMono-Bold.ttf"))

    def test_untouched_settings_stay_default(self, example):
        t = Config.load(example).theme
        assert t.path_stroke == themes.default.path_stroke
        assert t.ic_label == themes.default.ic_label

    def test_empty_config_is_the_default_theme(self):
        assert Config.from_dict({}).theme is themes.default

    def test_base_theme(self):
        t = Config.from_dict({"base": "nord", "stroke": {"budget": {"width": 2.5}}}).theme
        assert t.name == "nord" and t.ic_color == themes.nord.ic_color
        assert t.budget_stroke.width == 2.5

    @pytest.mark.parametrize(
        "data, message",
        [
            ({"colour": {}}, "unknown section"),
            ({"base": "neon"}, "unknown base theme"),
            ({"color": {"sky": "#000000"}}, "no such colour"),
            ({"stroke": {"cloud": {"width": 1}}}, "no such setting"),
            ({"stroke": {"budget": {"thickness": 1}}}, "fields"),
            ({"stroke": {"budget": {"width": -1}}}, "must be positive"),
            ({"label": {"point": {"position": "middle"}}}, "invalid"),
            ({"font": {"size": 12}}, "text and math"),
            ({"font": {"text": "Avenir"}}, "font must be one of sans, serif, mono"),
            ({"font": {"math": "stix"}}, "pass the path of an OpenType math font"),
            ({"font": {"math": "missing.otf"}}, "not a font file"),
            ({"fonts": {"title": ["a.ttf"]}}, "sans, serif and mono"),
            ({"fonts": {"sans": []}}, "non-empty list"),
            ({"fonts": {"serif": ["/no/such.ttf"]}}, "not a font file"),
            ({"fonts": 3}, "must be a table"),
            ({"legend": 3}, "must be a table"),
        ],
    )
    def test_errors_name_the_problem(self, data, message):
        with pytest.raises(InvalidParameterError, match=message):
            Config.from_dict(data)

    def test_missing_and_invalid_files(self, tmp_path):
        with pytest.raises(InvalidParameterError, match="not found"):
            Config.load(tmp_path / "nope.toml")
        bad = tmp_path / "bad.toml"
        bad.write_text("[stroke\n", encoding="utf-8")
        with pytest.raises(InvalidParameterError, match="invalid TOML"):
            Config.load(bad)


class TestUse:
    def test_use_sets_the_default_for_new_diagrams(self, example):
        Config.load(example).use()
        cvs = Canvas().add_budget(2, 3, 30)
        budget = next(a for a in cvs.snapshot().ordered_layers if isinstance(a, PathLayer) and a.id == "budget")
        assert budget.stroke.width == 3.0
        assert cvs.math_font == MathFont(MATH_FILE) and cvs.font == "serif"
        assert cvs.fonts == Config.active().fonts
        assert not any(a.id == "axes.origin.label" for a in cvs.snapshot().ordered_layers)

    def test_config_markers_and_strokes_are_drawn(self, example):
        from utility_viz import solve

        Config.load(example).use()
        eq = solve(CobbDouglas(), px=2.0, py=3.0, income=30.0)
        cvs = Canvas(x_max=20, y_max=15).add_equilibrium(eq)
        point = next(a for a in cvs.snapshot().ordered_layers if isinstance(a, MarkerLayer))
        assert point.marker.size == 7**2

    def test_explicit_stroke_beats_config(self, example):
        from utility_viz import Stroke

        Config.load(example).use()
        cvs = Canvas().add_budget(2, 3, 30, stroke=Stroke(width=1.0))
        budget = next(a for a in cvs.snapshot().ordered_layers if isinstance(a, PathLayer) and a.id == "budget")
        assert budget.stroke.width == 1.0
        assert budget.stroke.dash.value == "dashed"  # style still from the config

    def test_explicit_theme_wins(self, example):
        Config.load(example).use()
        assert Canvas(theme=themes.nord).legacy_theme is themes.nord

    def test_reset(self, example):
        Config.load(example).use()
        Config.reset()
        assert Canvas().legacy_theme is themes.default
        assert Config.active().theme is themes.default

    def test_figure_and_edgeworth_follow_the_config(self, example):
        Config.load(example).use()
        fig = Figure(Layout.SIDE_BY_SIDE)
        assert all(cvs.legacy_theme.ic_color == "#2E86AB" for cvs in fig.canvases)
        box = EdgeworthBox(CobbDouglas(), CobbDouglas(), total_x=10.0, total_y=10.0)
        assert box.legacy_theme.ic_color == "#2E86AB"

    def test_theme_alone(self, example):
        cvs = Canvas(x_max=20, y_max=15, theme=Config.load(example).theme).add_budget(2, 3, 30, fill=True)
        fill = next(a for a in cvs.snapshot().ordered_layers if isinstance(a, FillLayer))
        assert fill.fill.color.to_hex() == "#D3D3D3"
        assert Config.active().theme is themes.default


class TestTemplate:
    def test_template_loads_and_changes_nothing(self, tmp_path):
        path = tmp_path / "econ-viz.toml"
        path.write_text(template(), encoding="utf-8")
        t = Config.load(path).theme
        for name in ("budget_stroke", "eq_marker", "point_label", "budget_fill", "legend"):
            assert getattr(t, name) == getattr(themes.default, name)

    def test_template_lists_setting_names(self):
        text = template()
        assert "compensated_budget" in text and "origin" in text and "edgeworth" in text


class TestCli:
    def _run(self, monkeypatch, *argv):
        from utility_viz.cli.main import main

        monkeypatch.setattr("sys.argv", ["utility-viz", *argv])
        main()

    def test_init_writes_and_refuses_to_overwrite(self, tmp_path, monkeypatch, capsys):
        path = tmp_path / "econ-viz.toml"
        self._run(monkeypatch, "init", str(path))
        assert path.read_text(encoding="utf-8") == template()
        with pytest.raises(SystemExit):
            self._run(monkeypatch, "init", str(path))
        assert "already exists" in capsys.readouterr().err
        self._run(monkeypatch, "init", str(path), "--force")

    def test_plot_with_config(self, tmp_path, monkeypatch, example):
        out = tmp_path / "plot.png"
        self._run(
            monkeypatch,
            "plot",
            "--model",
            "cobb-douglas",
            "--px",
            "2",
            "--py",
            "3",
            "--income",
            "30",
            "--x-max",
            "20",
            "--y-max",
            "15",
            "--config",
            str(example),
            "--output",
            str(out),
        )
        assert out.exists() and out.stat().st_size > 0

    def test_plot_with_bad_config(self, tmp_path, monkeypatch, capsys):
        bad = tmp_path / "bad.toml"
        bad.write_text("[stroke.cloud]\nwidth = 1\n", encoding="utf-8")
        with pytest.raises(SystemExit):
            self._run(
                monkeypatch,
                "plot",
                "--model",
                "cobb-douglas",
                "--config",
                str(bad),
                "--output",
                str(tmp_path / "x.png"),
            )
        assert "no such setting" in capsys.readouterr().err


class TestFontPaths:
    def test_relative_font_paths_follow_the_config_file(self, tmp_path):
        (tmp_path / "fonts").mkdir()
        (tmp_path / "fonts" / "serif.ttf").write_bytes((FONT_DIR / "DejaVuSerif.ttf").read_bytes())
        (tmp_path / "fonts" / "math.ttf").write_bytes(MATH_FILE.read_bytes())
        path = tmp_path / "econ-viz.toml"
        path.write_text('[font]\nmath = "fonts/math.ttf"\n[fonts]\nserif = "fonts/serif.ttf"\n', encoding="utf-8")
        config = Config.load(path)
        assert config.fonts == TextFonts(serif=tmp_path / "fonts" / "serif.ttf")
        assert config.math_font == MathFont(tmp_path / "fonts" / "math.ttf")

    def test_the_template_documents_the_generic_fonts(self):
        text = template()
        assert 'text = "serif"' in text and "[fonts]" in text and "math = " in text


def test_other_packages_tables_are_skipped(tmp_path):
    from utility_viz.core.config.settings import Config

    path = tmp_path / "econ-viz.toml"
    path.write_text(
        '[color]\nic = "#123456"\n[principle.color]\ndemand = "#8c8c8c"\n[macro]\nx = 1\n',
        encoding="utf-8",
    )

    config = Config.load(path)

    assert config.theme.ic_color == "#123456"
