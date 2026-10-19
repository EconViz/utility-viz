"""Animated GIF examples for utility_viz v1.4.0.

This example intentionally separates two different teaching questions:

1. How does the indifference map change when utility-function parameters move?
2. How does the equilibrium bundle move when prices change?

For four common utility functions, the script writes:

- 4 parameter-sweep GIFs
- 4 price-sweep GIFs with ``py`` held fixed
- 4 income-sweep GIFs with the utility function held fixed
- 2 budget-only GIFs that isolate the motion of the budget line itself

Run from the project root::

    python examples/scripts/animation.py

Output is written to ``examples/output/animation/``.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from mosaickit import TextLayer

from utility_viz import Canvas, levels, solve
from utility_viz.core.animation import Animator
from utility_viz.models import CES, CobbDouglas, Leontief, PerfectSubstitutes
from utility_viz.models.curves.layers import Layer

OUTPUT_DIR = "examples/output/animation"
PARAMETER_DIR = f"{OUTPUT_DIR}/parameter_sweeps"
PRICE_DIR = f"{OUTPUT_DIR}/price_sweeps"
INCOME_DIR = f"{OUTPUT_DIR}/income_sweeps"

X_MAX = 14
Y_MAX = 12
INCOME = 20.0
PY_FIXED = 2.0
PX_FOR_PARAMETER_SWEEPS = 2.0
PRICE_MIN = 1.0
PRICE_MAX = 6.0
PRICE_FRAME_COUNT = 45
DEFAULT_SPEED = 1.0
PARAMETER_SPEED = DEFAULT_SPEED
PRICE_SPEED = DEFAULT_SPEED
INCOME_SPEED = DEFAULT_SPEED
INCOME_MIN = 8.0
INCOME_MAX = 36.0
FIGURE_SIZE = (7.6, 6.4)


# Replaced by the real frames once _build_parameter_frames is defined below.
_PLACEHOLDER_FRAMES = np.empty(0)


@dataclass(frozen=True)
class UtilityAnimationSpec:
    """Configuration for one model family in the animation gallery."""

    key: str
    title: str
    parameter_name: str
    parameter_frames: np.ndarray
    parameter_factory: Callable[[float], object]
    parameter_label: Callable[[float], str]
    price_model: object
    utility_kwargs: dict = field(default_factory=dict)


SPECS = [
    UtilityAnimationSpec(
        key="cobb_douglas",
        title="Cobb-Douglas",
        parameter_name="alpha",
        parameter_frames=_PLACEHOLDER_FRAMES,
        parameter_factory=lambda alpha: CobbDouglas(alpha=alpha, beta=1.0 - alpha),
        parameter_label=lambda alpha: rf"$\alpha={alpha:.2f},\ \beta={1.0 - alpha:.2f}$",
        price_model=CobbDouglas(alpha=0.5, beta=0.5),
    ),
    UtilityAnimationSpec(
        key="ces",
        title="CES",
        parameter_name="rho",
        parameter_frames=_PLACEHOLDER_FRAMES,
        parameter_factory=lambda rho: CES(alpha=0.5, beta=0.5, rho=rho),
        parameter_label=lambda rho: rf"$\rho={rho:.2f}$",
        price_model=CES(alpha=0.5, beta=0.5, rho=0.4),
    ),
    UtilityAnimationSpec(
        key="perfect_substitutes",
        title="Perfect Substitutes",
        parameter_name="a",
        parameter_frames=_PLACEHOLDER_FRAMES,
        parameter_factory=lambda a: PerfectSubstitutes(a=a, b=1.0),
        parameter_label=lambda a: rf"$a={a:.2f},\ b=1.00$",
        price_model=PerfectSubstitutes(a=1.5, b=1.0),
        utility_kwargs={"show_rays": True},
    ),
    UtilityAnimationSpec(
        key="leontief",
        title="Leontief",
        parameter_name="a",
        parameter_frames=_PLACEHOLDER_FRAMES,
        parameter_factory=lambda a: Leontief(a=a, b=1.0),
        parameter_label=lambda a: rf"$a={a:.2f},\ b=1.00$",
        price_model=Leontief(a=1.5, b=1.0),
        utility_kwargs={"show_rays": True, "show_kinks": True},
    ),
]


def _parameterized_progress(n: int, speed: float = DEFAULT_SPEED) -> np.ndarray:
    """Return monotone progress values in [0, 1] with configurable pacing."""
    if speed <= 0:
        raise ValueError("speed must be positive.")
    progress = np.linspace(0.0, 1.0, n)
    if speed == 1.0:
        return progress
    return progress**speed


def _parameterized_linear_frames(
    start: float,
    stop: float,
    n: int,
    speed: float = DEFAULT_SPEED,
) -> np.ndarray:
    """Interpolate linearly between two endpoints with configurable pacing."""
    progress = _parameterized_progress(n=n, speed=speed)
    return start + (stop - start) * progress


def _build_parameter_frames(spec_key: str) -> np.ndarray:
    """Build parameter frames for one utility family."""
    if spec_key == "cobb_douglas":
        return _parameterized_linear_frames(0.2, 0.8, PRICE_FRAME_COUNT, speed=PARAMETER_SPEED)
    if spec_key == "ces":
        left = _parameterized_linear_frames(-1.2, -0.1, 23, speed=PARAMETER_SPEED)
        right = _parameterized_linear_frames(0.1, 0.8, 22, speed=PARAMETER_SPEED)
        return np.concatenate([left, right])
    if spec_key in {"perfect_substitutes", "leontief"}:
        return _parameterized_linear_frames(0.6, 2.4, PRICE_FRAME_COUNT, speed=PARAMETER_SPEED)
    raise ValueError(f"Unknown spec key: {spec_key}")


for idx, spec in enumerate(SPECS):
    SPECS[idx] = UtilityAnimationSpec(
        key=spec.key,
        title=spec.title,
        parameter_name=spec.parameter_name,
        parameter_frames=_build_parameter_frames(spec.key),
        parameter_factory=spec.parameter_factory,
        parameter_label=spec.parameter_label,
        price_model=spec.price_model,
        utility_kwargs=spec.utility_kwargs,
    )


def _add_frame_metadata(canvas: Canvas, *lines: str) -> Canvas:
    """Attach compact frame metadata as scene text."""
    canvas.add(
        TextLayer(
            (canvas.x_max, canvas.y_max),
            "Dynamic Info",
            id="animation.metadata.title",
            role="title",
            offset=(-8, -8),
            anchor="top-right",
            z_index=9,
        )
    )
    canvas.add(
        TextLayer(
            (canvas.x_max, canvas.y_max),
            "\n".join(lines),
            id="animation.metadata.body",
            role="axes",
            offset=(-8, -28),
            anchor="top-right",
            z_index=9,
        )
    )
    return canvas


def _fixed_levels_for_model(model, n: int = 5, res: int = 400) -> list[float]:
    """Compute one reusable IC family for a fixed utility function.

    Price and income sweeps should hold the utility function fixed, so they
    should also hold the background indifference-map levels fixed.
    """
    _, _, z = Layer.compute_contour(model, (0.1, X_MAX), (0.1, Y_MAX), res=res)
    return levels.percentile(z, n=n, lo=20, hi=80)


def _uniform_budget_speed_price_frames(
    px_min: float = PRICE_MIN,
    px_max: float = PRICE_MAX,
    income: float = INCOME,
    n: int = PRICE_FRAME_COUNT,
    speed: float = PRICE_SPEED,
) -> np.ndarray:
    """Sample prices so the x-intercept moves at a roughly constant speed.

    Linear spacing in price makes the budget line appear slow at first and
    much faster near low prices because the x-intercept equals ``income / px``.
    Here we sample uniformly in x-intercept space, then map back to price.
    """
    x_intercept_min = income / px_max
    x_intercept_max = income / px_min
    x_intercepts = _parameterized_linear_frames(
        x_intercept_min,
        x_intercept_max,
        n=n,
        speed=speed,
    )
    return income / x_intercepts


def _budget_only_canvas(title: str, px: float, py: float, income: float) -> Canvas:
    """Render an animation-ready budget-only frame with a right metadata gutter."""
    canvas = _make_animation_canvas(title=title)
    canvas.add_budget(px=px, py=py, income=income, fill=True)
    return canvas


def _make_animation_canvas(title: str) -> Canvas:
    """Create a slightly wider canvas with reserved space for frame metadata."""
    canvas = Canvas(
        x_max=X_MAX,
        y_max=Y_MAX,
        x_label="X_1",
        y_label="X_2",
        title=title,
        dpi=120,
    )
    canvas.spec = canvas.spec.replace(width=FIGURE_SIZE[0], height=FIGURE_SIZE[1])
    return canvas


def build_parameter_drawer(spec: UtilityAnimationSpec) -> Callable[[float], Canvas]:
    """Return a frame factory for one utility-parameter sweep."""

    def _draw(param_value: float) -> Canvas:
        model = spec.parameter_factory(float(param_value))
        eq = solve(model, px=PX_FOR_PARAMETER_SWEEPS, py=PY_FIXED, income=INCOME)
        canvas = _make_animation_canvas(title=f"{spec.title} parameter sweep")
        canvas.add_utility(model, levels=levels.around(eq.utility, n=5), **spec.utility_kwargs)
        canvas.add_budget(px=PX_FOR_PARAMETER_SWEEPS, py=PY_FIXED, income=INCOME, fill=True)
        canvas.add_equilibrium(eq, drop_dashes=True, show_ray=True)
        return _add_frame_metadata(
            canvas,
            spec.parameter_label(float(param_value)),
            rf"$(x^*, y^*) = ({eq.x:.2f}, {eq.y:.2f})$",
        )

    return _draw


def build_price_drawer(spec: UtilityAnimationSpec) -> Callable[[float], Canvas]:
    """Return a frame factory for one price sweep with py fixed."""
    model = spec.price_model
    fixed_levels = _fixed_levels_for_model(model)

    def _draw(px: float) -> Canvas:
        eq = solve(model, px=float(px), py=PY_FIXED, income=INCOME)
        canvas = _make_animation_canvas(title=f"{spec.title} price sweep")
        canvas.add_utility(model, levels=fixed_levels, **spec.utility_kwargs)
        canvas.add_budget(px=float(px), py=PY_FIXED, income=INCOME, fill=True)
        canvas.add_equilibrium(eq, drop_dashes=True, show_ray=True)
        return _add_frame_metadata(
            canvas,
            rf"$p_x={px:.2f}$",
            rf"$p_y={PY_FIXED:.2f}$",
            rf"$(x^*, y^*) = ({eq.x:.2f}, {eq.y:.2f})$",
        )

    return _draw


def build_income_drawer(spec: UtilityAnimationSpec) -> Callable[[float], Canvas]:
    """Return a frame factory for one income sweep with utility fixed."""
    model = spec.price_model
    fixed_levels = _fixed_levels_for_model(model)

    def _draw(income: float) -> Canvas:
        eq = solve(model, px=PX_FOR_PARAMETER_SWEEPS, py=PY_FIXED, income=float(income))
        canvas = _make_animation_canvas(title=f"{spec.title} income sweep")
        canvas.add_utility(model, levels=fixed_levels, **spec.utility_kwargs)
        canvas.add_budget(px=PX_FOR_PARAMETER_SWEEPS, py=PY_FIXED, income=float(income), fill=True)
        canvas.add_equilibrium(eq, drop_dashes=True, show_ray=True)
        return _add_frame_metadata(
            canvas,
            rf"$I={income:.2f}$",
            rf"$p_x={PX_FOR_PARAMETER_SWEEPS:.2f},\ p_y={PY_FIXED:.2f}$",
            rf"$(x^*, y^*) = ({eq.x:.2f}, {eq.y:.2f})$",
        )

    return _draw


def build_budget_only_price_drawer() -> Callable[[float], Canvas]:
    """Return a frame factory for a pure budget-line price sweep."""

    def _draw(px: float) -> Canvas:
        canvas = _budget_only_canvas(
            title="Budget-only price sweep",
            px=float(px),
            py=PY_FIXED,
            income=INCOME,
        )
        return _add_frame_metadata(
            canvas,
            rf"$p_x={px:.2f}$",
            rf"$p_y={PY_FIXED:.2f}$",
            rf"$x\mathrm{{-int}}={INCOME / px:.2f}$",
        )

    return _draw


def build_budget_only_income_drawer() -> Callable[[float], Canvas]:
    """Return a frame factory for a pure budget-line income sweep."""

    def _draw(income: float) -> Canvas:
        canvas = _budget_only_canvas(
            title="Budget-only income sweep",
            px=PX_FOR_PARAMETER_SWEEPS,
            py=PY_FIXED,
            income=float(income),
        )
        return _add_frame_metadata(
            canvas,
            rf"$I={income:.2f}$",
            rf"$p_x={PX_FOR_PARAMETER_SWEEPS:.2f},\ p_y={PY_FIXED:.2f}$",
            rf"$x\mathrm{{-int}}={income / PX_FOR_PARAMETER_SWEEPS:.2f},\ "
            rf"y\mathrm{{-int}}={income / PY_FIXED:.2f}$",
        )

    return _draw


def main(*, smoke: bool = False) -> None:
    """Render the animation gallery or one short representative GIF."""
    for directory in (PARAMETER_DIR, PRICE_DIR, INCOME_DIR):
        Path(directory).mkdir(parents=True, exist_ok=True)

    if smoke:
        frames = _uniform_budget_speed_price_frames(n=3)
        out_path = f"{PRICE_DIR}/budget_only_price_sweep.gif"
        print("Rendering animation smoke test ...")
        Animator(build_budget_only_price_drawer(), frames=frames).save(
            out_path,
            fps=2,
            dpi=72,
        )
        print(f"  -> saved to {out_path}")
        return

    price_frames = _uniform_budget_speed_price_frames(speed=PRICE_SPEED)
    income_frames = _parameterized_linear_frames(
        INCOME_MIN,
        INCOME_MAX,
        PRICE_FRAME_COUNT,
        speed=INCOME_SPEED,
    )

    print("Rendering parameter sweeps ...")
    for idx, spec in enumerate(SPECS, start=1):
        out_path = f"{PARAMETER_DIR}/{spec.key}_parameter_sweep.gif"
        print(f"  [{idx}/4] {spec.title} parameter sweep")
        Animator(build_parameter_drawer(spec), frames=spec.parameter_frames).save(
            out_path,
            fps=12,
            dpi=120,
        )
        print(f"      -> saved to {out_path}")

    print("Rendering price sweeps (holding py fixed) ...")
    for idx, spec in enumerate(SPECS, start=1):
        out_path = f"{PRICE_DIR}/{spec.key}_price_sweep.gif"
        print(f"  [{idx}/4] {spec.title} price sweep")
        Animator(build_price_drawer(spec), frames=price_frames).save(
            out_path,
            fps=12,
            dpi=120,
        )
        print(f"      -> saved to {out_path}")

    budget_only_price_path = f"{PRICE_DIR}/budget_only_price_sweep.gif"
    print("  [budget] Budget-only price sweep")
    Animator(build_budget_only_price_drawer(), frames=price_frames).save(
        budget_only_price_path,
        fps=12,
        dpi=120,
    )
    print(f"      -> saved to {budget_only_price_path}")

    print("Rendering income sweeps (holding utility and prices fixed) ...")
    for idx, spec in enumerate(SPECS, start=1):
        out_path = f"{INCOME_DIR}/{spec.key}_income_sweep.gif"
        print(f"  [{idx}/4] {spec.title} income sweep")
        Animator(build_income_drawer(spec), frames=income_frames).save(
            out_path,
            fps=12,
            dpi=120,
        )
        print(f"      -> saved to {out_path}")

    budget_only_income_path = f"{INCOME_DIR}/budget_only_income_sweep.gif"
    print("  [budget] Budget-only income sweep")
    Animator(build_budget_only_income_drawer(), frames=income_frames).save(
        budget_only_income_path,
        fps=12,
        dpi=120,
    )
    print(f"      -> saved to {budget_only_income_path}")

    print(f"\nDone. Wrote 14 GIFs under {OUTPUT_DIR}")


JUPYTER_EXAMPLE = """
# ── Paste into a Jupyter notebook cell ──────────────────────────────
from utility_viz.core.interactive import WidgetViewer
from utility_viz import Canvas, levels, solve
from utility_viz.models import CobbDouglas

def draw(alpha: float, px: float) -> Canvas:
    model = CobbDouglas(alpha=alpha, beta=1.0 - alpha)
    eq = solve(model, px=px, py=2.0, income=20.0)
    c = Canvas(x_max=14, y_max=12, x_label="X_1", y_label="X_2")
    c.add_utility(model, levels=levels.around(eq.utility, n=5))
    c.add_budget(px=px, py=2.0, income=20.0, fill=True)
    c.add_equilibrium(eq, drop_dashes=True, show_ray=True)
    return c

WidgetViewer(draw, alpha=(0.2, 0.8, 0.05), px=(1.0, 6.0, 0.25)).show()
# ────────────────────────────────────────────────────────────────────
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="render one three-frame GIF for a fast integration check",
    )
    main(smoke=parser.parse_args().smoke)
