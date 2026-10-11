"""Demonstrate LaTeX string parsing into utility function models.

Each entry is a raw LaTeX string.  parse_latex() identifies the family
and returns the appropriate model instance (CobbDouglas, Leontief, or
PerfectSubstitutes), which is then used in the standard solve → draw
workflow.
"""

from pathlib import Path

from utility_viz import Canvas, levels, parse_latex, solve

OUTPUT_DIR = "examples/output/latex"
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# Each case pairs an output file name with a LaTeX utility string.
cases = [
    ("latex_cobb_douglas", r"x^{0.4} y^{0.6}"),
    ("latex_cobb_douglas_u", r"U(x,y) = x^{0.5} y^{0.5}"),
    ("latex_leontief", r"\min(2x, y)"),
    ("latex_leontief_u", r"U = \min(x, 3y)"),
    ("latex_perfect_subs", r"3x + 1.5y"),
    ("latex_perfect_subs_u", r"U(x,y) = 2x + y"),
]

px, py, income = 2.0, 3.0, 30.0

for name, latex in cases:
    model = parse_latex(latex)
    print(f"{latex!r:40s}  →  {model!r}")

    eq = solve(model, px, py, income)
    lvls = levels.around(eq.utility, n=5)

    cvs = Canvas(
        x_max=20,
        y_max=15,
        x_label="x",
        y_label="y",
        title=f"$U(x,y) = {latex.split('=')[-1].strip()}$" if "=" in latex else f"${latex}$",
    )
    cvs.add_utility(model, levels=lvls, show_rays=True, show_kinks=True)
    cvs.add_budget(px, py, income, fill=True)
    cvs.add_equilibrium(eq, show_ray=True)
    cvs.save(f"{OUTPUT_DIR}/{name}.png")
    print(f"  saved → {OUTPUT_DIR}/{name}.png")
