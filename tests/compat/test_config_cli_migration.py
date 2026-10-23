"""Config lookup order, CLI forwarder, ``init --migrate`` and packaging metadata (#132)."""

from __future__ import annotations

import dataclasses
import subprocess
import sys
import warnings
from pathlib import Path

import pytest

from utility_viz import Config, UtilityVizDeprecationWarning, themes
from utility_viz.core.config.settings import DEFAULT_FILE, LEGACY_FILE, find_config_file
from utility_viz.core.errors.deprecation import deprecation_message, warn_deprecated
from utility_viz.core.errors.exceptions import InvalidParameterError

ROOT = Path(__file__).resolve().parent.parent.parent

NEW_TOML = 'base = "nord"\n[utility.color]\nic = "#111111"\n'
OLD_TOML = 'base = "nord"\n[color]\nic = "#222222"\n'


# --- deprecation warning type ------------------------------------------------------------------------


def test_warning_is_a_futurewarning():
    assert issubclass(UtilityVizDeprecationWarning, FutureWarning)


def test_message_states_version_removal_and_replacement():
    text = deprecation_message("econ_viz.Thing", "utility_viz.Other")
    assert "econ_viz.Thing" in text
    assert "deprecated since 2.0.0" in text
    assert "removed in 3.0.0" in text
    assert "use utility_viz.Other instead" in text


def test_warn_deprecated_blames_the_caller():
    def legacy_api():
        warn_deprecated("old", "new")  # default stacklevel blames legacy_api's caller

    with pytest.warns(UtilityVizDeprecationWarning) as caught:
        legacy_api()
    assert caught[0].filename == __file__


# --- config lookup order -----------------------------------------------------------------------------


def _same(a: Config, b: Config) -> bool:
    return (dataclasses.asdict(a.theme), a.font, a.math_font) == (dataclasses.asdict(b.theme), b.font, b.math_font)


def _write(directory: Path, name: str, text: str) -> Path:
    path = directory / name
    path.write_text(text, encoding="utf-8")
    return path


def test_defaults_when_no_file(tmp_path):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert find_config_file(directory=tmp_path) is None
        assert Config.discover(directory=tmp_path) == Config()


def test_explicit_path_beats_everything(tmp_path):
    _write(tmp_path, DEFAULT_FILE, NEW_TOML)
    _write(tmp_path, LEGACY_FILE, OLD_TOML)
    explicit = _write(tmp_path, "custom.toml", 'base = "paper"\n')
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # explicit path: no lookup warnings at all
        config = Config.discover(explicit, directory=tmp_path)
    assert config.theme.ic_color == themes.paper.ic_color


def test_explicit_missing_path_errors(tmp_path):
    with pytest.raises(InvalidParameterError, match="not found"):
        Config.discover(tmp_path / "nope.toml", directory=tmp_path)


def test_new_file_is_used_silently(tmp_path):
    _write(tmp_path, DEFAULT_FILE, NEW_TOML)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        config = Config.discover(directory=tmp_path)
    assert config.theme.ic_color == "#111111"


def test_legacy_file_is_used_with_warning(tmp_path):
    _write(tmp_path, LEGACY_FILE, OLD_TOML)
    with pytest.warns(UtilityVizDeprecationWarning) as caught:
        config = Config.discover(directory=tmp_path)
    assert config.theme.ic_color == "#222222"
    text = str(caught[0].message)
    assert "utility-viz.toml" in text and "econ-viz.toml" in text
    assert "deprecated since 2.0.0" in text and "removed in 3.0.0" in text
    assert "init --migrate" in text
    assert caught[0].filename == __file__


def test_new_wins_when_both_exist_and_legacy_is_ignored_with_warning(tmp_path):
    _write(tmp_path, DEFAULT_FILE, NEW_TOML)
    _write(tmp_path, LEGACY_FILE, OLD_TOML)
    with pytest.warns(UtilityVizDeprecationWarning, match="ignored") as caught:
        config = Config.discover(directory=tmp_path)
    assert config.theme.ic_color == "#111111"
    assert "utility-viz.toml" in str(caught[0].message)


def test_load_without_path_uses_lookup_in_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(InvalidParameterError, match="config file not found: econ-viz.toml"):
        Config.load()  # 1.x semantics: no file is an error ...
    assert Config.discover() == Config()  # ... discover() falls back to defaults
    _write(tmp_path, LEGACY_FILE, OLD_TOML)
    with pytest.warns(UtilityVizDeprecationWarning):
        assert Config.load().theme.ic_color == "#222222"
    _write(tmp_path, DEFAULT_FILE, NEW_TOML)
    with pytest.warns(UtilityVizDeprecationWarning, match="ignored"):
        assert Config.load().theme.ic_color == "#111111"


def test_load_with_explicit_path_is_unchanged(tmp_path):
    path = _write(tmp_path, "x.toml", NEW_TOML)
    assert Config.load(path).theme.ic_color == "#111111"
    assert Config.load(str(path)).theme.ic_color == "#111111"


def test_section_names_unchanged_between_files(tmp_path):
    text = '[font]\ntext = "serif"\n[utility.stroke.budget]\nwidth = 2\n'
    old = Config.load(_write(tmp_path, LEGACY_FILE, text))
    new = Config.load(_write(tmp_path, DEFAULT_FILE, text))
    assert _same(old, new)


# --- CLI: utility-viz init --migrate -----------------------------------------------------------------


def _run_cli(monkeypatch, *argv):
    from utility_viz.cli.main import main

    monkeypatch.setattr(sys, "argv", ["utility-viz", *argv])
    main()


def test_init_migrate_writes_new_and_keeps_old(tmp_path, monkeypatch, capsys):
    legacy = _write(tmp_path, LEGACY_FILE, OLD_TOML)
    target = tmp_path / DEFAULT_FILE
    _run_cli(monkeypatch, "init", str(target), "--migrate")
    assert legacy.read_text(encoding="utf-8") == OLD_TOML  # old file kept untouched
    assert target.exists()
    migrated = target.read_text(encoding="utf-8")
    assert migrated.endswith('base = "nord"\n[utility.color]\nic = "#222222"\n')  # utility keys moved
    assert "Migrated from utility-viz.toml" in migrated
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # the migrated file uses the new layout
        new = Config.load(target)
    with pytest.warns(UtilityVizDeprecationWarning):
        assert _same(new, Config.load(legacy))
    assert "kept" in capsys.readouterr().out
    # After migrating, the new file wins; the leftover legacy file warns as ignored.
    with pytest.warns(UtilityVizDeprecationWarning, match="ignored"):
        Config.discover(directory=tmp_path)


def test_init_migrate_without_legacy_file_fails(tmp_path, monkeypatch, capsys):
    with pytest.raises(SystemExit) as exc:
        _run_cli(monkeypatch, "init", str(tmp_path / DEFAULT_FILE), "--migrate")
    assert exc.value.code == 1
    assert "nothing to migrate" in capsys.readouterr().err
    assert not (tmp_path / DEFAULT_FILE).exists()


def test_init_migrate_refuses_to_overwrite_without_force(tmp_path, monkeypatch):
    _write(tmp_path, LEGACY_FILE, OLD_TOML)
    _write(tmp_path, DEFAULT_FILE, NEW_TOML)
    with pytest.raises(SystemExit):
        _run_cli(monkeypatch, "init", str(tmp_path / DEFAULT_FILE), "--migrate")
    assert (tmp_path / DEFAULT_FILE).read_text(encoding="utf-8") == NEW_TOML
    _run_cli(monkeypatch, "init", str(tmp_path / DEFAULT_FILE), "--migrate", "--force")
    assert (tmp_path / DEFAULT_FILE).read_text(encoding="utf-8").endswith('[utility.color]\nic = "#222222"\n')


LEGACY_LAYOUT = """\
# my settings
base = "nord"

[font]
text = "serif"

[color]
# the indifference curves
ic = "#123456"  # blue-ish
background = "#ffffff"
budget = "#654321"

# strokes below
[stroke.ic]
width = 2.6

[legend]
position = "bottom"
"""

MIGRATED_LAYOUT = """\
# Migrated from econ-viz.toml by `utility-viz init --migrate`: utility-viz's settings now live under [utility].
# my settings
base = "nord"

[font]
text = "serif"

[color]
background = "#ffffff"

[utility.color]
# the indifference curves
ic = "#123456"  # blue-ish
budget = "#654321"

# strokes below
[utility.stroke.ic]
width = 2.6

[utility.legend]
position = "bottom"
"""


def test_init_migrate_rewrites_a_legacy_econ_viz_toml_in_place(tmp_path, monkeypatch, capsys):
    target = _write(tmp_path, DEFAULT_FILE, LEGACY_LAYOUT)
    with pytest.warns(UtilityVizDeprecationWarning):
        before = Config.load(target)
    _run_cli(monkeypatch, "init", str(target), "--migrate")
    assert target.read_text(encoding="utf-8") == MIGRATED_LAYOUT  # comments kept, keys moved
    out = capsys.readouterr().out
    assert "[stroke.ic] -> [utility.stroke.ic]" in out and "[color] ic -> [utility.color] ic" in out
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        after = Config.load(target)
    assert _same(before, after)
    # A second run has nothing left to move and leaves the file alone.
    _run_cli(monkeypatch, "init", str(target), "--migrate")
    assert "nothing to migrate" in capsys.readouterr().out
    assert target.read_text(encoding="utf-8") == MIGRATED_LAYOUT


def test_init_migrate_merges_into_an_existing_utility_colour_table(tmp_path, monkeypatch):
    target = _write(
        tmp_path, DEFAULT_FILE, '[utility.color]\nic = "#111111"\n\n[color]\naxis = "#222222"\nray = "#333333"\n'
    )
    _run_cli(monkeypatch, "init", str(target), "--migrate")
    text = target.read_text(encoding="utf-8")
    assert text.count("[utility.color]") == 1
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        theme = Config.load(target).theme
    assert (theme.ic_color, theme.ray_color, theme.axis_color) == ("#111111", "#333333", "#222222")


def test_init_migrate_moves_dotted_top_level_keys(tmp_path, monkeypatch):
    target = _write(tmp_path, DEFAULT_FILE, 'color.ic = "#111111"\ncolor.axis = "#222222"\nstroke.ic.width = 3\n')
    _run_cli(monkeypatch, "init", str(target), "--migrate")
    assert target.read_text(encoding="utf-8").endswith(
        'utility.color.ic = "#111111"\ncolor.axis = "#222222"\nutility.stroke.ic.width = 3\n'
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        theme = Config.load(target).theme
    assert (theme.ic_color, theme.axis_color, theme.ic_stroke.width) == ("#111111", "#222222", 3)


def test_init_migrate_refuses_a_result_that_is_not_valid_toml(tmp_path, monkeypatch, capsys):
    text = "[stroke.ic]\nwidth = 2\n[utility.stroke.ic]\nwidth = 3\n"  # both names for one table
    target = _write(tmp_path, DEFAULT_FILE, text)
    with pytest.raises(SystemExit):
        _run_cli(monkeypatch, "init", str(target), "--migrate")
    assert "could not migrate automatically" in capsys.readouterr().err
    assert target.read_text(encoding="utf-8") == text
    assert not list(tmp_path.glob("*.migrating"))


def test_init_migrate_rejects_invalid_toml(tmp_path, monkeypatch, capsys):
    _write(tmp_path, LEGACY_FILE, "this is = = not toml")
    with pytest.raises(SystemExit):
        _run_cli(monkeypatch, "init", str(tmp_path / DEFAULT_FILE), "--migrate")
    assert "invalid TOML" in capsys.readouterr().err
    assert not (tmp_path / DEFAULT_FILE).exists()


def test_plain_init_writes_new_default_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _run_cli(monkeypatch, "init")
    assert (tmp_path / "econ-viz.toml").exists()
    assert not (tmp_path / "utility-viz.toml").exists()


def test_utility_viz_cli_prog_and_version(monkeypatch, capsys):
    with pytest.raises(SystemExit):
        _run_cli(monkeypatch, "--version")
    assert capsys.readouterr().out.startswith("utility-viz ")


# --- CLI: legacy econ-viz forwarder ------------------------------------------------------------------


def test_legacy_cli_forwards_with_warning(monkeypatch, capsys):
    from econ_viz.cli import main

    monkeypatch.setattr(sys, "argv", ["econ-viz", "models"])
    with pytest.warns(UtilityVizDeprecationWarning) as caught:
        main()
    text = str(caught[0].message)
    assert "`econ-viz` command" in text and "`utility-viz`" in text
    assert "deprecated since 2.0.0" in text and "removed in 3.0.0" in text
    assert "CobbDouglas" in capsys.readouterr().out  # real output from the forwarded command


def test_legacy_cli_end_to_end_subprocess():
    code = "import sys; sys.argv = ['econ-viz', '--version']; from econ_viz.cli import main; main()"
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0
    assert "utility-viz" in result.stdout
    assert "UtilityVizDeprecationWarning" in result.stderr
    assert "removed in 3.0.0" in result.stderr


# --- packaging metadata ------------------------------------------------------------------------------


def _pyproject() -> dict:
    if sys.version_info >= (3, 11):
        import tomllib
    else:  # pragma: no cover
        import tomli as tomllib
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _shim_pyproject() -> dict:
    if sys.version_info >= (3, 11):
        import tomllib
    else:  # pragma: no cover
        import tomli as tomllib
    return tomllib.loads((ROOT / "packages" / "econ-viz" / "pyproject.toml").read_text(encoding="utf-8"))


def test_pyproject_uses_canonical_names():
    data = _pyproject()
    assert data["project"]["name"] == "utility-viz"
    assert data["project"]["scripts"]["utility-viz"] == "utility_viz.cli:main"
    # utility-viz ships only utility_viz: the econ_viz package and econ-viz command live in packages/econ-viz.
    assert "econ-viz" not in data["project"]["scripts"]
    assert data["tool"]["uv"]["build-backend"]["module-name"] == "utility_viz"
    assert data["tool"]["uv"]["workspace"]["members"] == ["packages/econ-viz"]


def test_animation_extra_delegates_gif_export_to_kinetickit():
    extras = _pyproject()["project"]["optional-dependencies"]
    assert extras["animation"] == ["kinetickit[raster]>=1.0.0b2,<2.0.0"]
    assert not any(item.lower().startswith("pillow") for item in extras["all"])


def test_econ_viz_distribution_is_a_lockstep_shim():
    shim, root = _shim_pyproject(), _pyproject()
    assert shim["project"]["name"] == "econ-viz"
    assert shim["project"]["scripts"]["econ-viz"] == "econ_viz.cli:main"  # 2.x forwarder
    assert shim["tool"]["uv"]["build-backend"]["module-name"] == "econ_viz"
    assert shim["project"]["version"] == root["project"]["version"]
    assert shim["project"]["dependencies"] == [f"utility-viz=={root['project']['version']}"]


def test_installed_distribution_metadata():
    from importlib.metadata import PackageNotFoundError, entry_points, version

    try:
        assert version("utility-viz")
    except PackageNotFoundError:  # pragma: no cover - not installed
        pytest.skip("utility-viz is not installed")
    scripts = {ep.name: ep.value for ep in entry_points(group="console_scripts")}
    assert scripts.get("utility-viz") == "utility_viz.cli:main"
    assert scripts.get("econ-viz") == "econ_viz.cli:main"


def test_both_import_names_are_importable():
    import econ_viz
    import utility_viz

    assert econ_viz.__name__ == "econ_viz" and utility_viz.__name__ == "utility_viz"


# --- CLI plot: automatic config lookup ---------------------------------------------------------------


def _plot(monkeypatch, tmp_path, *extra):
    out = tmp_path / "o.png"
    _run_cli(monkeypatch, "plot", "--model", "cobb-douglas", "--alpha", "0.5", "--beta", "0.5", "-o", str(out), *extra)
    return out


@pytest.fixture
def captured_theme(monkeypatch):
    seen = {}
    from utility_viz.core.canvas.base import Canvas

    original = Canvas.__init__

    def spy(self, *a, **k):
        seen["theme"] = k.get("theme")
        original(self, *a, **k)

    monkeypatch.setattr(Canvas, "__init__", spy)
    return seen


def test_plot_without_config_uses_defaults(tmp_path, monkeypatch, captured_theme):
    monkeypatch.chdir(tmp_path)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert _plot(monkeypatch, tmp_path).exists()
    assert captured_theme["theme"] is themes.default


def test_plot_picks_up_new_file_from_cwd(tmp_path, monkeypatch, captured_theme):
    monkeypatch.chdir(tmp_path)
    _write(tmp_path, DEFAULT_FILE, NEW_TOML)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _plot(monkeypatch, tmp_path)
    assert captured_theme["theme"].ic_color == "#111111"


def test_plot_picks_up_legacy_file_with_warning(tmp_path, monkeypatch, captured_theme):
    monkeypatch.chdir(tmp_path)
    _write(tmp_path, LEGACY_FILE, OLD_TOML)
    with pytest.warns(UtilityVizDeprecationWarning, match="utility-viz.toml"):
        _plot(monkeypatch, tmp_path)
    assert captured_theme["theme"].ic_color == "#222222"


def test_plot_new_wins_over_legacy_with_warning(tmp_path, monkeypatch, captured_theme):
    monkeypatch.chdir(tmp_path)
    _write(tmp_path, DEFAULT_FILE, NEW_TOML)
    _write(tmp_path, LEGACY_FILE, OLD_TOML)
    with pytest.warns(UtilityVizDeprecationWarning, match="ignored"):
        _plot(monkeypatch, tmp_path)
    assert captured_theme["theme"].ic_color == "#111111"


def test_plot_explicit_config_beats_lookup(tmp_path, monkeypatch, captured_theme):
    monkeypatch.chdir(tmp_path)
    _write(tmp_path, DEFAULT_FILE, NEW_TOML)
    explicit = _write(tmp_path, "mine.toml", 'base = "paper"\n')
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _plot(monkeypatch, tmp_path, "--config", str(explicit))
    assert captured_theme["theme"].ic_color == themes.paper.ic_color
