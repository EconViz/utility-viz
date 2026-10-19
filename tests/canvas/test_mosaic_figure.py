from mosaickit import CanvasGrid

from utility_viz import Canvas, Figure, Layout


def test_figure_is_a_canvas_grid_composition_without_renderer_state():
    figure = Figure(Layout.TOP_TWO_BOTTOM_ONE, x_max=12, y_max=8)

    assert len(figure) == 3
    assert all(isinstance(canvas, Canvas) for canvas in figure.canvases)
    assert isinstance(figure.grid, CanvasGrid)
    assert not hasattr(figure, "fig")
    assert not hasattr(figure, "ax")
    assert (figure.grid.rows, figure.grid.cols) == (2, 2)


def test_figure_saves_grid_through_mosaickit(tmp_path):
    target = tmp_path / "grid.png"
    figure = Figure(Layout.SIDE_BY_SIDE)
    figure[0].add_budget(1, 1, 8)
    figure[1].add_point(2, 3, label="A")

    result = figure.save(target)

    assert result == [target]
    assert target.read_bytes().startswith(b"\x89PNG")
