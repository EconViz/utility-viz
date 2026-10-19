"""
utility_viz.core.animation
==================

Parameter-sweep GIF animation for utility_viz diagrams.

Usage::

    from utility_viz.core.animation import Animator
    import numpy as np

    def draw(p1: float):
        from utility_viz import Canvas
        from utility_viz.models.utility import CobbDouglas
        c = Canvas(x_max=10, y_max=10, x_label="X_1", y_label="X_2")
        c.add_budget(px=p1, py=2.0, income=20.0)
        return c

    Animator(draw, frames=np.linspace(1, 8, 40)).save("sweep.gif", fps=12)

Requires ``KineticKit`` with raster export support::

    pip install utility-viz[animation]
    # or: pip install 'kinetickit[raster]'
"""

from utility_viz.core.animation.animator import Animator

__all__ = ["Animator"]
