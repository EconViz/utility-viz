"""Tests for Config: TOML settings mapped onto Theme properties (#112)."""

import warnings
from pathlib import Path

import matplotlib
import pytest
from mosaickit import FillLayer, MarkerLayer, MathFont, PathLayer, TextFonts

from utility_viz import Canvas, Config, Figure, Layout, UtilityVizDeprecationWarning, themes
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

[utility.color]
ic = "#2E86AB"
equilibrium = "#C0392B"

[utility.stroke.budget]
width = 3.0
style = "dashed"

[utility.stroke.axis]
opacity = 0.5

[utility.marker.equilibrium]
size = 7

[utility.label.point]
fontsize = 15
position = "left"

[utility.label.origin]
visible = false

[utility.fill.budget]
color = "lightgrey"
opacity = 0.3

[utility.legend]
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
        t = Config.from_dict({"base": "nord", "utility": {"stroke": {"budget": {"width": 2.5}}}}).theme
        assert t.name == "nord" and t.ic_color == themes.nord.ic_color
        assert t.budget_stroke.width == 2.5

    @pytest.mark.parametrize(
        "data, message",
        [
            ({"colour": {}}, "unknown top-level key 'colour'; did you mean 'color'"),
            ({"base": "neon"}, "base 'neon' is not a built-in utility theme; choose from colorblind"),
            ({"utility": {"color": {"sky": "#000000"}}}, r"\[utility.color\] unknown key 'sky'"),
            ({"utility": {"color": {"ic": "#12345"}}}, r"\[utility.color\] ic must be a colour"),
            ({"utility": {"stroke": {"cloud": {"width": 1}}}}, r"\[utility.stroke.cloud\] no such setting"),
            ({"utility": {"stroke": {"budgte": {}}}}, "no such setting; did you mean 'budget'"),
            ({"utility": {"stroke": {"budget": {"thickness": 1}}}}, "fields"),
            ({"utility": {"stroke": {"budget": {"widht": 1}}}}, "unknown key 'widht'; did you mean 'width'"),
            ({"utility": {"stroke": {"budget": {"width": -1}}}}, "must be positive"),
            ({"utility": {"stroke": {"budget": {"color": "notacolour"}}}}, "color must be a colour"),
            ({"utility": {"label": {"point": {"position": "middle"}}}}, "invalid"),
            ({"utility": {"legend": {"position": "middle"}}}, r"\[utility.legend\] invalid Legend position"),
            ({"utility": {"legend": {"frame": "yes"}}}, "frame must be true or false"),
            ({"utility": {"lgend": {}}}, "unknown key 'lgend'; did you mean 'legend'"),
            ({"utility": 3}, "must be a table"),
            ({"font": {"size": 12}}, r"\[font\] unknown key 'size'"),
            ({"font": {"text": "Avenir"}}, "text must be one of sans, serif, mono"),
            ({"font": {"math": "stix"}}, "pass the path of an OpenType math font"),
            ({"font": {"math": "missing.otf"}}, "not a font file"),
            ({"fonts": {"title": ["a.ttf"]}}, r"\[fonts\] unknown key 'title'"),
            ({"fonts": {"sans": []}}, "needs at least one font file"),
            ({"fonts": {"serif": ["/no/such.ttf"]}}, "not a font file"),
            ({"fonts": 3}, "must be a table"),
            ({"legend": 3}, "must be a table"),
        ],
    )
    def test_errors_name_the_problem(self, data, message):
        with pytest.raises(InvalidParameterError, match=message), warnings.catch_warnings():
            warnings.simplefilter("ignore", UtilityVizDeprecationWarning)  # the legacy-layout rows
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
        bad.write_text("[utility.stroke.cloud]\nwidth = 1\n", encoding="utf-8")
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
        '[utility.color]\nic = "#123456"\n[principle.color]\ndemand = "#8c8c8c"\n[macro]\nx = 1\n',
        encoding="utf-8",
    )

    config = Config.load(path)

    assert config.theme.ic_color == "#123456"


LEGACY_EXAMPLE = EXAMPLE.replace("[utility.", "[")


class TestLayout:
    def test_shared_colours_set_the_theme(self):
        t = Config.from_dict({"color": {"background": "#FFFFFF", "axis": "#101010", "label": "#202020"}}).theme
        assert (t.background_color, t.axis_color, t.label_color) == ("#FFFFFF", "#101010", "#202020")

    def test_utility_colour_beats_the_shared_one(self):
        t = Config.from_dict({"color": {"axis": "#101010"}, "utility": {"color": {"axis": "#303030"}}}).theme
        assert t.axis_color == "#303030"

    def test_values_equal_to_the_default_change_nothing(self):
        data = {"utility": {"color": {"ic": themes.default.ic_color}}}
        assert Config.from_dict(data).theme == themes.default

    def test_legacy_layout_reads_the_same_with_one_warning(self, tmp_path, example):
        legacy = tmp_path / "legacy.toml"
        legacy.write_text(LEGACY_EXAMPLE, encoding="utf-8")
        with pytest.warns(UtilityVizDeprecationWarning) as caught:
            old = Config.load(legacy)
        assert len(caught) == 1
        text = str(caught[0].message)
        assert "[color] ic -> [utility.color] ic" in text and "[stroke] -> [utility.stroke]" in text
        assert "removed in 3.0" in text or "3.0" in text
        assert "init --migrate" in text
        assert caught[0].filename == __file__
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            new = Config.load(example)
        assert old.font == new.font and old.fonts == new.fonts and old.math_font == new.math_font
        for name in ("ic_color", "eq_color", "budget_stroke", "axis_stroke", "eq_marker", "point_label", "legend"):
            assert getattr(old.theme, name) == getattr(new.theme, name)

    def test_utility_key_beats_the_legacy_key(self):
        data = {
            "color": {"ic": "#111111", "budget": "#222222"},
            "stroke": {"budget": {"width": 1.0, "style": "dotted"}},
            "utility": {"color": {"ic": "#333333"}, "stroke": {"budget": {"width": 4.0}}},
        }
        with pytest.warns(UtilityVizDeprecationWarning):
            t = Config.from_dict(data).theme
        assert (t.ic_color, t.budget_color) == ("#333333", "#222222")
        assert (t.budget_stroke.width, t.budget_stroke.style) == (4.0, LineStyle.DOTTED)

    def test_other_packages_tables_are_ignored(self):
        data = {
            "principle": {"color": {"demand": "#8c8c8c"}, "stroke": {"demand": 3.5}},
            "micro": {"anything": {"nested": True}},
            "game": {"x": 1},
            "utility": {"color": {"ic": "#123456"}},
        }
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            assert Config.from_dict(data).theme.ic_color == "#123456"

    def test_errors_name_the_file_and_table(self, tmp_path):
        path = tmp_path / "econ-viz.toml"
        path.write_text("[utility.stroke.ic]\nwidth = -1\n", encoding="utf-8")
        with pytest.raises(InvalidParameterError, match=rf"^{path}: \[utility.stroke.ic\] Stroke width must be"):
            Config.load(path)

    def test_schema_is_registered_with_mosaickit(self, example):
        from mosaickit import econ_toml

        from utility_viz.core.config.settings import SCHEMA

        assert econ_toml.registered()["utility"] is SCHEMA
        assert SCHEMA.legacy_top_level
        built = econ_toml.load(example)["utility"]
        assert isinstance(built, Config) and built.theme.budget_stroke.width == 3.0

    def test_mosaickit_use_activates_utility_viz(self, example):
        from importlib.metadata import entry_points

        from mosaickit import econ_toml

        if "utility" not in {ep.name for ep in entry_points(group="econviz.config")}:  # pragma: no cover
            pytest.skip("utility-viz is not installed with its entry points")
        econ_toml.use(example)
        assert Config.active().theme.ic_color == "#2E86AB"


class TestNewTemplate:
    def test_template_uses_the_utility_tables(self):
        text = template()
        assert "# [utility.color]" in text and "# [utility.stroke.<name>]" in text and "# [utility.legend]" in text
        assert "\n[stroke" not in text and "\n[legend]" not in text

    def test_template_loads_without_warnings(self, tmp_path):
        path = tmp_path / "econ-viz.toml"
        path.write_text(template(), encoding="utf-8")
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            assert Config.load(path) == Config()

    def test_uncommented_template_values_are_the_defaults(self):
        from mosaickit import econ_toml

        from utility_viz.core.config.settings import SCHEMA

        assert any(line.startswith('# ic = "#377EB8"') for line in SCHEMA.template().splitlines())
        assert econ_toml.registered()["utility"].template() == SCHEMA.template()
