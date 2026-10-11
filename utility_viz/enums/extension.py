"""
Enumeration of supported export file formats.

Used by :meth:`Canvas.save` to dispatch to the correct export backend
with strict validation rather than raw string comparison.
"""

from enum import Enum

from utility_viz.core.errors.exceptions import ExportError


class ExportFormat(Enum):
    """Supported output formats for :meth:`Canvas.save`.

    Members
    -------
    PNG
        Raster image export (default).
    PDF
        PDF vector export.
    SVG
        Scalable vector export.
    TEX
        Pure TikZ export from the scene graph.
    """

    PNG = "png"
    PDF = "pdf"
    SVG = "svg"
    TEX = "tex"

    @classmethod
    def from_path(cls, path: str) -> "ExportFormat":
        """Infer the format from a file path's extension.

        Parameters
        ----------
        path : str
            Destination file path (e.g. ``"plot.png"``).

        Returns
        -------
        ExportFormat

        Raises
        ------
        ExportError
            If the extension is not recognised.
        """
        ext = path.rsplit(".", maxsplit=1)[-1].lower()
        try:
            return cls(ext)
        except ValueError:
            supported = ", ".join(f".{m.value}" for m in cls)
            raise ExportError(f"Unsupported file extension '.{ext}'. Supported formats: {supported}") from None
