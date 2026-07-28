#!/usr/bin/env python3
"""Execute 18 x 3 GuardianSim candidate futures in one batched Genesis scene."""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from guardian_sim.candidates import generate_obstacle_aware_candidates
from guardian_sim.gate32_benchmark import (
    GATE32_MINIMUM_SAFE_CLEARANCE_M,
    GATE32_MINIMUM_STABILITY,
)
from guardian_sim.parallel_futures import (
    PARALLEL_FUTURES_PHASE_STEPS,
    PARALLEL_FUTURES_REPEATS,
    PARALLEL_FUTURES_REPORT_NAME,
    PARALLEL_FUTURES_SCHEMA_VERSION,
    assign_parallel_futures,
    build_parallel_future_poses,
    build_parallel_futures_protocol,
    validate_parallel_futures_report,
)
from guardian_sim.rocm_telemetry import RocmSmiSampler

PICK_OBJECT = "011_banana"
OBSTACLE_OBJECT = "018_plum"
REQUESTED_LIFT_HEIGHT_M = 0.10
CLEARANCE_LINK_NAMES = (
    "link5",
    "link6",
    "link7",
    "hand",
    "left_finger",
    "right_finger",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preflight-output", type=Path)
    parser.add_argument("--validation-output", type=Path)
    return parser


def _as_batched_tensor(value, *, n_envs: int, torch):
    tensor = value if isinstance(value, torch.Tensor) else torch.as_tensor(value)
    tensor = tensor.to(device=torch.device("cuda"), dtype=torch.float32)
    if tensor.ndim == 1:
        tensor = tensor.unsqueeze(0)
    if tensor.shape[0] == 1 and n_envs > 1:
        tensor = tensor.repeat(n_envs, *([1] * (tensor.ndim - 1)))
    if tensor.shape[0] != n_envs:
        raise ValueError(f"expected {n_envs} environments, got {tensor.shape[0]}")
    return tensor


def _first_numpy(value):
    if hasattr(value, "detach"):
        value = value.detach().cpu().numpy()
    import numpy as np

    array = np.asarray(value)
    if array.ndim > 1:
        array = array[0]
    return array


def _place_controlled_clutter(bundle, *, n_envs: int, torch) -> None:
    from franka_fruit_pick.scene_config import get_ycb_assets

    assets = get_ycb_assets()
    target = bundle.ycb[PICK_OBJECT]
    obstacle = bundle.ycb[OBSTACLE_OBJECT]
    target_base = _as_batched_tensor(
        target.get_pos(),
        n_envs=n_envs,
        torch=torch,
    )[0]
    obstacle_base = _as_batched_tensor(
        obstacle.get_pos(),
        n_envs=n_envs,
        torch=torch,
    )[0]
    separation = (
        assets[PICK_OBJECT].radius_xy
        + assets[OBSTACLE_OBJECT].radius_xy
        + 0.012
    )
    target_position = target_base.repeat(n_envs, 1)
    obstacle_position = obstacle_base.repeat(n_envs, 1)
    obstacle_position[:, 0] = target_position[:, 0]
    obstacle_position[:, 1] = target_position[:, 1] - separation
    target.set_pos(target_position, zero_velocity=True)
    obstacle.set_pos(obstacle_position, zero_velocity=True)

    parking_xy = iter(((0.66, 0.25), (0.66, -0.25)))
    for name, entity in sorted(bundle.ycb.items()):
        if name in {PICK_OBJECT, OBSTACLE_OBJECT}:
            continue
        x, y = next(parking_xy)
        position = _as_batched_tensor(
            entity.get_pos(),
            n_envs=n_envs,
            torch=torch,
        )
        position[:, 0] = x
        position[:, 1] = y
        entity.set_pos(position, zero_velocity=True)


class _BatchedRecorder:
    def __init__(self, bundle, *, n_envs: int, torch) -> None:
        self._bundle = bundle
        self._n_envs = n_envs
        self._torch = torch
        self._hand = bundle.franka.get_link("hand")
        self._links = [
            bundle.franka.get_link(name)
            for name in CLEARANCE_LINK_NAMES
        ]
        self._obstacles = [
            entity
            for name, entity in sorted(bundle.ycb.items())
            if name != PICK_OBJECT
        ]
        self.minimum_clearance = torch.full(
            (n_envs,),
            math.inf,
            device=torch.device("cuda"),
            dtype=torch.float32,
        )
        self.path_length = torch.zeros(
            n_envs,
            device=torch.device("cuda"),
            dtype=torch.float32,
        )
        self._previous_hand_position = None

    def sample(self) -> None:
        torch = self._torch
        hand_position = _as_batched_tensor(
            self._hand.get_pos(),
            n_envs=self._n_envs,
            torch=torch,
        )
        if self._previous_hand_position is not None:
            self.path_length += torch.linalg.vector_norm(
                hand_position - self._previous_hand_position,
                dim=1,
            )
        self._previous_hand_position = hand_position.clone()

        per_sample = torch.full_like(self.minimum_clearance, math.inf)
        for link in self._links:
            link_bounds = _as_batched_tensor(
                link.get_AABB(),
                n_envs=self._n_envs,
                torch=torch,
            )
            link_min, link_max = link_bounds[:, 0], link_bounds[:, 1]
            for obstacle in self._obstacles:
                obstacle_bounds = _as_batched_tensor(
                    obstacle.get_AABB(),
                    n_envs=self._n_envs,
                    torch=torch,
                )
                obstacle_min = obstacle_bounds[:, 0]
                obstacle_max = obstacle_bounds[:, 1]
                gaps = torch.maximum(
                    torch.maximum(
                        link_min - obstacle_max,
                        obstacle_min - link_max,
                    ),
                    torch.zeros_like(link_min),
                )
                clearance = torch.linalg.vector_norm(gaps, dim=1)
                per_sample = torch.minimum(per_sample, clearance)
        self.minimum_clearance = torch.minimum(
            self.minimum_clearance,
            per_sample,
        )


def _command_position_trajectory(
    bundle,
    start,
    goal,
    *,
    steps: int,
    settle_steps: int,
    recorder: _BatchedRecorder,
    sample_every: int = 5,
) -> None:
    for step_index in range(1, steps + 1):
        alpha = step_index / steps
        command = start + (goal - start) * alpha
        bundle.franka.control_dofs_position(command)
        bundle.scene.step()
        if step_index % sample_every == 0:
            recorder.sample()
    for settle_index in range(settle_steps):
        bundle.franka.control_dofs_position(goal)
        bundle.scene.step()
        if (settle_index + 1) % sample_every == 0:
            recorder.sample()


def _command_force_hold(
    bundle,
    arm_goal,
    *,
    steps: int,
    close_force: float,
    recorder: _BatchedRecorder,
    torch,
    sample_every: int = 5,
) -> None:
    motors = list(range(7))
    fingers = [7, 8]
    finger_force = torch.full(
        (arm_goal.shape[0], 2),
        close_force,
        device=arm_goal.device,
        dtype=arm_goal.dtype,
    )
    for step_index in range(steps):
        bundle.franka.control_dofs_position(arm_goal, motors)
        bundle.franka.control_dofs_force(finger_force, fingers)
        bundle.scene.step()
        if (step_index + 1) % sample_every == 0:
            recorder.sample()


def _command_lift(
    bundle,
    arm_start,
    arm_goal,
    *,
    steps: int,
    settle_steps: int,
    close_force: float,
    recorder: _BatchedRecorder,
    torch,
    sample_every: int = 5,
) -> None:
    motors = list(range(7))
    fingers = [7, 8]
    finger_force = torch.full(
        (arm_goal.shape[0], 2),
        close_force,
        device=arm_goal.device,
        dtype=arm_goal.dtype,
    )

    def command(arm, step_index: int) -> None:
        bundle.franka.control_dofs_position(arm, motors)
        bundle.franka.control_dofs_force(finger_force, fingers)
        bundle.scene.step()
        if step_index % sample_every == 0:
            recorder.sample()

    for step_index in range(1, steps + 1):
        alpha = step_index / steps
        command(arm_start + (arm_goal - arm_start) * alpha, step_index)
    for settle_index in range(1, settle_steps + 1):
        command(arm_goal, settle_index)


def main() -> None:
    args = build_parser().parse_args()

    import genesis as gs
    import numpy as np
    import torch
    from genesis.utils.geom import quat_to_xyz

    from franka_fruit_pick.build_scene import build_scene
    from franka_fruit_pick.grasp_demo import (
        DEFAULT_PROFILE,
        GRASP_PROFILES,
        _grasp_hand_z,
    )
    from franka_fruit_pick.scene_config import FRANKA_QPOS

    if not torch.cuda.is_available() or not torch.version.hip:
        raise RuntimeError("parallel futures require ROCm/HIP PyTorch")

    placeholder_candidates = generate_obstacle_aware_candidates(
        (0.31, 0.22, 0.78),
        (0.31, 0.12, 0.78),
    )
    n_envs = len(placeholder_candidates) * PARALLEL_FUTURES_REPEATS
    gs.init(backend=gs.gpu)
    build_started = time.perf_counter()
    bundle = build_scene(
        n_envs=n_envs,
        add_world_cam=False,
        add_wrist_cam=False,
        add_video_cam=False,
    )
    torch.cuda.synchronize()
    build_seconds = time.perf_counter() - build_started

    _place_controlled_clutter(bundle, n_envs=n_envs, torch=torch)
    hold = torch.as_tensor(
        np.tile(np.asarray(FRANKA_QPOS), (n_envs, 1)),
        device=torch.device("cuda"),
        dtype=torch.float32,
    )
    for _ in range(PARALLEL_FUTURES_PHASE_STEPS["settle"]):
        bundle.franka.control_dofs_position(hold)
        bundle.scene.step()

    pick_entity = bundle.ycb[PICK_OBJECT]
    obstacle_entity = bundle.ycb[OBSTACLE_OBJECT]
    target_position = _first_numpy(pick_entity.get_pos())[:3]
    obstacle_position = _first_numpy(obstacle_entity.get_pos())[:3]
    target_quaternion = _first_numpy(pick_entity.get_quat())[:4]
    object_yaw = float(quat_to_xyz(target_quaternion, degrees=True)[2])
    candidates = tuple(
        generate_obstacle_aware_candidates(
            tuple(float(value) for value in target_position),
            tuple(float(value) for value in obstacle_position),
        )
    )
    assignments = assign_parallel_futures(candidates)
    if len(assignments) != n_envs:
        raise AssertionError("parallel environment count drift")
    profile = GRASP_PROFILES.get(PICK_OBJECT, DEFAULT_PROFILE)
    grasp_hand_z = _grasp_hand_z(pick_entity, profile)
    poses = build_parallel_future_poses(
        candidates,
        object_yaw_degrees=object_yaw + profile.yaw_offset,
        object_start_height_m=float(target_position[2]),
        grasp_hand_z_m=grasp_hand_z,
    )
    protocol = build_parallel_futures_protocol(candidates)
    preflight_path = args.preflight_output or args.output.with_suffix(".preflight.json")
    preflight_path.parent.mkdir(parents=True, exist_ok=True)
    preflight_path.write_text(
        json.dumps(
            {
                "status": "frozen_before_execution",
                "protocol": protocol,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    device = torch.device("cuda")
    pregrasp_positions = torch.tensor(
        [pose.pregrasp_position for pose in poses],
        device=device,
        dtype=torch.float32,
    )
    grasp_positions = torch.tensor(
        [pose.grasp_position for pose in poses],
        device=device,
        dtype=torch.float32,
    )
    grasp_quaternions = torch.tensor(
        [pose.grasp_quaternion_wxyz for pose in poses],
        device=device,
        dtype=torch.float32,
    )
    finger_open = torch.tensor(
        [pose.finger_open_m for pose in poses],
        device=device,
        dtype=torch.float32,
    )
    hand = bundle.franka.get_link("hand")
    recorder = _BatchedRecorder(bundle, n_envs=n_envs, torch=torch)
    recorder.sample()
    object_start_positions = _as_batched_tensor(
        pick_entity.get_pos(),
        n_envs=n_envs,
        torch=torch,
    ).clone()
    reachable = torch.ones(n_envs, device=device, dtype=torch.bool)

    sampler = RocmSmiSampler()
    sampler.start()
    torch.cuda.synchronize()
    execution_started = time.perf_counter()

    q_start = _as_batched_tensor(
        bundle.franka.get_qpos(),
        n_envs=n_envs,
        torch=torch,
    )
    q_pregrasp = bundle.franka.inverse_kinematics(
        link=hand,
        pos=pregrasp_positions,
        quat=grasp_quaternions,
    )
    q_pregrasp = _as_batched_tensor(
        q_pregrasp,
        n_envs=n_envs,
        torch=torch,
    )
    reachable &= torch.isfinite(q_pregrasp).all(dim=1)
    q_pregrasp[:, -2:] = finger_open.unsqueeze(1)
    _command_position_trajectory(
        bundle,
        q_start,
        q_pregrasp,
        steps=PARALLEL_FUTURES_PHASE_STEPS["approach"],
        settle_steps=PARALLEL_FUTURES_PHASE_STEPS["approach_settle"],
        recorder=recorder,
    )

    descent_start = pregrasp_positions.clone()
    q_grasp = q_pregrasp
    for step_index in range(1, PARALLEL_FUTURES_PHASE_STEPS["descent"] + 1):
        alpha = step_index / PARALLEL_FUTURES_PHASE_STEPS["descent"]
        descent_position = descent_start + (grasp_positions - descent_start) * alpha
        q_grasp = bundle.franka.inverse_kinematics(
            link=hand,
            pos=descent_position,
            quat=grasp_quaternions,
        )
        q_grasp = _as_batched_tensor(
            q_grasp,
            n_envs=n_envs,
            torch=torch,
        )
        reachable &= torch.isfinite(q_grasp).all(dim=1)
        q_grasp[:, -2:] = finger_open.unsqueeze(1)
        bundle.franka.control_dofs_position(q_grasp)
        bundle.scene.step()
        if step_index % 5 == 0:
            recorder.sample()
    for settle_index in range(
        PARALLEL_FUTURES_PHASE_STEPS["descent_settle"]
    ):
        bundle.franka.control_dofs_position(q_grasp)
        bundle.scene.step()
        if (settle_index + 1) % 5 == 0:
            recorder.sample()

    _command_force_hold(
        bundle,
        q_grasp[:, :7],
        steps=PARALLEL_FUTURES_PHASE_STEPS["close"],
        close_force=profile.close_force,
        recorder=recorder,
        torch=torch,
    )

    lift_positions = grasp_positions.clone()
    lift_positions[:, 2] += REQUESTED_LIFT_HEIGHT_M
    q_lift = bundle.franka.inverse_kinematics(
        link=hand,
        pos=lift_positions,
        quat=grasp_quaternions,
    )
    q_lift = _as_batched_tensor(
        q_lift,
        n_envs=n_envs,
        torch=torch,
    )
    reachable &= torch.isfinite(q_lift).all(dim=1)
    _command_lift(
        bundle,
        q_grasp[:, :7],
        q_lift[:, :7],
        steps=PARALLEL_FUTURES_PHASE_STEPS["lift"],
        settle_steps=PARALLEL_FUTURES_PHASE_STEPS["lift_settle"],
        close_force=profile.close_force,
        recorder=recorder,
        torch=torch,
    )
    recorder.sample()
    torch.cuda.synchronize()
    execution_seconds = time.perf_counter() - execution_started
    telemetry = sampler.stop()

    final_object_positions = _as_batched_tensor(
        pick_entity.get_pos(),
        n_envs=n_envs,
        torch=torch,
    )
    retained_lift = torch.clamp(
        final_object_positions[:, 2] - object_start_positions[:, 2],
        min=0.0,
    )
    stability = torch.clamp(
        retained_lift / REQUESTED_LIFT_HEIGHT_M,
        min=0.0,
        max=1.0,
    )
    clearances = recorder.minimum_clearance
    hard_safe = (
        reachable
        & (clearances >= GATE32_MINIMUM_SAFE_CLEARANCE_M)
        & (stability >= GATE32_MINIMUM_STABILITY)
    )

    clearances_cpu = clearances.detach().cpu().tolist()
    reachable_cpu = reachable.detach().cpu().tolist()
    stability_cpu = stability.detach().cpu().tolist()
    retained_lift_cpu = retained_lift.detach().cpu().tolist()
    path_length_cpu = recorder.path_length.detach().cpu().tolist()
    hard_safe_cpu = hard_safe.detach().cpu().tolist()
    results = []
    for assignment in assignments:
        env_index = assignment.env_index
        results.append(
            {
                "env_index": env_index,
                "candidate_index": assignment.candidate_index,
                "candidate_id": assignment.candidate_id,
                "repeat_index": assignment.repeat_index,
                "minimum_clearance_m": float(clearances_cpu[env_index]),
                "reachable": bool(reachable_cpu[env_index]),
                "retained_lift_height_m": float(
                    retained_lift_cpu[env_index]
                ),
                "predicted_stability": float(stability_cpu[env_index]),
                "path_length_m": float(path_length_cpu[env_index]),
                "hard_safe": bool(hard_safe_cpu[env_index]),
            }
        )

    payload = {
        "schema_version": PARALLEL_FUTURES_SCHEMA_VERSION,
        "report_name": PARALLEL_FUTURES_REPORT_NAME,
        "backend": "genesis_gpu_batched",
        "protocol": protocol,
        "device": {
            "name": torch.cuda.get_device_name(0),
            "torch_version": torch.__version__,
            "hip_version": torch.version.hip,
            "genesis_version": getattr(gs, "__version__", "unknown"),
        },
        "scene_build_seconds": build_seconds,
        "gpu_telemetry": telemetry,
        "results": results,
        "summary": {
            "batched_execution_wall_seconds": execution_seconds,
            "candidate_futures_per_second": n_envs / execution_seconds,
            "hard_safe_future_count": sum(hard_safe_cpu),
            "unsafe_future_count": n_envs - sum(hard_safe_cpu),
            "mean_clearance_m": float(clearances.mean().item()),
            "mean_stability": float(stability.mean().item()),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    validation = validate_parallel_futures_report(payload)
    validation_path = (
        args.validation_output
        or args.output.with_suffix(".validation.json")
    )
    validation_path.write_text(
        json.dumps(validation, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
