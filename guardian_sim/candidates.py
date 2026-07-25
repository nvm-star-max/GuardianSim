"""Deterministic grasp-candidate generation for the first GuardianSim MVP."""

from __future__ import annotations

from collections.abc import Sequence
from math import hypot

from guardian_sim.models import ActionCandidate

DEFAULT_YAWS: tuple[float, ...] = (-45.0, -22.5, 0.0, 22.5, 45.0)
DEFAULT_OFFSETS: tuple[float, ...] = (-0.02, 0.0, 0.02)
OBSTACLE_AWARE_YAWS: tuple[float, ...] = (
    -90.0,
    -67.5,
    -45.0,
    -22.5,
    0.0,
    22.5,
    45.0,
    67.5,
    90.0,
)


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


def generate_obstacle_aware_candidates(
    target_xyz: tuple[float, float, float],
    obstacle_xyz: tuple[float, float, float],
    *,
    yaw_degrees: Sequence[float] = OBSTACLE_AWARE_YAWS,
    retreat_distance_m: float = 0.025,
    approach_height_m: float = 0.14,
    gripper_width_m: float = 0.06,
) -> list[ActionCandidate]:
    """Generate centered and obstacle-retreating top-down grasp candidates."""

    if retreat_distance_m <= 0.0:
        raise ValueError("retreat_distance_m must be positive")
    if approach_height_m <= 0.0:
        raise ValueError("approach_height_m must be positive")
    if gripper_width_m <= 0.0:
        raise ValueError("gripper_width_m must be positive")
    if not yaw_degrees:
        raise ValueError("at least one yaw is required")

    away_x = target_xyz[0] - obstacle_xyz[0]
    away_y = target_xyz[1] - obstacle_xyz[1]
    distance = hypot(away_x, away_y)
    if distance <= 1e-9:
        raise ValueError("target and obstacle XY positions must differ")
    retreat = (
        away_x / distance * retreat_distance_m,
        away_y / distance * retreat_distance_m,
    )

    candidates: list[ActionCandidate] = []
    for yaw in yaw_degrees:
        centered_id = (
            "yaw_+00.0_offset_+0.000"
            if float(yaw) == 0.0
            else f"yaw_{float(yaw):+05.1f}_retreat_+0.000_approach_{approach_height_m:+.3f}"
        )
        candidates.append(
            ActionCandidate(
                candidate_id=centered_id,
                target_xyz=target_xyz,
                yaw_degrees=float(yaw),
                lateral_offset_m=0.0,
                approach_height_m=0.10 if float(yaw) == 0.0 else approach_height_m,
                gripper_width_m=gripper_width_m,
            )
        )
        candidates.append(
            ActionCandidate(
                candidate_id=(
                    f"yaw_{float(yaw):+05.1f}_retreat_{retreat_distance_m:+.3f}"
                    f"_approach_{approach_height_m:+.3f}"
                ),
                target_xyz=target_xyz,
                yaw_degrees=float(yaw),
                lateral_offset_m=0.0,
                approach_height_m=approach_height_m,
                gripper_width_m=gripper_width_m,
                target_offset_xy_m=retreat,
            )
        )
    return candidates
