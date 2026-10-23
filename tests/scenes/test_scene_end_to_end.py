"""Cobb-Douglas IC + budget + equilibrium built only from mosaickit layers, then rendered."""

import shutil
import subprocess

import pytest
from mosaickit import Canvas, CanvasSpec, LegendLayer, Scene, quadrant_axes

from utility_viz.core.scenes import (
    UTILITY_THEME,
    budget_layers,
    canvas_to_tikz,
    equilibrium_layers,
    indifference_layers,
)
from utility_viz.models import CobbDouglas, solve

PX, PY, INCOME = 2.0, 3.0, 30.0
X_MAX, Y_MAX = INCOME / PX * 1.2, INCOME / PY * 1.2


@pytest.fixture(scope="module")
def canvas() -> Canvas:
    func = CobbDouglas(0.5, 0.5)
    eq = solve(func, PX, PY, INCOME)
    ic, _ = indifference_layers(
        func, [eq.utility * 0.6, eq.utility, eq.utility * 1.4], X_MAX, Y_MAX, show_labels=True, legend="IC"
    )
    spec = CanvasSpec(x_range=(0, X_MAX), y_range=(0, Y_MAX), x_label="x", y_label="y", dpi=100)
    return (
        Canvas(spec, theme=UTILITY_THEME)
        .extend(quadrant_axes(X_MAX, Y_MAX))
        .extend(ic)
        .extend(budget_layers(PX, PY, INCOME, fill=True, label="I", legend="Budget"))
        .extend(equilibrium_layers(eq, ray_to=(X_MAX, Y_MAX)))
        .add(LegendLayer())
    )


def test_scene_contains_only_mosaickit_layers(canvas):
    scene = canvas.snapshot()
    assert isinstance(scene, Scene)
    roles = {layer.role for layer in scene.layers}
    assert {"utility.budget", "utility.equilibrium", "utility.indifference"} <= roles
    assert len({layer.id for layer in scene.layers}) == len(scene.layers)


def test_matplotlib_render_to_png(canvas, tmp_path):
    (png,) = canvas.save(tmp_path / "cd.png")
    assert png.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert png.stat().st_size > 5_000


def test_matplotlib_render_to_svg_uses_theme_colors(canvas, tmp_path):
    (svg,) = canvas.save(tmp_path / "cd.svg")
    text = svg.read_text(encoding="utf-8").lower()
    for color in ("#377eb8", "#984ea3", "#e41a1c"):
        assert color in text


def test_tikz_source_uses_native_bezier_and_theme_colors(canvas):
    tex = canvas_to_tikz(canvas)
    assert "\\draw[" in tex and "\\fill[" in tex and "\\node[" in tex
    assert ".. controls" in tex
    assert "377EB8" in tex and "984EA3" in tex and "E41A1C" in tex
    assert "Marshallian" not in tex


def test_utility_viz_reexports_the_mosaickit_scene_exporter():
    from mosaickit.rendering.tikz import canvas_to_tikz as mosaic_exporter

    assert canvas_to_tikz is mosaic_exporter


def test_tikz_exports_legend_text_and_generic_font(tmp_path):
    target = tmp_path / "legend.tex"
    from utility_viz import Canvas as UtilityCanvas

    UtilityCanvas(font="serif").add_budget(2, 3, 30, label="Budget").show_legend().save(target)
    source = target.read_text(encoding="utf-8")
    assert source.count("Budget") == 2  # curve label plus legend entry
    assert r"\rmfamily" in source


def test_tikz_exports_canvas_background():
    from dataclasses import replace

    from utility_viz import Canvas as UtilityCanvas
    from utility_viz import themes

    source = canvas_to_tikz(UtilityCanvas(theme=replace(themes.default, background_color="#1E1E1E")))
    assert r"\path[fill=" in source
    assert "1E1E1E" in source


def test_tikz_preserves_preformatted_math_text():
    from utility_viz import Canvas as UtilityCanvas

    source = canvas_to_tikz(UtilityCanvas(title=r"$U=\min(2x+y,\ x+3y)$"))
    assert r"{$U=\min(2x+y,\ x+3y)$};" in source
    assert r"\textbackslash" not in source


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex is not installed")
def test_tikz_compiles_with_pdflatex(canvas, tmp_path):
    tex = tmp_path / "cd.tex"
    tex.write_text(canvas_to_tikz(canvas), encoding="utf-8")
    result = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex.name],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout[-2000:]
    assert (tmp_path / "cd.pdf").stat().st_size > 0
