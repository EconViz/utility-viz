"""
Layer — numerical evaluation helpers for contour-based visualizations.

The :class:`Layer` class provides static methods that convert a scalar
utility function into mesh-grid arrays for numerical level-set operations.
"""

from collections.abc import Callable

import numpy as np


class Layer:
    """Utility evaluation layer for generating contour data.

    This class is not instantiated directly; all functionality is exposed
    through static methods.
    """

    @staticmethod
    def compute_contour(
        func: Callable[[np.ndarray, np.ndarray], np.ndarray],
        x_range: tuple[float, float],
        y_range: tuple[float, float],
        res: int = 400,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Evaluate *func* over a 2-D mesh grid.

        Parameters
        ----------
        func : Callable[[ndarray, ndarray], ndarray]
            A vectorized function ``f(X, Y)`` returning utility values.
        x_range : tuple[float, float]
            ``(x_min, x_max)`` bounds for the horizontal axis.
        y_range : tuple[float, float]
            ``(y_min, y_max)`` bounds for the vertical axis.
        res : int
            Number of sample points along each axis (total grid size is
            *res* × *res*).

        Returns
        -------
        tuple[ndarray, ndarray, ndarray]
            ``(X, Y, Z)`` mesh-grid arrays suitable for level-set tracing.
        """
        x = np.linspace(x_range[0], x_range[1], res)
        y = np.linspace(y_range[0], y_range[1], res)
        X, Y = np.meshgrid(x, y)

        with np.errstate(divide="ignore", invalid="ignore"):
            Z = func(X, Y)

        return X, Y, Z
