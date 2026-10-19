"""Effect: colour, position, and label of one decomposition effect arrow."""

from __future__ import annotations

from dataclasses import dataclass, replace

from utility_viz.core.styles.label import Label, split_label, to_position
from utility_viz.core.styles.opacity import check_opacity
from utility_viz.enums import LabelPosition


@dataclass(frozen=True)
class Effect:
    """How to show the substitution or income effect in a decomposition."""

    color: str | None = None
    y: float | None = None
    label: str | Label | None = None
    label_position: LabelPosition | str = LabelPosition.RIGHT
    label_offset: float = 4.0
    opacity: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "label_position", to_position(self.label_position, what="Effect label_position"))
        check_opacity("Effect", self.opacity)

    def resolved_label(self, default: Label) -> tuple[str | None, Label]:
        """Return label text and style, with explicit Label fields taking precedence."""
        text, style = split_label(self.label, default)
        own = self.label if isinstance(self.label, Label) else Label()
        return text, replace(
            style,
            position=own.position or self.label_position,
            offset=own.offset if own.offset is not None else self.label_offset,
        )
