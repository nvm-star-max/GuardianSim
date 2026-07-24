"""Convert sampled Genesis motion traces into candidate measurements."""

from __future__ import annotations

from dataclasses import dataclass
from math import dist, sqrt

from guardian_sim.genesis_adapter import GenesisRolloutMeasurement


@dataclass(frozen=True, slots=True)
class RolloutTrace:
    """Raw physical observations collected while executing one candidate."""

    minimum_clearance_m: float
    reachable: bool
    alignment_error_degrees: float
    object_start_height_m: float
    object_retained_height_m: float
    requested_lift_height_m: float
    end_effector_positions: tuple[tuple[float, float, float], ...]
    perception_uncertainty: float


def aabb_clearance(
    first: tuple[tuple[float, float, float], tuple[float, float, float]],
    second: tuple[tuple[float, float, float], tuple[float, float, float]],
) -> float:
    """Euclidean separation between two world-frame collision AABBs."""

    gaps = [
        max(first[0][axis] - second[1][axis], second[0][axis] - first[1][axis], 0.0)
        for axis in range(3)
    ]
    return sqrt(sum(gap * gap for gap in gaps))


def measure_rollout(trace: RolloutTrace) -> GenesisRolloutMeasurement:
    """Derive planner inputs without applying risk-scoring weights."""

    path_length_m = sum(
        dist(start, end)
        for start, end in zip(
            trace.end_effector_positions,
            trace.end_effector_positions[1:],
        )
    )
    retained_lift_height_m = max(
        0.0,
        trace.object_retained_height_m - trace.object_start_height_m,
    )
    return GenesisRolloutMeasurement(
        minimum_clearance_m=trace.minimum_clearance_m,
        reachable=trace.reachable,
        alignment_error_degrees=trace.alignment_error_degrees,
        retained_lift_height_m=retained_lift_height_m,
        requested_lift_height_m=trace.requested_lift_height_m,
        path_length_m=path_length_m,
        perception_uncertainty=trace.perception_uncertainty,
    )
