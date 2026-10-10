"""WidgetViewer — ipywidgets-based interactive slider viewer."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from utility_viz.core.canvas.base import Canvas
    from utility_viz.core.layout.figure import Figure

    AnyFigure = Canvas | Figure

# Slider spec: (min, max, step)
SliderSpec = tuple[float, float, float]


def _require_widgets() -> None:
    """Raise a helpful ImportError when ipywidgets / IPython are absent."""
    missing = []
    try:
        import ipywidgets  # noqa: F401
    except ImportError:
        missing.append("ipywidgets")
    try:
        import IPython  # noqa: F401
    except ImportError:
        missing.append("IPython")

    if missing:
        pkg_list = " ".join(missing)
        raise ImportError(
            f"Interactive widgets require: {pkg_list}\n"
            "Install them with:  pip install utility-viz[interactive]\n"
            "                or:  pip install ipywidgets"
        )


class WidgetViewer:
    """Render an utility_viz diagram inside a Jupyter notebook with live sliders.

    Pass a drawing function and a slider specification for each parameter.
    Every parameter gets both a slider and a numeric input box.
    When a control is changed the old figure is cleared
    (``clear_output(wait=True)``) and the diagram is redrawn immediately,
    so the notebook cell never accumulates a stack of repeated images.

    Parameters
    ----------
    draw_func : Callable[..., Canvas | Figure]
        A function whose keyword-argument names match the keys in
        *slider_specs* and that returns a fully populated Canvas or Figure.
    **slider_specs : tuple[float, float, float]
        One ``(min, max, step)`` triple per parameter.  Every key must
        correspond to a keyword argument accepted by *draw_func*.

    Examples
    --------
    .. code-block:: python

        from utility_viz.core.interactive import WidgetViewer
        from utility_viz import Canvas
        from utility_viz.models.utility import CobbDouglas

        def draw(p1: float, income: float) -> Canvas:
            c = Canvas(x_max=10, y_max=10, x_label="X_1", y_label="X_2")
            c.add_budget(px=p1, py=2.0, income=income)
            c.add_utility(CobbDouglas(0.5, 0.5), levels=5)
            return c

        WidgetViewer(draw, p1=(1.0, 8.0, 0.5), income=(10.0, 40.0, 5.0)).show()
    """

    def __init__(
        self,
        draw_func: Callable[..., AnyFigure],
        **slider_specs: SliderSpec,
    ) -> None:
        if not slider_specs:
            raise ValueError("Provide at least one slider spec, e.g. p1=(1.0, 8.0, 0.5).")
        self._draw_func = draw_func
        self._slider_specs: dict[str, SliderSpec] = slider_specs
        self._links: list[Any] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show(self) -> None:
        """Render the widget panel in the active Jupyter output cell.

        Raises
        ------
        ImportError
            If ``ipywidgets`` or ``IPython`` are not installed.
        RuntimeError
            If called outside of a Jupyter / IPython environment.
        """
        _require_widgets()

        import ipywidgets as widgets
        from IPython.display import Image, clear_output, display

        sliders = self._build_sliders(widgets)
        value_inputs = self._build_value_inputs(widgets, sliders)
        out = widgets.Output()

        # Draw the initial frame before any slider interaction.
        self._redraw(
            out=out,
            values={name: s.value for name, s in sliders.items()},
            clear_output=clear_output,
            display=display,
            image_type=Image,
        )

        # Wire each slider to the redraw callback.
        def _on_change(_change: Any) -> None:
            self._redraw(
                out=out,
                values={name: s.value for name, s in sliders.items()},
                clear_output=clear_output,
                display=display,
                image_type=Image,
            )

        for slider in sliders.values():
            slider.observe(_on_change, names="value")

        # Lay out: per-parameter controls on top, diagram output below.
        self._links = self._link_value_inputs(widgets, sliders, value_inputs)
        slider_box = widgets.VBox(
            self._build_control_rows(widgets, sliders, value_inputs),
            layout=widgets.Layout(margin="0 0 12px 0"),
        )
        display(widgets.VBox([slider_box, out]))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_sliders(self, widgets) -> dict[str, Any]:
        """Construct a FloatSlider for every slider spec."""
        sliders: dict[str, Any] = {}
        for name, (lo, hi, step) in self._slider_specs.items():
            mid = lo + (hi - lo) / 2
            # Snap mid to the nearest step boundary.
            mid = round(round((mid - lo) / step) * step + lo, 10)
            sliders[name] = widgets.FloatSlider(
                value=mid,
                min=lo,
                max=hi,
                step=step,
                description=f"{name}:",
                continuous_update=False,
                style={"description_width": "initial"},
                layout=widgets.Layout(width="400px"),
            )
        return sliders

    @staticmethod
    def _build_value_inputs(widgets, sliders: dict[str, Any]) -> dict[str, Any]:
        """Construct a FloatText box for every slider."""
        inputs: dict[str, Any] = {}
        for name, slider in sliders.items():
            inputs[name] = widgets.FloatText(
                value=slider.value,
                description="",
                step=slider.step,
                layout=widgets.Layout(width="110px"),
            )
        return inputs

    @staticmethod
    def _link_value_inputs(
        widgets,
        sliders: dict[str, Any],
        value_inputs: dict[str, Any],
    ) -> list[Any]:
        """Two-way link each slider with its numeric input box."""
        return [widgets.link((sliders[name], "value"), (value_inputs[name], "value")) for name in sliders]

    @staticmethod
    def _build_control_rows(
        widgets,
        sliders: dict[str, Any],
        value_inputs: dict[str, Any],
    ) -> list[Any]:
        """Combine each slider with its numeric input box."""
        return [
            widgets.HBox(
                [sliders[name], value_inputs[name]],
                layout=widgets.Layout(align_items="center"),
            )
            for name in sliders
        ]

    def _redraw(
        self,
        out,
        values: dict[str, float],
        clear_output: Callable,
        display: Callable,
        image_type: type,
    ) -> None:
        """Clear the output widget and render a fresh diagram."""
        with out:
            clear_output(wait=True)
            canvas_or_fig = self._draw_func(**values)
            with TemporaryDirectory(prefix="utility-viz-widget-") as directory:
                target = Path(directory) / "frame.png"
                canvas_or_fig.save(target, transparent=False)
                display(image_type(data=target.read_bytes(), format="png"))
