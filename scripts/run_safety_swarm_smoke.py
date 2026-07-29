#!/usr/bin/env python3
"""Run a frozen V1 or candidate-selection V2 Safety Swarm Radeon smoke."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from guardian_sim.candidates import generate_obstacle_aware_candidates
from guardian_sim.gate32_benchmark import GATE32_MINIMUM_STABILITY
from guardian_sim.parallel_futures import PARALLEL_FUTURES_PHASE_STEPS
from guardian_sim.reference_motion import candidate_grasp_pose
from guardian_sim.rocm_telemetry import RocmSmiSampler
from guardian_sim.safety_swarm import (
    SafetySwarmMeasurement,
    assemble_safety_swarm_smoke_report,
    build_safety_swarm_matrix,
    build_safety_swarm_smoke_protocol,
    safety_swarm_smoke_world_ids,
    validate_safety_swarm_smoke_report,
)
from guardian_sim.safety_swarm_genesis import (
    build_safety_swarm_placements,
    delayed_trajectory_alphas,
)
from guardian_sim.safety_swarm_v2 import (
    CandidateWorldMeasurement,
    assemble_safety_swarm_v2_smoke_report,
    assign_candidate_worlds,
    build_safety_swarm_v2_smoke_protocol,
    safety_swarm_v2_tier_definition,
    validate_safety_swarm_v2_smoke_report,
)

PICK_OBJECT = "011_banana"
OBSTACLE_OBJECT = "018_plum"
DEFAULT_CANDIDATE_ID = "yaw_+67.5_retreat_+0.000_approach_+0.140"
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
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--world-count", type=int, choices=(4, 16))
    selection.add_argument(
        "--v2-tier",
        choices=("triad-4", "full-4", "full-16"),
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preflight-output", type=Path)
    parser.add_argument("--validation-output", type=Path)
    parser.add_argument("--candidate-id", default=DEFAULT_CANDIDATE_ID)
    return parser


def _refuse_overwrite(paths: tuple[Path, ...]) -> None:
    existing = [str(path) for path in paths if path.exists()]
    if existing:
        raise FileExistsError(
            "Safety Swarm smoke refuses to overwrite existing evidence: "
            + ", ".join(existing)
        )


def _source_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


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


def _topdown_quaternion_wxyz(yaw_degrees: float) -> tuple[float, ...]:
    yaw_half = math.radians(yaw_degrees) / 2.0
    return (0.0, math.cos(yaw_half), math.sin(yaw_half), 0.0)


class _SafetySwarmRecorder:
    """Sample path length, AABB separation, and strict AABB overlap per world."""

    def __init__(self, bundle, *, n_envs: int, torch) -> None:
        self._bundle = bundle
        self._n_envs = n_envs
        self._torch = torch
        self._hand = bundle.franka.get_link("hand")
        self._links = [
            bundle.franka.get_link(name) for name in CLEARANCE_LINK_NAMES
        ]
        self._obstacles = [
            entity
            for name, entity in sorted(bundle.ycb.items())
            if name != PICK_OBJECT
        ]
        device = torch.device("cuda")
        self.minimum_clearance = torch.full(
            (n_envs,),
            math.inf,
            device=device,
            dtype=torch.float32,
        )
        self.clutter_contact = torch.zeros(
            n_envs,
            device=device,
            dtype=torch.bool,
        )
        self.path_length = torch.zeros(
            n_envs,
            device=device,
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
        per_sample_contact = torch.zeros_like(self.clutter_contact)
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
                obstacle_min, obstacle_max = (
                    obstacle_bounds[:, 0],
                    obstacle_bounds[:, 1],
                )
                signed_overlap = torch.minimum(
                    link_max,
                    obstacle_max,
                ) - torch.maximum(link_min, obstacle_min)
                per_sample_contact |= (signed_overlap > 0.0).all(dim=1)
                gaps = torch.maximum(
                    torch.maximum(
                        link_min - obstacle_max,
                        obstacle_min - link_max,
                    ),
                    torch.zeros_like(link_min),
                )
                per_sample = torch.minimum(
                    per_sample,
                    torch.linalg.vector_norm(gaps, dim=1),
                )
        self.minimum_clearance = torch.minimum(
            self.minimum_clearance,
            per_sample,
        )
        self.clutter_contact |= per_sample_contact


def _sampled_step(
    bundle,
    *,
    recorder: _SafetySwarmRecorder,
    step_index: int,
    sample_every: int = 5,
) -> None:
    bundle.scene.step()
    if step_index % sample_every == 0:
        recorder.sample()


def _command_delayed_position_trajectory(
    bundle,
    start,
    goal,
    *,
    delays: tuple[int, ...],
    steps: int,
    settle_steps: int,
    recorder: _SafetySwarmRecorder,
    torch,
) -> None:
    total_steps = steps + max(delays)
    for step_index in range(1, total_steps + 1):
        alphas = torch.tensor(
            delayed_trajectory_alphas(
                delays,
                step_index=step_index,
                trajectory_steps=steps,
            ),
            device=start.device,
            dtype=start.dtype,
        ).unsqueeze(1)
        bundle.franka.control_dofs_position(start + (goal - start) * alphas)
        _sampled_step(
            bundle,
            recorder=recorder,
            step_index=step_index,
        )
    for settle_index in range(1, settle_steps + 1):
        bundle.franka.control_dofs_position(goal)
        _sampled_step(
            bundle,
            recorder=recorder,
            step_index=settle_index,
        )


def _command_force_hold(
    bundle,
    arm_goal,
    *,
    steps: int,
    close_force: float,
    recorder: _SafetySwarmRecorder,
    torch,
) -> None:
    motors = list(range(7))
    fingers = [7, 8]
    finger_force = torch.full(
        (arm_goal.shape[0], 2),
        close_force,
        device=arm_goal.device,
        dtype=arm_goal.dtype,
    )
    for step_index in range(1, steps + 1):
        bundle.franka.control_dofs_position(arm_goal, motors)
        bundle.franka.control_dofs_force(finger_force, fingers)
        _sampled_step(
            bundle,
            recorder=recorder,
            step_index=step_index,
        )


def _command_lift(
    bundle,
    arm_start,
    arm_goal,
    *,
    steps: int,
    settle_steps: int,
    close_force: float,
    recorder: _SafetySwarmRecorder,
    torch,
) -> None:
    motors = list(range(7))
    fingers = [7, 8]
    finger_force = torch.full(
        (arm_goal.shape[0], 2),
        close_force,
        device=arm_goal.device,
        dtype=arm_goal.dtype,
    )
    for step_index in range(1, steps + 1):
        alpha = step_index / steps
        bundle.franka.control_dofs_position(
            arm_start + (arm_goal - arm_start) * alpha,
            motors,
        )
        bundle.franka.control_dofs_force(finger_force, fingers)
        _sampled_step(
            bundle,
            recorder=recorder,
            step_index=step_index,
        )
    for settle_index in range(1, settle_steps + 1):
        bundle.franka.control_dofs_position(arm_goal, motors)
        bundle.franka.control_dofs_force(finger_force, fingers)
        _sampled_step(
            bundle,
            recorder=recorder,
            step_index=settle_index,
        )


def _place_worlds(bundle, placements, *, torch, np, euler_to_quat) -> None:
    n_envs = len(placements)
    target = bundle.ycb[PICK_OBJECT]
    obstacle = bundle.ycb[OBSTACLE_OBJECT]
    target_positions = torch.tensor(
        [placement.target_xyz for placement in placements],
        device=torch.device("cuda"),
        dtype=torch.float32,
    )
    obstacle_positions = torch.tensor(
        [placement.obstacle_xyz for placement in placements],
        device=torch.device("cuda"),
        dtype=torch.float32,
    )
    target_quaternions = torch.tensor(
        [
            euler_to_quat(
                np.array([0.0, 0.0, 35.0 + placement.target_yaw_bias_deg])
            )
            for placement in placements
        ],
        device=torch.device("cuda"),
        dtype=torch.float32,
    )
    target.set_pos(target_positions, zero_velocity=True)
    target.set_quat(target_quaternions, zero_velocity=True)
    obstacle.set_pos(obstacle_positions, zero_velocity=True)

    parking_xy = ((0.66, 0.25), (0.66, -0.25))
    parked = [
        (name, entity)
        for name, entity in sorted(bundle.ycb.items())
        if name not in {PICK_OBJECT, OBSTACLE_OBJECT}
    ]
    if len(parked) > len(parking_xy):
        raise ValueError("Safety Swarm parking layout is incomplete")
    for (name, entity), (x, y) in zip(parked, parking_xy, strict=True):
        del name
        positions = _as_batched_tensor(
            entity.get_pos(),
            n_envs=n_envs,
            torch=torch,
        )
        positions[:, 0] = x
        positions[:, 1] = y
        entity.set_pos(positions, zero_velocity=True)


def main() -> None:
    args = build_parser().parse_args()
    preflight_path = (
        args.preflight_output
        or args.output.with_suffix(".preflight.json")
    )
    validation_path = (
        args.validation_output
        or args.output.with_suffix(".validation.json")
    )
    _refuse_overwrite((args.output, preflight_path, validation_path))

    matrix = build_safety_swarm_matrix()
    v2_mode = args.v2_tier is not None
    if v2_mode:
        candidate_ids, world_ids = safety_swarm_v2_tier_definition(args.v2_tier)
        assignments = assign_candidate_worlds(candidate_ids, world_ids)
        worlds = tuple(matrix[assignment.world_id] for assignment in assignments)
        candidate_ids_by_env = tuple(
            assignment.candidate_id for assignment in assignments
        )
        protocol = build_safety_swarm_v2_smoke_protocol(args.v2_tier)
    else:
        world_ids = safety_swarm_smoke_world_ids(args.world_count)
        worlds = tuple(matrix[world_id] for world_id in world_ids)
        assignments = ()
        candidate_ids_by_env = (args.candidate_id,) * len(worlds)
        protocol = build_safety_swarm_smoke_protocol(args.world_count)
    source_commit = _source_commit()
    preflight = {
        "status": "frozen_before_execution",
        "source_commit": source_commit,
        "mode": "candidate_selection_v2" if v2_mode else "single_candidate_v1",
        "candidate_ids": list(dict.fromkeys(candidate_ids_by_env)),
        "protocol": protocol,
        "assignments": [
            {
                field: getattr(assignment, field)
                for field in assignment.__dataclass_fields__
            }
            for assignment in assignments
        ],
        "worlds": [
            {
                field: getattr(world, field)
                for field in world.__dataclass_fields__
            }
            for world in worlds
        ],
        "output": str(args.output),
    }
    preflight_path.parent.mkdir(parents=True, exist_ok=True)
    preflight_path.write_text(
        json.dumps(preflight, indent=2) + "\n",
        encoding="utf-8",
    )

    import genesis as gs
    import numpy as np
    import torch
    from genesis.utils.geom import euler_to_quat

    from franka_fruit_pick.build_scene import build_scene
    from franka_fruit_pick.grasp_demo import (
        DEFAULT_PROFILE,
        GRASP_PROFILES,
        _grasp_hand_z,
    )
    from franka_fruit_pick.scene_config import FRANKA_QPOS, get_ycb_assets

    if not torch.cuda.is_available() or not torch.version.hip:
        raise RuntimeError("Safety Swarm smoke requires ROCm/HIP PyTorch")

    n_envs = len(worlds)
    gs.init(backend=gs.gpu)
    build_started = time.perf_counter()
    bundle = build_scene(
        n_envs=n_envs,
        add_world_cam=False,
        add_wrist_cam=False,
        add_video_cam=False,
    )
    torch.cuda.synchronize()
    scene_build_seconds = time.perf_counter() - build_started

    assets = get_ycb_assets()
    target_entity = bundle.ycb[PICK_OBJECT]
    obstacle_entity = bundle.ycb[OBSTACLE_OBJECT]
    base_target = _as_batched_tensor(
        target_entity.get_pos(),
        n_envs=n_envs,
        torch=torch,
    )[0].detach().cpu().tolist()
    base_obstacle = _as_batched_tensor(
        obstacle_entity.get_pos(),
        n_envs=n_envs,
        torch=torch,
    )[0].detach().cpu().tolist()
    placements = build_safety_swarm_placements(
        worlds,
        base_target_xyz=tuple(float(value) for value in base_target[:3]),
        target_radius_xy_m=assets[PICK_OBJECT].radius_xy,
        obstacle_radius_xy_m=assets[OBSTACLE_OBJECT].radius_xy,
        obstacle_z_m=float(base_obstacle[2]),
    )
    _place_worlds(
        bundle,
        placements,
        torch=torch,
        np=np,
        euler_to_quat=euler_to_quat,
    )

    hold = torch.as_tensor(
        np.tile(np.asarray(FRANKA_QPOS), (n_envs, 1)),
        device=torch.device("cuda"),
        dtype=torch.float32,
    )
    for _ in range(PARALLEL_FUTURES_PHASE_STEPS["settle"]):
        bundle.franka.control_dofs_position(hold)
        bundle.scene.step()

    actual_targets = _as_batched_tensor(
        target_entity.get_pos(),
        n_envs=n_envs,
        torch=torch,
    ).detach().cpu().tolist()
    actual_obstacles = _as_batched_tensor(
        obstacle_entity.get_pos(),
        n_envs=n_envs,
        torch=torch,
    ).detach().cpu().tolist()
    selected_candidates = []
    for target_position, obstacle_position, candidate_id in zip(
        actual_targets,
        actual_obstacles,
        candidate_ids_by_env,
        strict=True,
    ):
        candidates = generate_obstacle_aware_candidates(
            tuple(float(value) for value in target_position[:3]),
            tuple(float(value) for value in obstacle_position[:3]),
        )
        matches = [
            candidate
            for candidate in candidates
            if candidate.candidate_id == candidate_id
        ]
        if len(matches) != 1:
            raise ValueError(
                f"candidate {candidate_id!r} is not uniquely defined"
            )
        selected_candidates.append(matches[0])

    profile = GRASP_PROFILES.get(PICK_OBJECT, DEFAULT_PROFILE)
    grasp_hand_z = _grasp_hand_z(target_entity, profile)
    grasp_positions = []
    pregrasp_positions = []
    grasp_quaternions = []
    finger_open = []
    for candidate, placement, target_position in zip(
        selected_candidates,
        placements,
        actual_targets,
        strict=True,
    ):
        grasp_target, grasp_yaw = candidate_grasp_pose(
            candidate,
            object_yaw_degrees=(
                35.0 + placement.target_yaw_bias_deg + profile.yaw_offset
            ),
        )
        x = grasp_target[0] + placement.end_effector_bias_xy_m[0]
        y = grasp_target[1] + placement.end_effector_bias_xy_m[1]
        grasp_positions.append((x, y, grasp_hand_z))
        pregrasp_positions.append(
            (
                x,
                y,
                max(
                    grasp_hand_z + 0.04,
                    float(target_position[2]) + candidate.approach_height_m,
                ),
            )
        )
        grasp_quaternions.append(_topdown_quaternion_wxyz(grasp_yaw))
        finger_open.append(min(0.04, candidate.gripper_width_m / 2.0))

    device = torch.device("cuda")
    pregrasp_tensor = torch.tensor(
        pregrasp_positions,
        device=device,
        dtype=torch.float32,
    )
    grasp_tensor = torch.tensor(
        grasp_positions,
        device=device,
        dtype=torch.float32,
    )
    quaternion_tensor = torch.tensor(
        grasp_quaternions,
        device=device,
        dtype=torch.float32,
    )
    finger_tensor = torch.tensor(
        finger_open,
        device=device,
        dtype=torch.float32,
    )
    delays = tuple(
        placement.action_start_delay_steps for placement in placements
    )
    hand = bundle.franka.get_link("hand")
    recorder = _SafetySwarmRecorder(
        bundle,
        n_envs=n_envs,
        torch=torch,
    )
    recorder.sample()
    object_start_positions = _as_batched_tensor(
        target_entity.get_pos(),
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
    q_pregrasp = _as_batched_tensor(
        bundle.franka.inverse_kinematics(
            link=hand,
            pos=pregrasp_tensor,
            quat=quaternion_tensor,
        ),
        n_envs=n_envs,
        torch=torch,
    )
    reachable &= torch.isfinite(q_pregrasp).all(dim=1)
    q_pregrasp[:, -2:] = finger_tensor.unsqueeze(1)
    _command_delayed_position_trajectory(
        bundle,
        q_start,
        q_pregrasp,
        delays=delays,
        steps=PARALLEL_FUTURES_PHASE_STEPS["approach"],
        settle_steps=PARALLEL_FUTURES_PHASE_STEPS["approach_settle"],
        recorder=recorder,
        torch=torch,
    )

    q_grasp = q_pregrasp
    for step_index in range(1, PARALLEL_FUTURES_PHASE_STEPS["descent"] + 1):
        alpha = step_index / PARALLEL_FUTURES_PHASE_STEPS["descent"]
        descent_position = (
            pregrasp_tensor + (grasp_tensor - pregrasp_tensor) * alpha
        )
        q_grasp = _as_batched_tensor(
            bundle.franka.inverse_kinematics(
                link=hand,
                pos=descent_position,
                quat=quaternion_tensor,
            ),
            n_envs=n_envs,
            torch=torch,
        )
        reachable &= torch.isfinite(q_grasp).all(dim=1)
        q_grasp[:, -2:] = finger_tensor.unsqueeze(1)
        bundle.franka.control_dofs_position(q_grasp)
        _sampled_step(
            bundle,
            recorder=recorder,
            step_index=step_index,
        )
    for settle_index in range(
        1,
        PARALLEL_FUTURES_PHASE_STEPS["descent_settle"] + 1,
    ):
        bundle.franka.control_dofs_position(q_grasp)
        _sampled_step(
            bundle,
            recorder=recorder,
            step_index=settle_index,
        )

    _command_force_hold(
        bundle,
        q_grasp[:, :7],
        steps=PARALLEL_FUTURES_PHASE_STEPS["close"],
        close_force=profile.close_force,
        recorder=recorder,
        torch=torch,
    )

    lift_positions = grasp_tensor.clone()
    lift_positions[:, 2] += REQUESTED_LIFT_HEIGHT_M
    q_lift = _as_batched_tensor(
        bundle.franka.inverse_kinematics(
            link=hand,
            pos=lift_positions,
            quat=quaternion_tensor,
        ),
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
        target_entity.get_pos(),
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
    total_steps = (
        PARALLEL_FUTURES_PHASE_STEPS["approach"]
        + max(delays)
        + PARALLEL_FUTURES_PHASE_STEPS["approach_settle"]
        + PARALLEL_FUTURES_PHASE_STEPS["descent"]
        + PARALLEL_FUTURES_PHASE_STEPS["descent_settle"]
        + PARALLEL_FUTURES_PHASE_STEPS["close"]
        + PARALLEL_FUTURES_PHASE_STEPS["lift"]
        + PARALLEL_FUTURES_PHASE_STEPS["lift_settle"]
    )

    clearances = recorder.minimum_clearance.detach().cpu().tolist()
    stabilities = stability.detach().cpu().tolist()
    reachability = reachable.detach().cpu().tolist()
    contacts = recorder.clutter_contact.detach().cpu().tolist()
    device_identity = {
        "name": torch.cuda.get_device_name(0),
        "torch_version": torch.__version__,
        "hip_version": torch.version.hip,
        "genesis_version": getattr(gs, "__version__", "unknown"),
    }
    if v2_mode:
        measurements = [
            CandidateWorldMeasurement(
                candidate_id=assignment.candidate_id,
                world_id=assignment.world_id,
                minimum_clearance_m=float(clearances[index]),
                stability=float(stabilities[index]),
                reachable=bool(reachability[index]),
                task_completed=(
                    bool(reachability[index])
                    and float(stabilities[index]) >= GATE32_MINIMUM_STABILITY
                ),
                clutter_contact=bool(contacts[index]),
                elapsed_environment_steps=total_steps,
            )
            for index, assignment in enumerate(assignments)
        ]
        report = assemble_safety_swarm_v2_smoke_report(
            measurements,
            tier=args.v2_tier,
            wall_seconds=execution_seconds,
            mode="radeon_engineering_smoke",
            source_commit=source_commit,
            backend="genesis_gpu_batched",
            device=device_identity,
            gpu_telemetry=telemetry,
        )
    else:
        measurements = [
            SafetySwarmMeasurement(
                world_id=world.world_id,
                minimum_clearance_m=float(clearances[index]),
                stability=float(stabilities[index]),
                reachable=bool(reachability[index]),
                task_completed=(
                    bool(reachability[index])
                    and float(stabilities[index]) >= GATE32_MINIMUM_STABILITY
                ),
                clutter_contact=bool(contacts[index]),
                elapsed_environment_steps=total_steps,
            )
            for index, world in enumerate(worlds)
        ]
        report = assemble_safety_swarm_smoke_report(
            measurements,
            candidate_id=args.candidate_id,
            wall_seconds=execution_seconds,
            source_commit=source_commit,
            backend="genesis_gpu_batched",
            device=device_identity,
            gpu_telemetry=telemetry,
        )
    report["scene_build_seconds"] = scene_build_seconds
    report["runtime"] = {
        "pick_object": PICK_OBJECT,
        "obstacle_object": OBSTACLE_OBJECT,
        "requested_lift_height_m": REQUESTED_LIFT_HEIGHT_M,
        "measurement_contract": protocol["measurement_contract"],
        "phase_steps": dict(PARALLEL_FUTURES_PHASE_STEPS),
        "maximum_action_delay_steps": max(delays),
    }
    # Runtime provenance is intentionally hashed too.
    if v2_mode:
        from guardian_sim.safety_swarm_v2 import _sha256_json
    else:
        from guardian_sim.safety_swarm import _sha256_json

    report["report_sha256"] = _sha256_json(
        {key: value for key, value in report.items() if key != "report_sha256"}
    )
    if v2_mode:
        validation = validate_safety_swarm_v2_smoke_report(
            report,
            require_radeon=True,
        )
    else:
        validation = validate_safety_swarm_smoke_report(
            report,
            require_radeon=True,
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    validation_path.write_text(
        json.dumps(validation, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
