"""Hicks decompositions of a fall in p_x for five kinds of goods.

Normal and income-neutral goods use Cobb-Douglas and quasi-linear utility.
The three inferior cases use Haagsma's (2012) utility, whose good x is always
inferior. With income I fixed, gamma_y * p_y above, equal to, or below I gives
an ordinary inferior good, exactly offsetting effects, and a Giffen good.

Haagsma, R. (2012). A convenient utility function with Giffen behaviour.
ISRN Economics, 2012, 1-4. https://doi.org/10.5402/2012/608645
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np

from utility_viz import Canvas, Effect
from utility_viz.models import CobbDouglas, Haagsma, QuasiLinear
from utility_viz.models.optimization import DecompositionMethod, decompose_price_effect

OUTPUT_DIR = Path("examples/output/decom/goods")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PX = (2.0, 1.0)  # p_x falls
PY = 1.0
INCOME = 28.0


CASES = [
    ("1_normal", "Normal good", CobbDouglas(alpha=0.5, beta=0.5)),
    ("2_neutral", "Income-neutral good", QuasiLinear(v_func=lambda z: 4.0 * np.log(z), linear_in="y")),
    ("3_inferior", "Inferior good: SE > |IE|", Haagsma(gamma_y=30.0)),
    ("4_offsetting", "Inferior good: SE = |IE|", Haagsma(gamma_y=28.0)),
    ("5_giffen", "Giffen good: SE < |IE|", Haagsma(gamma_y=27.0)),
]


def _axis_limits(dec) -> tuple[float, float]:
    xs = [dec.A.x, dec.B.x, dec.C.x, dec.income / dec.px_after, dec.compensated_income / dec.px_after]
    ys = [dec.A.y, dec.B.y, dec.C.y, dec.income / dec.py, dec.compensated_income / dec.py]
    return max(xs) * 1.2, max(ys) * 1.25


def build_examples() -> None:
    for slug, title, model in CASES:
        with warnings.catch_warnings():
            # Inferior and Giffen goods are the point here; silence the library's reminders.
            warnings.filterwarnings("ignore", message=".*(inferior|Giffen) good.*")
            dec = decompose_price_effect(model, px=PX, py=PY, income=INCOME, method=DecompositionMethod.HICKS)
        x_max, y_max = _axis_limits(dec)
        (
            Canvas(x_max=x_max, y_max=y_max, x_label="x", y_label="y", title=title)
            .add_decomposition(
                dec,
                show_x_projections=True,
                substitution=Effect(label="SE"),
                income=Effect(label="IE"),
            )
            .save(str(OUTPUT_DIR / f"{slug}.png"))
        )
        se, ie, te = dec.substitution_effect[0], dec.income_effect[0], dec.total_effect[0]
        print(f"[ok] {slug}: SE={se:+.2f} IE={ie:+.2f} TE={te:+.2f}")


if __name__ == "__main__":
    build_examples()
