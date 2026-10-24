"""Per-figure label overrides: ``[figure.<stem>.label."<id>"]`` in econ-viz.toml (mosaickit 1.0.0rc7).

utility-viz does not parse ``[figure]``; mosaickit does, ``Config.use()`` activates the result and
every utility-viz save path goes through ``Canvas.save`` / ``CanvasGrid.save``, which apply it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from mosaickit import econ_toml

from utility_viz import Canvas, Config, Figure, Layout, solve
from utility_viz.cli.main import main
from utility_viz.core.errors.exceptions import InvalidParameterError
from utility_viz.models.utility import CobbDouglas

MODEL = CobbDouglas(alpha=0.4, beta=0.6)
EQ = solve(MODEL, px=2.0, py=3.0, income=60.0)

OVERRIDE = """
[figure.tangency.label."equilibrium.label"]
top = "12pt"
right = 8
"""


@pytest.fixture(autouse=True)
def _clean():
    Config.reset()
    econ_toml.clear_figure_overrides()
    yield
    Config.reset()
    econ_toml.clear_figure_overrides()


def _canvas() -> Canvas:
    return Canvas(x_max=40, y_max=25).add_utility(MODEL, levels=[10, 15]).add_budget(2, 3, 60).add_equilibrium(EQ)


def _read(path: Path) -> str:
    text = re.sub(r"<dc:date>.*?</dc:date>", "", path.read_text(encoding="utf-8"))
    return re.sub(r"\b([a-z]{1,4})[0-9a-f]{10}\b", r"\1X", text)


def _file(tmp_path: Path, text: str = OVERRIDE) -> Path:
    path = tmp_path / "econ-viz.toml"
    path.write_text(text, encoding="utf-8")
    return path


def _origin(svg: str, layer_id: str) -> tuple[float, float]:
    """Where the element with this layer id is drawn (its first translate)."""
    group = svg[svg.index(f'<g id="{layer_id}"') :]
    x, y = re.search(r"translate\(([-\d.]+) ([-\d.]+)\)", group).groups()  # type: ignore[union-attr]
    return float(x), float(y)


def _block(svg: str, layer_id: str) -> str:
    start = svg.index(f'<g id="{layer_id}"')
    return svg[start : svg.index("</g>", start)]


def _svg(drawable, path: Path) -> str:
    """The saved SVG without what changes from run to run (timestamp, generated element ids)."""
    drawable.save(path)
    text = re.sub(r"<dc:date>.*?</dc:date>", "", path.read_text(encoding="utf-8"))
    return re.sub(r"\b([a-z]{1,4})[0-9a-f]{10}\b", r"\1X", text)


def test_layer_ids_of_a_typical_figure():
    ids = [layer.id for layer in _canvas().snapshot().layers]
    assert ids == [
        "axes.x",
        "axes.y",
        "axes.x.label",
        "axes.y.label",
        "axes.origin.label",
        "utility.1",
        "utility.2",
        "budget",
        "equilibrium",
        "equilibrium.label",
        "equilibrium.drop",
    ]


class TestCanvasSave:
    def test_use_moves_the_label_of_the_matching_stem(self, tmp_path):
        plain = _svg(_canvas(), tmp_path / "tangency.svg")
        Config.load(_file(tmp_path)).use()
        moved = _svg(_canvas(), tmp_path / "tangency.svg")

        (x0, y0), (x1, y1) = _origin(plain, "equilibrium.label"), _origin(moved, "equilibrium.label")
        assert (x1 - x0, y1 - y0) == pytest.approx((8, -12), abs=0.01)  # SVG y grows downwards
        assert _origin(moved, "axes.x.label") == _origin(plain, "axes.x.label")
        # only the label moves: the marker and its drop lines are drawn as before
        assert _block(moved, "equilibrium") == _block(plain, "equilibrium")
        assert _block(moved, "equilibrium.drop") == _block(plain, "equilibrium.drop")

    def test_other_stems_and_render_are_unchanged(self, tmp_path):
        plain = _svg(_canvas(), tmp_path / "other.svg")
        Config.load(_file(tmp_path)).use()
        assert _svg(_canvas(), tmp_path / "other.svg") == plain
        assert econ_toml.figure_overrides("tangency")["equilibrium.label"].dy == 12

    def test_output_is_unchanged_without_overrides(self, tmp_path):
        plain = _svg(_canvas(), tmp_path / "tangency.svg")
        Config.load(_file(tmp_path, 'base = "default"\n')).use()
        assert _svg(_canvas(), tmp_path / "tangency.svg") == plain
        Config.reset()
        assert _svg(_canvas(), tmp_path / "tangency.svg") == plain

    def test_unknown_ids_are_ignored(self, tmp_path):
        plain = _svg(_canvas(), tmp_path / "tangency.svg")
        Config.load(_file(tmp_path, '[figure.tangency.label."nothing.here"]\ntop = 5\n')).use()
        assert _svg(_canvas(), tmp_path / "tangency.svg") == plain

    def test_an_empty_table_cancels_the_labels_own_nudge(self, tmp_path):
        Config.from_dict({"utility": {"label": {"point": {"top": 20}}}}).use()
        nudged = Canvas(x_max=40, y_max=25).add_equilibrium(EQ)
        with_nudge = _svg(nudged, tmp_path / "tangency.svg")
        Config.from_dict({"figure": {"tangency": {"label": {"equilibrium.label": {}}}}}).use()
        cancelled = _svg(Canvas(x_max=40, y_max=25).add_equilibrium(EQ), tmp_path / "tangency.svg")
        assert _origin(cancelled, "equilibrium.label")[1] > _origin(with_nudge, "equilibrium.label")[1]

    def test_png_pdf_and_tex_are_written_through_the_same_path(self, tmp_path):
        Config.load(_file(tmp_path)).use()
        for suffix in (".png", ".pdf"):
            assert _canvas().save(tmp_path / f"tangency{suffix}") == [tmp_path / f"tangency{suffix}"]
        Config.reset()
        plain = _canvas().save(tmp_path / "plain" / "tangency.tex")[0].read_text(encoding="utf-8")
        Config.load(_file(tmp_path)).use()
        moved = _canvas().save(tmp_path / "moved" / "tangency.tex")[0].read_text(encoding="utf-8")
        assert moved != plain

    def test_render_never_applies_overrides(self, tmp_path):
        Config.load(_file(tmp_path)).use()
        canvas = _canvas()
        canvas.render()  # must not raise or change the scene
        labels = {layer.id: layer for layer in canvas.snapshot().layers}
        assert getattr(labels["equilibrium.label"], "nudge", None) is None


class TestConfigActivation:
    def test_use_activates_and_reset_drops(self, tmp_path):
        config = Config.load(_file(tmp_path))
        assert econ_toml.figure_overrides() == {}  # nothing before use()
        assert set(config.figure_labels["tangency"]) == {"equilibrium.label"}
        config.use()
        assert econ_toml.figure_overrides("tangency")["equilibrium.label"].dx == 8
        Config.reset()
        assert econ_toml.figure_overrides() == {}

    def test_a_file_without_figures_replaces_earlier_overrides(self, tmp_path):
        Config.load(_file(tmp_path)).use()
        Config.load(_file(tmp_path, 'base = "default"\n')).use()
        assert econ_toml.figure_overrides() == {}

    def test_a_config_made_directly_leaves_overrides_alone(self, tmp_path):
        Config.load(_file(tmp_path)).use()
        Config().use()
        assert econ_toml.figure_overrides("tangency")

    def test_overrides_do_not_change_equality(self, tmp_path):
        assert Config.load(_file(tmp_path)) == Config.from_dict({})

    def test_reset_keeps_overrides_activated_by_someone_else(self, tmp_path):
        data = econ_toml.figure_labels({"figure": {"x": {"label": {"a": {"top": 1}}}}})
        econ_toml.activate_figure_overrides(data)
        Config.reset()
        assert econ_toml.figure_overrides("x")

    def test_malformed_values_name_the_file(self, tmp_path):
        path = _file(tmp_path, '[figure.tangency.label."equilibrium.label"]\ntop = "3em"\n')
        with pytest.raises(InvalidParameterError, match="econ-viz.toml"):
            Config.load(path)
        with pytest.raises(InvalidParameterError, match="unknown key 'up'"):
            Config.from_dict({"figure": {"a": {"label": {"b": {"up": 1}}}}})

    def test_econ_toml_use_activates_through_the_entry_point(self, tmp_path):
        econ_toml.use(_file(tmp_path))
        assert econ_toml.figure_overrides("tangency")


class TestEverySavePath:
    def test_figure_save_applies_to_every_cell(self, tmp_path):
        def figure() -> Figure:
            fig = Figure(Layout.SIDE_BY_SIDE, x_max=40, y_max=25)
            fig[0].add_budget(2, 3, 60).add_equilibrium(EQ)
            fig[1].add_budget(2, 3, 60).add_equilibrium(EQ)
            return fig

        plain = _svg(figure(), tmp_path / "tangency.svg")
        Config.load(_file(tmp_path)).use()
        moved = _svg(figure(), tmp_path / "tangency.svg")
        assert moved != plain
        assert len(re.findall(r'<g id="equilibrium.label"', moved)) == 2
        starts = [m.start() for m in re.finditer(r'<g id="equilibrium.label"', moved)]
        before = [m.start() for m in re.finditer(r'<g id="equilibrium.label"', plain)]
        for a, b in zip(starts, before, strict=True):
            ma = re.search(r"translate\(([-\d.]+) ([-\d.]+)\)", moved[a:]).groups()  # type: ignore[union-attr]
            mb = re.search(r"translate\(([-\d.]+) ([-\d.]+)\)", plain[b:]).groups()  # type: ignore[union-attr]
            assert float(ma[1]) - float(mb[1]) == pytest.approx(-12, abs=0.01)

    def test_save_figure_helper_applies(self, tmp_path):
        from utility_viz.core.export import save_figure

        plain = _svg(_canvas(), tmp_path / "tangency.svg")
        Config.load(_file(tmp_path)).use()
        save_figure(_canvas(), path=tmp_path / "tangency.svg", dpi=200)
        moved = _read(tmp_path / "tangency.svg")
        assert _origin(moved, "equilibrium.label") != _origin(plain, "equilibrium.label")

    def test_edgeworth_box_save_goes_through_the_same_path(self, tmp_path):
        from utility_viz.core.diagrams.consumer.edgeworth import EdgeworthBox

        def box() -> EdgeworthBox:
            return EdgeworthBox(CobbDouglas(), CobbDouglas(), total_x=10.0, total_y=10.0)

        path = tmp_path / "box.svg"
        plain = _svg(box(), path)
        target = "box.origin_a"
        Config.from_dict({"figure": {"box": {"label": {target: {"top": 15}}}}}).use()
        assert _origin(_svg(box(), path), target) != _origin(plain, target)

    def test_animation_frames_are_named_after_the_gif(self, tmp_path):
        from utility_viz.core.animation import Animator

        def frames(stem: str) -> list[bytes]:
            return list(Animator(lambda v: _canvas(), frames=[1.0])._render_frames(dpi=60, stem=stem))

        plain = frames("tangency")
        Config.load(_file(tmp_path)).use()
        assert frames("tangency") != plain
        assert frames("another") == plain

    def test_gif_save_passes_its_stem(self, tmp_path, monkeypatch):
        from utility_viz.core.animation import Animator, animator

        seen: dict[str, object] = {}

        def fake_export(frames, target, **kwargs):
            seen["frames"] = list(frames)

        monkeypatch.setattr(animator, "_require_kinetickit", lambda: fake_export)
        plain_gif = tmp_path / "tangency.gif"
        Animator(lambda v: _canvas(), frames=[1.0]).save(plain_gif, dpi=60)
        plain = seen["frames"]
        Config.load(_file(tmp_path)).use()
        Animator(lambda v: _canvas(), frames=[1.0]).save(plain_gif, dpi=60)
        assert seen["frames"] != plain

    def test_cli_plot_with_config_applies_and_cleans_up(self, tmp_path, monkeypatch):
        args = ["plot", "--model", "cobb-douglas", "--px", "2", "--py", "3", "--income", "60", "--x-max", "40"]
        args += ["--y-max", "25"]

        def run(config: Path | None, output: Path) -> str:
            argv = ["utility-viz", *args, "--output", str(output)]
            if config is not None:
                argv += ["--config", str(config)]
            monkeypatch.setattr("sys.argv", argv)
            main()
            return _read(output)

        plain = run(None, tmp_path / "tangency.svg")
        moved = run(_file(tmp_path), tmp_path / "tangency.svg")
        assert _origin(moved, "equilibrium.label") != _origin(plain, "equilibrium.label")
        assert econ_toml.figure_overrides() == {}
        assert run(_file(tmp_path), tmp_path / "unmatched.svg") == plain
