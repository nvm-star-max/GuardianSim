"""Deterministic grasp-candidate generation for the first GuardianSim MVP."""

from __future__ import annotations

from collections.abc import Sequence

from guardian_sim.models import ActionCandidate


DEFAULT_YAWS: tuple[float, ...] = (-45.0, -22.5, 0.0, 22.5, 45.0)
DEFAULT_OFFSETS: tuple[float, ...] = (-0.02, 0.0, 0.02)


def generate_grasp_candidates(
    target_xyz: tuple[float, float, float],
    *,
    yaw_degrees: Sequence[float] = DEFAULT_YAWS,
    lateral_offsets_m: Sequence[float] = DEFAULT_OFFSETS,
    approach_height_m: float = 0.10,
    gripper_width_m: float = 0.06,
) -> list[ActionCandidate]:
    """Generate reproducible candidate poses around a perceived target."""

    if approach_height_m <= 0:
        raise ValueError("approach_height_m must be positive")
    if gripper_width_m <= 0:
        raise ValueError("gripper_width_m must be positive")
    if not yaw_degrees or not lateral_offsets_m:
        raise ValueError("at least one yaw and one lateral offset are required")

    candidates: list[ActionCandidate] = []
    for yaw in yaw_degrees:
        for offset in lateral_offsets_m:
            candidate_id = f"yaw_{yaw:+05.1f}_offset_{offset:+.3f}"
            candidates.append(
                ActionCandidate(
                    candidate_id=candidate_id,
                    target_xyz=target_xyz,
                    yaw_degrees=float(yaw),
                    lateral_offset_m=float(offset),
                    approach_height_m=approach_height_m,
                    gripper_width_m=gripper_width_m,
                )
            )
    return candidates
