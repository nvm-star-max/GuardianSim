"""Protocol and portable helpers for batched GuardianSim candidate futures."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass

from guardian_sim.gate32_benchmark import (
    GATE32_MINIMUM_SAFE_CLEARANCE_M,
    GATE32_MINIMUM_STABILITY,
)
from guardian_sim.models import ActionCandidate
from guardian_sim.reference_motion import candidate_grasp_pose

PARALLEL_FUTURES_SCHEMA_VERSION = 1
PARALLEL_FUTURES_REPORT_NAME = "guardiansim-parallel-candidate-futures"
PARALLEL_FUTURES_REPEATS = 3
PARALLEL_FUTURES_PHASE_STEPS = {
    "settle": 60,
    "approach": 140,
    "approach_settle": 20,
    "descent": 80,
    "descent_settle": 15,
    "close": 100,
    "lift": 120,
    "lift_settle": 20,
}


@dataclass(frozen=True, slots=True)
class ParallelFutureAssignment:
    """Map one batched Genesis environment to one candidate/repeat pair."""

    env_index: int
    candidate_index: int
    repeat_index: int
    candidate_id: str


@dataclass(frozen=True, slots=True)
class ParallelFuturePose:
    """Per-environment Cartesian targets for one candidate future."""

    assignment: ParallelFutureAssignment
    grasp_position: tuple[float, float, float]
    pregrasp_position: tuple[float, float, float]
    grasp_quaternion_wxyz: tuple[float, float, float, float]
    finger_open_m: float


def assign_parallel_futures(
    candidates: Sequence[ActionCandidate],
    *,
    repeats: int = PARALLEL_FUTURES_REPEATS,
) -> tuple[ParallelFutureAssignment, ...]:
    """Return a deterministic candidate-major environment assignment."""

    if not candidates:
        raise ValueError("at least one candidate is required")
    if repeats < 1:
        raise ValueError("repeats must be positive")
    candidate_ids = [candidate.candidate_id for candidate in candidates]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("candidate ids must be unique")

    assignments = []
    for candidate_index, candidate in enumerate(candidates):
        for repeat_index in range(repeats):
            assignments.append(
                ParallelFutureAssignment(
                    env_index=len(assignments),
                    candidate_index=candidate_index,
                    repeat_index=repeat_index,
                    candidate_id=candidate.candidate_id,
                )
            )
    return tuple(assignments)


def _topdown_quaternion_wxyz(
    yaw_degrees: float,
) -> tuple[float, float, float, float]:
    """Return Genesis' wxyz quaternion for roll=180, pitch=0, yaw=yaw."""

    yaw_half = math.radians(yaw_degrees) / 2.0
    return (0.0, math.cos(yaw_half), math.sin(yaw_half), 0.0)


def build_parallel_future_poses(
    candidates: Sequence[ActionCandidate],
    *,
    object_yaw_degrees: float,
    object_start_height_m: float,
    grasp_hand_z_m: float,
    repeats: int = PARALLEL_FUTURES_REPEATS,
    maximum_finger_open_m: float = 0.04,
) -> tuple[ParallelFuturePose, ...]:
    """Expand candidate geometry into one Cartesian plan per environment."""

    assignments = assign_parallel_futures(candidates, repeats=repeats)
    poses = []
    for assignment in assignments:
        candidate = candidates[assignment.candidate_index]
        grasp_target, grasp_yaw = candidate_grasp_pose(
            candidate,
            object_yaw_degrees=object_yaw_degrees,
        )
        grasp_position = (
            grasp_target[0],
            grasp_target[1],
            grasp_hand_z_m,
        )
        pregrasp_position = (
            grasp_position[0],
            grasp_position[1],
            max(
                grasp_hand_z_m + 0.04,
                object_start_height_m + candidate.approach_height_m,
            ),
        )
        poses.append(
            ParallelFuturePose(
                assignment=assignment,
                grasp_position=grasp_position,
                pregrasp_position=pregrasp_position,
                grasp_quaternion_wxyz=_topdown_quaternion_wxyz(grasp_yaw),
                finger_open_m=min(
                    maximum_finger_open_m,
                    candidate.gripper_width_m / 2.0,
                ),
            )
        )
    return tuple(poses)


def build_parallel_futures_protocol(
    candidates: Sequence[ActionCandidate],
    *,
    repeats: int = PARALLEL_FUTURES_REPEATS,
    pick_object: str = "011_banana",
    obstacle_object: str = "018_plum",
) -> dict[str, object]:
    """Freeze the engineering-demo execution matrix before observing outcomes."""

    assignments = assign_parallel_futures(candidates, repeats=repeats)
    payload: dict[str, object] = {
        "report_name": PARALLEL_FUTURES_REPORT_NAME,
        "candidate_ids": [candidate.candidate_id for candidate in candidates],
        "candidate_count": len(candidates),
        "repeats_per_candidate": repeats,
        "parallel_environment_count": len(assignments),
        "pick_object": pick_object,
        "obstacle_object": obstacle_object,
        "minimum_safe_clearance_m": GATE32_MINIMUM_SAFE_CLEARANCE_M,
        "minimum_stability": GATE32_MINIMUM_STABILITY,
        "phase_steps": dict(PARALLEL_FUTURES_PHASE_STEPS),
        "execution": (
            "one Genesis scene built with one environment per candidate/repeat; "
            "batched inverse kinematics and GPU-resident control tensors"
        ),
        "evidence_scope": (
            "Engineering throughput and batched-future demonstration. This does not "
            "increase the independent formal safety-evaluation sample count."
        ),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["protocol_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return payload


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return value


def _finite(value: object, label: str) -> float:
    if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{label} must be finite")
    return float(value)


def validate_parallel_futures_report(
    payload: Mapping[str, object],
    *,
    require_telemetry: bool = True,
) -> dict[str, object]:
    """Strictly validate assignment coverage, derived labels, and AMD execution."""

    if payload.get("schema_version") != PARALLEL_FUTURES_SCHEMA_VERSION:
        raise ValueError("unsupported parallel-futures schema")
    if payload.get("report_name") != PARALLEL_FUTURES_REPORT_NAME:
        raise ValueError("unexpected parallel-futures report name")
    if payload.get("backend") != "genesis_gpu_batched":
        raise ValueError("parallel futures did not use the Genesis GPU backend")

    protocol = _mapping(payload.get("protocol"), "protocol")
    protocol_without_hash = {
        key: value for key, value in protocol.items() if key != "protocol_sha256"
    }
    canonical = json.dumps(
        protocol_without_hash,
        sort_keys=True,
        separators=(",", ":"),
    )
    if protocol.get("protocol_sha256") != hashlib.sha256(canonical.encode()).hexdigest():
        raise ValueError("parallel-futures protocol hash mismatch")

    candidate_ids = protocol.get("candidate_ids")
    if not isinstance(candidate_ids, list) or not candidate_ids:
        raise TypeError("protocol.candidate_ids must be a non-empty list")
    repeats = int(protocol.get("repeats_per_candidate", 0))
    expected_envs = len(candidate_ids) * repeats
    if int(protocol.get("parallel_environment_count", 0)) != expected_envs:
        raise ValueError("parallel environment count does not match the matrix")

    device = _mapping(payload.get("device"), "device")
    if "amd" not in str(device.get("name", "")).lower():
        raise ValueError("parallel-futures report does not identify an AMD GPU")
    if not str(device.get("hip_version", "")).strip():
        raise ValueError("parallel-futures report is missing HIP")

    raw_results = payload.get("results")
    if not isinstance(raw_results, list) or len(raw_results) != expected_envs:
        raise ValueError("parallel-futures result count mismatch")
    expected_pairs = {
        (str(candidate_id), repeat_index)
        for candidate_id in candidate_ids
        for repeat_index in range(repeats)
    }
    observed_pairs: set[tuple[str, int]] = set()
    observed_envs: set[int] = set()
    safe_count = 0
    clearance_threshold = float(protocol["minimum_safe_clearance_m"])
    stability_threshold = float(protocol["minimum_stability"])
    for raw_result in raw_results:
        result = _mapping(raw_result, "result")
        pair = (str(result.get("candidate_id")), int(result.get("repeat_index", -1)))
        observed_pairs.add(pair)
        observed_envs.add(int(result.get("env_index", -1)))
        clearance = _finite(
            result.get("minimum_clearance_m"),
            f"{pair} clearance",
        )
        stability = _finite(
            result.get("predicted_stability"),
            f"{pair} stability",
        )
        path_length = _finite(
            result.get("path_length_m"),
            f"{pair} path length",
        )
        if clearance < 0.0 or not 0.0 <= stability <= 1.0 or path_length < 0.0:
            raise ValueError(f"{pair} contains invalid physical metrics")
        reachable = bool(result.get("reachable"))
        expected_safe = (
            reachable
            and clearance >= clearance_threshold
            and stability >= stability_threshold
        )
        if bool(result.get("hard_safe")) != expected_safe:
            raise ValueError(f"{pair} hard-safe label drift")
        safe_count += expected_safe
    if observed_pairs != expected_pairs:
        raise ValueError("candidate/repeat coverage mismatch")
    if observed_envs != set(range(expected_envs)):
        raise ValueError("environment assignment coverage mismatch")

    summary = _mapping(payload.get("summary"), "summary")
    wall_seconds = _finite(
        summary.get("batched_execution_wall_seconds"),
        "batched execution wall seconds",
    )
    if wall_seconds <= 0.0:
        raise ValueError("batched execution wall time must be positive")
    expected_throughput = expected_envs / wall_seconds
    actual_throughput = _finite(
        summary.get("candidate_futures_per_second"),
        "candidate futures per second",
    )
    if not math.isclose(
        actual_throughput,
        expected_throughput,
        rel_tol=1e-9,
        abs_tol=1e-9,
    ):
        raise ValueError("candidate-futures throughput mismatch")
    if int(summary.get("hard_safe_future_count", -1)) != safe_count:
        raise ValueError("hard-safe future count mismatch")

    telemetry = _mapping(payload.get("gpu_telemetry"), "gpu telemetry")
    if require_telemetry and int(telemetry.get("sample_count", 0)) < 1:
        raise ValueError("parallel-futures report has no ROCm telemetry")
    return {
        "status": "passed",
        "schema_version": PARALLEL_FUTURES_SCHEMA_VERSION,
        "protocol_sha256": protocol["protocol_sha256"],
        "parallel_environment_count": expected_envs,
        "hard_safe_future_count": safe_count,
        "candidate_futures_per_second": actual_throughput,
    }


def assignment_dicts(
    assignments: Sequence[ParallelFutureAssignment],
) -> list[dict[str, object]]:
    """Serialize assignments without coupling callers to dataclass details."""

    return [asdict(assignment) for assignment in assignments]
