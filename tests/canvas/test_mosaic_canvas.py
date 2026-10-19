from pathlib import Path

from mosaickit import Canvas as MosaicCanvas
from mosaickit import FillLayer, LegendLayer, MarkerLayer, PathLayer, TextLayer

from utility_viz import Canvas, Fill, Label, Marker, Stroke
from utility_viz.models.optimization import solve
from utility_viz.models.utility import CobbDouglas


def _layers(canvas: Canvas):
    return canvas.snapshot().layers


def test_public_canvas_is_a_backend_neutral_mosaickit_canvas():
    canvas = Canvas(x_max=12, y_max=8, x_label="Good X", y_label="Good Y")

    assert isinstance(canvas, MosaicCanvas)
    assert canvas.spec.x_range == (0.0, 12.0)
    assert canvas.spec.y_range == (0.0, 8.0)
    assert not hasattr(canvas, "ax")
    assert not hasattr(canvas, "fig")
    assert {layer.id for layer in _layers(canvas)} >= {
        "axes.x",
        "axes.y",
        "axes.x.label",
        "axes.y.label",
        "axes.origin.label",
    }


def test_basic_fluent_operations_only_add_mosaickit_layers():
    model = CobbDouglas()
    equilibrium = solve(model, px=2, py=3, income=30)
    canvas = Canvas(x_max=20, y_max=20)

    result = (
        canvas.add_utility(model, levels=[1.0, equilibrium.utility])
        .add_budget(
            2,
            3,
            30,
            fill=Fill(color="#ffeeaa", opacity=0.2),
            stroke=Stroke(color="#112233", width=2),
            label="Budget",
        )
        .add_equilibrium(
            equilibrium,
            marker=Marker(color="#ff0000", size=6),
            label=Label(text="x^*", color="#ff0000"),
        )
        .add_point(2, 4, label="A")
        .add_ray(1.5)
        .show_legend()
    )

    assert result is canvas
    layers = _layers(canvas)
    assert any(isinstance(layer, FillLayer) for layer in layers)
    assert any(isinstance(layer, MarkerLayer) for layer in layers)
    assert any(isinstance(layer, TextLayer) and layer.text == "A" for layer in layers)
    assert any(isinstance(layer, PathLayer) and layer.legend == "Budget" for layer in layers)
    assert isinstance(layers[-1], LegendLayer)


def test_public_canvas_saves_png_from_the_scene(tmp_path: Path):
    target = tmp_path / "utility.png"

    result = Canvas().add_budget(1, 1, 8).save(target)

    assert result == [target]
    assert target.read_bytes().startswith(b"\x89PNG")
