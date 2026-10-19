"""Marker values are preserved in MosaicKit marker layers and exports."""

import shutil
import subprocess

import pytest
from mosaickit import MarkerLayer

from utility_viz import Canvas, Marker, solve
from utility_viz.core.diagrams.consumer.edgeworth import EdgeworthBox
from utility_viz.core.errors.exceptions import InvalidParameterError
from utility_viz.models.optimization import decompose_price_effect
from utility_viz.models.utility import CobbDouglas, Leontief, Satiation

MODEL = CobbDouglas(0.5, 0.5)
EQ = solve(MODEL, px=2, py=3, income=30)
SQUARE = Marker(color="#123456", size=9, shape="s", opacity=0.6)


def _marker(canvas, suffix: str) -> MarkerLayer:
    return next(
        layer
        for layer in canvas.snapshot().ordered_layers
        if isinstance(layer, MarkerLayer) and layer.id.endswith(suffix)
    )


def _assert_marker(layer: MarkerLayer, marker: Marker):
    assert layer.marker is not None
    assert layer.marker.color is not None and not isinstance(layer.marker.color, str)
    assert layer.marker.shape == marker.shape
    assert layer.marker.size == pytest.approx(marker.size**2)
    assert layer.marker.opacity == marker.opacity
    assert layer.marker.color.to_hex() == marker.color


def test_marker_value_validation_and_merge():
    assert (Marker().color, Marker().size, Marker().shape) == (None, None, None)
    for kwargs in ({"size": 0}, {"size": -2}, {"shape": "not-a-marker"}):
        with pytest.raises(InvalidParameterError):
            Marker(**kwargs)
    assert Marker(size=3).merged_over(Marker(color="red", size=9, shape="s")) == Marker(color="red", size=3, shape="s")


def test_point_equilibrium_and_decomposition_markers():
    canvas = Canvas(x_max=20, y_max=15).add_point(2, 2, marker=SQUARE).add_equilibrium(EQ, marker=SQUARE)
    _assert_marker(_marker(canvas, "point"), SQUARE)
    _assert_marker(_marker(canvas, "equilibrium"), SQUARE)
    dec = decompose_price_effect(MODEL, px=(2, 4), py=3, income=30)
    bundles = _marker(Canvas(x_max=20, y_max=15).add_decomposition(dec, point_marker=SQUARE), "bundles")
    assert len(bundles.points) == 3
    _assert_marker(bundles, SQUARE)


def test_kink_and_bliss_markers():
    kink = _marker(Canvas().add_utility(Leontief(1, 2), levels=[2, 4], show_kinks=True, kink_marker=SQUARE), "kinks")
    assert len(kink.points) == 2
    _assert_marker(kink, SQUARE)
    bliss = _marker(Canvas(x_max=12, y_max=10).add_utility(Satiation(6, 4), levels=[-8], bliss_marker=SQUARE), "bliss")
    _assert_marker(bliss, SQUARE)


def test_edgeworth_keeps_marker_shapes():
    box = EdgeworthBox(MODEL, MODEL, total_x=10, total_y=10).add_endowment(7, 3, marker=SQUARE)
    _assert_marker(_marker(box, "endowment"), SQUARE)
    box.add_walrasian_equilibrium(px=1, py=1, marker="D")
    assert _marker(box, "walrasian").marker.shape == "D"


def test_marker_shape_reaches_tikz(tmp_path):
    circle = tmp_path / "circle.tex"
    square = tmp_path / "square.tex"
    Canvas().add_point(5, 5, marker=Marker(shape="o")).save(circle)
    Canvas().add_point(5, 5, marker=Marker(shape="s")).save(square)
    assert " circle " in circle.read_text(encoding="utf-8")
    assert " rectangle " in square.read_text(encoding="utf-8")


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex is not installed")
def test_all_marker_shapes_compile_in_tikz(tmp_path):
    output = tmp_path / "markers.tex"
    canvas = Canvas(x_max=20, y_max=10)
    for index, shape in enumerate(
        ("o", "s", "^", "v", "<", ">", "D", "d", "*", "+", "x", ".", ",", "p", "h", "H", "|", "_"), 1
    ):
        canvas.add_point(index, 5, marker=Marker(shape=shape))
    canvas.save(output)

    result = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", output.name],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stdout[-2000:]


def test_marker_is_exported():
    import utility_viz

    assert utility_viz.Marker is Marker
