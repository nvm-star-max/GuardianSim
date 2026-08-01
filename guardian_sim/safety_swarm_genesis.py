"""Portable geometry and timing helpers for Safety Swarm Genesis batching.

This module intentionally imports neither Genesis nor Torch.  The cloud runner
converts these deterministic values to GPU tensors after the protocol has been
frozen and written to disk.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin
from typing import Sequence

from guardian_sim.safety_swarm import SafetySwarmWorld

SAFETY_SWARM_BASE_CLUTTER_GAP_M = 0.012
SAFETY_SWARM_BASE_CLUTTER_BEARING_DEG = -90.0


@dataclass(frozen=True, slots=True)
class SafetySwarmPlacement:
    """Per-environment object and action offsets derived from one matrix row."""

    world_id: int
    target_xyz: tuple[float, float, float]
    target_yaw_bias_deg: float
    obstacle_xyz: tuple[float, float, float]
    end_effector_bias_xy_m: tuple[float, float]
    action_start_delay_steps: int


def build_safety_swarm_placements(
    worlds: Sequence[SafetySwarmWorld],
    *,
    base_target_xyz: tuple[float, float, float],
    target_radius_xy_m: float,
    obstacle_radius_xy_m: float,
    obstacle_z_m: float,
) -> tuple[SafetySwarmPlacement, ...]:
    """Map frozen uncertainty rows to collision-free initial scene positions."""

    if target_radius_xy_m <= 0.0 or obstacle_radius_xy_m <= 0.0:
        raise ValueError("object radii must be positive")
    placements: list[SafetySwarmPlacement] = []
    for world in worlds:
        target = (
            base_target_xyz[0] + world.target_dx_m,
            base_target_xyz[1] + world.target_dy_m,
            base_target_xyz[2],
        )
        gap = SAFETY_SWARM_BASE_CLUTTER_GAP_M + world.clutter_gap_delta_m
        if gap <= 0.0:
            raise ValueError("declared clutter perturbation creates a nonpositive gap")
        separation = target_radius_xy_m + obstacle_radius_xy_m + gap
        bearing = radians(
            SAFETY_SWARM_BASE_CLUTTER_BEARING_DEG
            + world.clutter_bearing_bias_deg
        )
        obstacle = (
            target[0] + separation * cos(bearing),
            target[1] + separation * sin(bearing),
            obstacle_z_m,
        )
        placements.append(
            SafetySwarmPlacement(
                world_id=world.world_id,
                target_xyz=target,
                target_yaw_bias_deg=world.target_yaw_bias_deg,
                obstacle_xyz=obstacle,
                end_effector_bias_xy_m=(
                    world.end_effector_dx_m,
                    world.end_effector_dy_m,
                ),
                action_start_delay_steps=world.action_start_delay_steps,
            )
        )
    return tuple(placements)


def delayed_trajectory_alphas(
    delays: Sequence[int],
    *,
    step_index: int,
    trajectory_steps: int,
) -> tuple[float, ...]:
    """Return per-environment interpolation alphas for a delayed trajectory.

    ``step_index`` is one-based.  A delayed environment holds its start pose,
    then receives the same number of motion steps as every other environment.
    """

    if trajectory_steps < 1:
        raise ValueError("trajectory_steps must be positive")
    if step_index < 1:
        raise ValueError("step_index must be positive")
    if any(delay < 0 for delay in delays):
        raise ValueError("delays must be nonnegative")
    return tuple(
        min(1.0, max(0.0, (step_index - delay) / trajectory_steps))
        for delay in delays
    )
