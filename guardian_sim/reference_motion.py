"""Geometry shared by local tests and Genesis reference-scene rollouts."""

from __future__ import annotations

from math import cos, radians, sin

from guardian_sim.models import ActionCandidate


def candidate_grasp_pose(
    candidate: ActionCandidate,
    *,
    object_yaw_degrees: float,
) -> tuple[tuple[float, float, float], float]:
    """Apply a candidate's lateral offset in the gripper's local XY frame."""

    grasp_yaw = object_yaw_degrees + candidate.yaw_degrees
    yaw_radians = radians(grasp_yaw)
    lateral_x = -sin(yaw_radians) * candidate.lateral_offset_m
    lateral_y = cos(yaw_radians) * candidate.lateral_offset_m
    return (
        (
            candidate.target_xyz[0] + candidate.target_offset_xy_m[0] + lateral_x,
            candidate.target_xyz[1] + candidate.target_offset_xy_m[1] + lateral_y,
            candidate.target_xyz[2],
        ),
        grasp_yaw,
    )
