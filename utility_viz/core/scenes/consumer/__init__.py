"""Consumer-theory scene factories."""

from utility_viz.core.scenes.consumer.demand import marshallian_demand_layers
from utility_viz.core.scenes.consumer.edgeworth import (
    edgeworth_frame_layers,
    edgeworth_indifference_layers,
    edgeworth_path_layer,
    edgeworth_point_layers,
)

__all__ = [
    "edgeworth_frame_layers",
    "edgeworth_indifference_layers",
    "edgeworth_path_layer",
    "edgeworth_point_layers",
    "marshallian_demand_layers",
]
