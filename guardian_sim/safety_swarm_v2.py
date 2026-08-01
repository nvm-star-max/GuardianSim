"""Candidate-selection protocol for Radeon Safety Swarm V2.

V1 evaluates one already-selected candidate across an uncertainty envelope.
V2 adds a candidate dimension without changing the V1 worlds or hard gates:
every candidate is evaluated against the same ordered world subset, and only a
candidate that passes every selected world may be executed.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from functools import lru_cache

from guardian_sim.candidates import OBSTACLE_AWARE_YAWS
from guardian_sim.gate32_benchmark import (
    GATE32_MINIMUM_SAFE_CLEARANCE_M,
    GATE32_MINIMUM_STABILITY,
)
from guardian_sim.safety_swarm import (
    STOP_REASON_ORDER,
    SafetySwarmMeasurement,
    build_safety_swarm_matrix,
    build_safety_swarm_protocol,
    classify_safety_swarm_world,
    safety_swarm_smoke_world_ids,
    safety_swarm_world_asdict,
)

SAFETY_SWARM_V2_SCHEMA_VERSION = 1
SAFETY_SWARM_V2_REPORT_NAME = "radeon-safety-swarm-v2-smoke"
SAFETY_SWARM_V2_FORMAL_REPORT_NAME = "radeon-safety-swarm-v2-formal"
SAFETY_SWARM_V2_FORMAL_CHUNK_REPORT_NAME = (
    "radeon-safety-swarm-v2-formal-chunk"
)
SAFETY_SWARM_V2_RETREAT_DISTANCE_M = 0.025
SAFETY_SWARM_V2_APPROACH_HEIGHT_M = 0.14
SAFETY_SWARM_V2_GRIPPER_WIDTH_M = 0.06
SAFETY_SWARM_V2_FORMAL_BATCH_CHUNK_SIZE = 256

SAFETY_SWARM_V2_TRIAD_CANDIDATE_IDS = (
    "yaw_+00.0_offset_+0.000",
    "yaw_+67.5_retreat_+0.000_approach_+0.140",
    "yaw_+67.5_retreat_+0.025_approach_+0.140",
)


@dataclass(frozen=True, slots=True)
class SafetySwarmCandidate:
    """One action in the frozen obstacle-aware candidate catalog."""

    candidate_index: int
    candidate_id: str
    yaw_degrees: float
    retreat_distance_m: float
    approach_height_m: float
    gripper_width_m: float


@dataclass(frozen=True, slots=True)
class CandidateWorldAssignment:
    """Map one environment to a candidate and one frozen uncertainty world."""

    env_index: int
    candidate_index: int
    candidate_id: str
    world_id: int


@dataclass(frozen=True, slots=True)
class CandidateWorldMeasurement:
    """Raw physical measurements for one candidate-world pair."""

    candidate_id: str
    world_id: int
    minimum_clearance_m: float
    stability: float
    reachable: bool
    task_completed: bool
    clutter_contact: bool
    elapsed_environment_steps: int


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode()).hexdigest()


def _finite(value: object, label: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
    ):
        raise ValueError(f"{label} must be finite")
    return float(value)


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return value


def _percentile(values: Sequence[float], percentile: float) -> float:
    if not values:
        raise ValueError("percentile requires values")
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


@lru_cache(maxsize=1)
def _frozen_world_matrix():
    return build_safety_swarm_matrix()


def build_safety_swarm_v2_candidate_catalog() -> tuple[SafetySwarmCandidate, ...]:
    """Return the original Gate 3.2 obstacle-aware 18-action family."""

    catalog: list[SafetySwarmCandidate] = []
    for yaw in OBSTACLE_AWARE_YAWS:
        centered_id = (
            "yaw_+00.0_offset_+0.000"
            if yaw == 0.0
            else (
                f"yaw_{yaw:+05.1f}_retreat_+0.000"
                f"_approach_{SAFETY_SWARM_V2_APPROACH_HEIGHT_M:+.3f}"
            )
        )
        catalog.append(
            SafetySwarmCandidate(
                candidate_index=len(catalog),
                candidate_id=centered_id,
                yaw_degrees=yaw,
                retreat_distance_m=0.0,
                approach_height_m=(
                    0.10 if yaw == 0.0 else SAFETY_SWARM_V2_APPROACH_HEIGHT_M
                ),
                gripper_width_m=SAFETY_SWARM_V2_GRIPPER_WIDTH_M,
            )
        )
        catalog.append(
            SafetySwarmCandidate(
                candidate_index=len(catalog),
                candidate_id=(
                    f"yaw_{yaw:+05.1f}"
                    f"_retreat_{SAFETY_SWARM_V2_RETREAT_DISTANCE_M:+.3f}"
                    f"_approach_{SAFETY_SWARM_V2_APPROACH_HEIGHT_M:+.3f}"
                ),
                yaw_degrees=yaw,
                retreat_distance_m=SAFETY_SWARM_V2_RETREAT_DISTANCE_M,
                approach_height_m=SAFETY_SWARM_V2_APPROACH_HEIGHT_M,
                gripper_width_m=SAFETY_SWARM_V2_GRIPPER_WIDTH_M,
            )
        )
    if len(catalog) != 18:
        raise AssertionError("Safety Swarm V2 candidate catalog must contain 18 actions")
    if len({candidate.candidate_id for candidate in catalog}) != len(catalog):
        raise AssertionError("Safety Swarm V2 candidate ids must be unique")
    return tuple(catalog)


def safety_swarm_v2_candidate_catalog_sha256() -> str:
    return _sha256_json(
        [asdict(candidate) for candidate in build_safety_swarm_v2_candidate_catalog()]
    )


def safety_swarm_v2_tier_definition(tier: str) -> tuple[tuple[str, ...], tuple[int, ...]]:
    """Return the predeclared candidate and world ids for a smoke tier."""

    catalog_ids = tuple(
        candidate.candidate_id
        for candidate in build_safety_swarm_v2_candidate_catalog()
    )
    tiers = {
        "triad-4": (
            SAFETY_SWARM_V2_TRIAD_CANDIDATE_IDS,
            safety_swarm_smoke_world_ids(4),
        ),
        "full-4": (catalog_ids, safety_swarm_smoke_world_ids(4)),
        "full-16": (catalog_ids, safety_swarm_smoke_world_ids(16)),
    }
    try:
        return tiers[tier]
    except KeyError as error:
        raise ValueError(
            "Safety Swarm V2 tier must be triad-4, full-4, or full-16"
        ) from error


def assign_candidate_worlds(
    candidate_ids: Sequence[str],
    world_ids: Sequence[int],
) -> tuple[CandidateWorldAssignment, ...]:
    """Return a deterministic candidate-major Cartesian assignment."""

    if not candidate_ids or not world_ids:
        raise ValueError("candidate_ids and world_ids must be non-empty")
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("candidate ids must be unique")
    if len(world_ids) != len(set(world_ids)):
        raise ValueError("world ids must be unique")
    catalog_ids = {
        candidate.candidate_id
        for candidate in build_safety_swarm_v2_candidate_catalog()
    }
    unknown = set(candidate_ids) - catalog_ids
    if unknown:
        raise ValueError(f"unknown Safety Swarm V2 candidates: {sorted(unknown)}")
    if any(world_id < 0 or world_id >= 256 for world_id in world_ids):
        raise ValueError("world ids must reference the frozen 256-world matrix")

    assignments: list[CandidateWorldAssignment] = []
    for candidate_index, candidate_id in enumerate(candidate_ids):
        for world_id in world_ids:
            assignments.append(
                CandidateWorldAssignment(
                    env_index=len(assignments),
                    candidate_index=candidate_index,
                    candidate_id=candidate_id,
                    world_id=int(world_id),
                )
            )
    return tuple(assignments)


def safety_swarm_v2_formal_chunk_assignments(
    chunk_index: int,
) -> tuple[CandidateWorldAssignment, ...]:
    """Return one frozen 256-world formal chunk for a single candidate."""

    catalog = build_safety_swarm_v2_candidate_catalog()
    if chunk_index < 0 or chunk_index >= len(catalog):
        raise ValueError("formal chunk index must be between 0 and 17")
    candidate = catalog[chunk_index]
    offset = chunk_index * SAFETY_SWARM_V2_FORMAL_BATCH_CHUNK_SIZE
    return tuple(
        CandidateWorldAssignment(
            env_index=offset + world_id,
            candidate_index=chunk_index,
            candidate_id=candidate.candidate_id,
            world_id=world_id,
        )
        for world_id in range(SAFETY_SWARM_V2_FORMAL_BATCH_CHUNK_SIZE)
    )


def build_safety_swarm_v2_formal_protocol() -> dict[str, object]:
    """Freeze the full 18 x 256 candidate-selection protocol."""

    catalog = build_safety_swarm_v2_candidate_catalog()
    v1 = build_safety_swarm_protocol()
    candidate_world_count = len(catalog) * int(v1["world_count"])
    protocol: dict[str, object] = {
        "report_name": SAFETY_SWARM_V2_FORMAL_REPORT_NAME,
        "candidate_catalog": [asdict(candidate) for candidate in catalog],
        "candidate_catalog_sha256": safety_swarm_v2_candidate_catalog_sha256(),
        "candidate_ids": [candidate.candidate_id for candidate in catalog],
        "candidate_count": len(catalog),
        "world_ids": list(range(int(v1["world_count"]))),
        "world_count_per_candidate": int(v1["world_count"]),
        "candidate_world_count": candidate_world_count,
        "assignment_order": "candidate_major_then_world_id",
        "execution_plan": {
            "maximum_environments_per_batch": SAFETY_SWARM_V2_FORMAL_BATCH_CHUNK_SIZE,
            "deterministic_chunk_order": "contiguous_assignment_prefix",
            "required_complete_assignment_count": candidate_world_count,
        },
        "v1_formal_protocol_sha256": v1["protocol_sha256"],
        "v1_world_matrix_sha256": v1["matrix_sha256"],
        "minimum_safe_clearance_m": GATE32_MINIMUM_SAFE_CLEARANCE_M,
        "minimum_stability": GATE32_MINIMUM_STABILITY,
        "maximum_contact_world_count_per_candidate": 0,
        "qualification_rule": (
            "candidate_must_pass_every_one_of_256_worlds_with_zero_contacts"
        ),
        "selection_order": [
            "highest_worst_case_clearance_m",
            "highest_fifth_percentile_clearance_m",
            "highest_minimum_stability",
            "lowest_candidate_index",
        ],
        "unsafe_policy": "execute_best_qualified_candidate_else_safe_stop",
        "evidence_scope": (
            "Candidate-by-uncertainty engineering stress test on Radeon. "
            "The 4,608 candidate-world pairs are not independent formal "
            "robot scenarios and do not establish physical-robot safety."
        ),
    }
    protocol["protocol_sha256"] = _sha256_json(protocol)
    return protocol


def build_safety_swarm_v2_smoke_protocol(tier: str) -> dict[str, object]:
    """Freeze a partial V2 smoke while retaining the full formal identity."""

    candidate_ids, world_ids = safety_swarm_v2_tier_definition(tier)
    assignments = assign_candidate_worlds(candidate_ids, world_ids)
    formal = build_safety_swarm_v2_formal_protocol()
    protocol: dict[str, object] = {
        "report_name": SAFETY_SWARM_V2_REPORT_NAME,
        "tier": tier,
        "candidate_ids": list(candidate_ids),
        "candidate_count": len(candidate_ids),
        "world_ids": list(world_ids),
        "world_count_per_candidate": len(world_ids),
        "candidate_world_count": len(assignments),
        "assignment_order": "candidate_major_then_world_id",
        "formal_report_name": SAFETY_SWARM_V2_FORMAL_REPORT_NAME,
        "formal_protocol_sha256": formal["protocol_sha256"],
        "candidate_catalog_sha256": formal["candidate_catalog_sha256"],
        "v1_formal_protocol_sha256": formal["v1_formal_protocol_sha256"],
        "v1_world_matrix_sha256": formal["v1_world_matrix_sha256"],
        "minimum_safe_clearance_m": GATE32_MINIMUM_SAFE_CLEARANCE_M,
        "minimum_stability": GATE32_MINIMUM_STABILITY,
        "maximum_contact_world_count_per_candidate": 0,
        "measurement_contract": {
            "minimum_clearance": (
                "minimum sampled AABB separation across declared robot links "
                "and non-target YCB clutter"
            ),
            "clutter_contact": (
                "strict positive AABB overlap at a five-step sample or phase "
                "endpoint"
            ),
            "stability": (
                "retained target lift divided by the requested 0.10 m lift, "
                "clamped to [0, 1]"
            ),
            "task_completed": (
                "reachable and stability at or above the frozen minimum"
            ),
            "elapsed_environment_steps": (
                "global batched control steps from approach start through lift "
                "settle, including the maximum declared start delay"
            ),
        },
        "qualification_rule": (
            "candidate_must_pass_every_selected_world_with_zero_contacts"
        ),
        "selection_order": list(formal["selection_order"]),
        "unsafe_policy": "execute_best_qualified_candidate_else_safe_stop",
        "evidence_scope": (
            "Partial Radeon executor and selection validation only. It cannot "
            "replace or be merged into the full 18 x 256 formal report."
        ),
    }
    protocol["protocol_sha256"] = _sha256_json(protocol)
    return protocol


def _measurement_from_mapping(
    value: Mapping[str, object] | CandidateWorldMeasurement,
) -> CandidateWorldMeasurement:
    if isinstance(value, CandidateWorldMeasurement):
        return value
    return CandidateWorldMeasurement(
        candidate_id=str(value["candidate_id"]),
        world_id=int(value["world_id"]),
        minimum_clearance_m=_finite(
            value["minimum_clearance_m"],
            "minimum_clearance_m",
        ),
        stability=_finite(value["stability"], "stability"),
        reachable=bool(value["reachable"]),
        task_completed=bool(value["task_completed"]),
        clutter_contact=bool(value["clutter_contact"]),
        elapsed_environment_steps=int(value["elapsed_environment_steps"]),
    )


def classify_candidate_world(
    assignment: CandidateWorldAssignment,
    measurement: CandidateWorldMeasurement,
) -> dict[str, object]:
    """Classify one candidate-world pair with the unchanged V1 hard gates."""

    if assignment.candidate_id != measurement.candidate_id:
        raise ValueError("measurement candidate_id does not match assignment")
    if assignment.world_id != measurement.world_id:
        raise ValueError("measurement world_id does not match assignment")
    world = _frozen_world_matrix()[assignment.world_id]
    classified = classify_safety_swarm_world(
        world,
        SafetySwarmMeasurement(
            world_id=measurement.world_id,
            minimum_clearance_m=measurement.minimum_clearance_m,
            stability=measurement.stability,
            reachable=measurement.reachable,
            task_completed=measurement.task_completed,
            clutter_contact=measurement.clutter_contact,
            elapsed_environment_steps=measurement.elapsed_environment_steps,
        ),
    )
    return {
        "env_index": assignment.env_index,
        "candidate_index": assignment.candidate_index,
        "candidate_id": assignment.candidate_id,
        "world_id": assignment.world_id,
        "perturbation": classified["perturbation"],
        "measurement": asdict(measurement),
        "costs": classified["costs"],
        "hard_safe": classified["hard_safe"],
        "primary_stop_reason": classified["primary_stop_reason"],
        "failed_gates": classified["failed_gates"],
    }


def summarize_candidate_selection(
    results: Sequence[Mapping[str, object]],
    *,
    protocol: Mapping[str, object],
    wall_seconds: float,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Build per-candidate envelopes and the execute-or-stop decision."""

    if wall_seconds <= 0.0 or not math.isfinite(wall_seconds):
        raise ValueError("wall_seconds must be positive and finite")
    candidate_ids = [str(value) for value in protocol["candidate_ids"]]
    worlds_per_candidate = int(protocol["world_count_per_candidate"])
    expected_count = len(candidate_ids) * worlds_per_candidate
    if len(results) != expected_count:
        raise ValueError("candidate-world result count mismatch")

    candidate_summaries: list[dict[str, object]] = []
    for candidate_index, candidate_id in enumerate(candidate_ids):
        candidate_results = [
            result
            for result in results
            if result["candidate_id"] == candidate_id
        ]
        if len(candidate_results) != worlds_per_candidate:
            raise ValueError(f"{candidate_id} world coverage mismatch")
        measurements = [
            _mapping(result["measurement"], "measurement")
            for result in candidate_results
        ]
        clearances = [
            _finite(value["minimum_clearance_m"], "minimum_clearance_m")
            for value in measurements
        ]
        stabilities = [
            _finite(value["stability"], "stability") for value in measurements
        ]
        safe_count = sum(bool(result["hard_safe"]) for result in candidate_results)
        contacts = sum(bool(value["clutter_contact"]) for value in measurements)
        histogram = Counter(
            str(result["primary_stop_reason"]) for result in candidate_results
        )
        candidate_summaries.append(
            {
                "candidate_index": candidate_index,
                "candidate_id": candidate_id,
                "qualifies": (
                    safe_count == worlds_per_candidate and contacts == 0
                ),
                "safe_world_count": safe_count,
                "unsafe_world_count": worlds_per_candidate - safe_count,
                "contact_world_count": contacts,
                "worst_case_clearance_m": min(clearances),
                "fifth_percentile_clearance_m": _percentile(clearances, 0.05),
                "minimum_stability": min(stabilities),
                "failure_histogram": {
                    reason: histogram.get(reason, 0)
                    for reason in ("safe", *STOP_REASON_ORDER)
                },
            }
        )

    qualified = [summary for summary in candidate_summaries if summary["qualifies"]]
    ranked = sorted(
        qualified,
        key=lambda summary: (
            -float(summary["worst_case_clearance_m"]),
            -float(summary["fifth_percentile_clearance_m"]),
            -float(summary["minimum_stability"]),
            int(summary["candidate_index"]),
        ),
    )
    selected = ranked[0]["candidate_id"] if ranked else None
    total_steps = sum(
        int(_mapping(result["measurement"], "measurement")["elapsed_environment_steps"])
        for result in results
    )
    summary = {
        "smoke_status": "passed" if selected is not None else "failed",
        "decision": "execute" if selected is not None else "safe_stop",
        "selected_candidate_id": selected,
        "qualifying_candidate_ids": [
            str(candidate["candidate_id"]) for candidate in ranked
        ],
        "candidate_count": len(candidate_ids),
        "world_count_per_candidate": worlds_per_candidate,
        "candidate_world_count": expected_count,
        "safe_candidate_world_count": sum(
            int(candidate["safe_world_count"]) for candidate in candidate_summaries
        ),
        "contact_candidate_world_count": sum(
            int(candidate["contact_world_count"]) for candidate in candidate_summaries
        ),
        "batched_execution_wall_seconds": wall_seconds,
        "total_environment_steps": total_steps,
        "candidate_worlds_per_second": expected_count / wall_seconds,
        "environment_steps_per_second": total_steps / wall_seconds,
    }
    return candidate_summaries, summary


def assemble_safety_swarm_v2_smoke_report(
    measurements: Sequence[Mapping[str, object] | CandidateWorldMeasurement],
    *,
    tier: str,
    wall_seconds: float,
    mode: str,
    backend: str,
    source_commit: str,
    device: Mapping[str, object] | None = None,
    gpu_telemetry: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Assemble a hashed offline fixture or Radeon V2 smoke report."""

    if mode not in {"offline_fixture", "radeon_engineering_smoke"}:
        raise ValueError("mode must be offline_fixture or radeon_engineering_smoke")
    protocol = build_safety_swarm_v2_smoke_protocol(tier)
    assignments = assign_candidate_worlds(
        [str(value) for value in protocol["candidate_ids"]],
        [int(value) for value in protocol["world_ids"]],
    )
    parsed = [_measurement_from_mapping(value) for value in measurements]
    if len(parsed) != len(assignments):
        raise ValueError("V2 smoke measurement count mismatch")
    results = [
        classify_candidate_world(assignment, measurement)
        for assignment, measurement in zip(assignments, parsed, strict=True)
    ]
    candidate_summaries, summary = summarize_candidate_selection(
        results,
        protocol=protocol,
        wall_seconds=wall_seconds,
    )
    payload: dict[str, object] = {
        "schema_version": SAFETY_SWARM_V2_SCHEMA_VERSION,
        "report_name": SAFETY_SWARM_V2_REPORT_NAME,
        "mode": mode,
        "tier": tier,
        "backend": backend,
        "evidence_status": (
            "ui_validation_only"
            if mode == "offline_fixture"
            else "partial_executor_validation"
        ),
        "showcase_ready": False,
        "claim_boundary": protocol["evidence_scope"],
        "source": {"commit": source_commit},
        "protocol": protocol,
        "device": dict(device or {}),
        "gpu_telemetry": dict(gpu_telemetry or {}),
        "results": results,
        "candidate_summaries": candidate_summaries,
        "summary": summary,
    }
    payload["report_sha256"] = _sha256_json(payload)
    validate_safety_swarm_v2_smoke_report(
        payload,
        require_radeon=mode == "radeon_engineering_smoke",
    )
    return payload


def _validate_radeon_identity(
    payload: Mapping[str, object],
    *,
    label: str,
) -> tuple[Mapping[str, object], Mapping[str, object], str]:
    source = _mapping(payload.get("source"), "source")
    commit = str(source.get("commit", ""))
    if len(commit) < 7 or any(
        character not in "0123456789abcdef" for character in commit
    ):
        raise ValueError(f"{label} requires a Git commit")
    if payload.get("backend") != "genesis_gpu_batched":
        raise ValueError(f"{label} requires Genesis GPU batching")
    device = _mapping(payload.get("device"), "device")
    if "amd" not in str(device.get("name", "")).lower():
        raise ValueError(f"{label} does not identify an AMD GPU")
    if not str(device.get("hip_version", "")).strip():
        raise ValueError(f"{label} is missing HIP")
    telemetry = _mapping(payload.get("gpu_telemetry"), "gpu_telemetry")
    if int(telemetry.get("sample_count", 0)) < 1:
        raise ValueError(f"{label} has no ROCm telemetry")
    for field in (
        "mean_gpu_utilization_pct",
        "max_gpu_utilization_pct",
        "max_vram_used_bytes",
        "total_vram_bytes",
    ):
        if _finite(telemetry.get(field), field) < 0.0:
            raise ValueError(f"{label} has invalid {field}")
    if not isinstance(telemetry.get("sampling_errors"), list):
        raise TypeError(f"{label} has invalid telemetry errors")
    return device, telemetry, commit


def assemble_safety_swarm_v2_formal_chunk_report(
    measurements: Sequence[Mapping[str, object] | CandidateWorldMeasurement],
    *,
    chunk_index: int,
    wall_seconds: float,
    source_commit: str,
    backend: str,
    device: Mapping[str, object],
    gpu_telemetry: Mapping[str, object],
) -> dict[str, object]:
    """Assemble one independently hashed 256-world formal execution chunk."""

    protocol = build_safety_swarm_v2_formal_protocol()
    assignments = safety_swarm_v2_formal_chunk_assignments(chunk_index)
    parsed = [_measurement_from_mapping(value) for value in measurements]
    if len(parsed) != len(assignments):
        raise ValueError("formal chunk measurement count mismatch")
    results = [
        classify_candidate_world(assignment, measurement)
        for assignment, measurement in zip(assignments, parsed, strict=True)
    ]
    payload: dict[str, object] = {
        "schema_version": SAFETY_SWARM_V2_SCHEMA_VERSION,
        "report_name": SAFETY_SWARM_V2_FORMAL_CHUNK_REPORT_NAME,
        "mode": "radeon_formal_chunk",
        "backend": backend,
        "evidence_status": "formal_chunk_not_standalone_evidence",
        "showcase_ready": False,
        "claim_boundary": protocol["evidence_scope"],
        "source": {"commit": source_commit},
        "formal_protocol_sha256": protocol["protocol_sha256"],
        "chunk": {
            "chunk_index": chunk_index,
            "assignment_start": assignments[0].env_index,
            "assignment_end_exclusive": assignments[-1].env_index + 1,
            "candidate_index": assignments[0].candidate_index,
            "candidate_id": assignments[0].candidate_id,
            "world_ids": list(range(SAFETY_SWARM_V2_FORMAL_BATCH_CHUNK_SIZE)),
            "candidate_world_count": len(assignments),
        },
        "device": dict(device),
        "gpu_telemetry": dict(gpu_telemetry),
        "batched_execution_wall_seconds": wall_seconds,
        "results": results,
    }
    payload["report_sha256"] = _sha256_json(payload)
    validate_safety_swarm_v2_formal_chunk_report(payload, require_radeon=True)
    return payload


def validate_safety_swarm_v2_formal_chunk_report(
    payload: Mapping[str, object],
    *,
    require_radeon: bool = False,
) -> dict[str, object]:
    """Strictly validate one exact contiguous formal chunk."""

    if payload.get("schema_version") != SAFETY_SWARM_V2_SCHEMA_VERSION:
        raise ValueError("unsupported Safety Swarm V2 schema")
    if payload.get("report_name") != SAFETY_SWARM_V2_FORMAL_CHUNK_REPORT_NAME:
        raise ValueError("unexpected Safety Swarm V2 formal chunk report name")
    if payload.get("mode") != "radeon_formal_chunk":
        raise ValueError("unexpected Safety Swarm V2 formal chunk mode")
    if payload.get("evidence_status") != "formal_chunk_not_standalone_evidence":
        raise ValueError("formal chunk evidence status mismatch")
    if bool(payload.get("showcase_ready")):
        raise ValueError("formal chunk cannot be showcase-ready")

    protocol = build_safety_swarm_v2_formal_protocol()
    if payload.get("formal_protocol_sha256") != protocol["protocol_sha256"]:
        raise ValueError("formal chunk protocol mismatch")
    if payload.get("claim_boundary") != protocol["evidence_scope"]:
        raise ValueError("formal chunk claim boundary mismatch")

    chunk = _mapping(payload.get("chunk"), "chunk")
    chunk_index = int(chunk.get("chunk_index", -1))
    assignments = safety_swarm_v2_formal_chunk_assignments(chunk_index)
    expected_chunk = {
        "chunk_index": chunk_index,
        "assignment_start": assignments[0].env_index,
        "assignment_end_exclusive": assignments[-1].env_index + 1,
        "candidate_index": assignments[0].candidate_index,
        "candidate_id": assignments[0].candidate_id,
        "world_ids": list(range(SAFETY_SWARM_V2_FORMAL_BATCH_CHUNK_SIZE)),
        "candidate_world_count": len(assignments),
    }
    if chunk != expected_chunk:
        raise ValueError("formal chunk assignment metadata mismatch")

    raw_results = payload.get("results")
    if not isinstance(raw_results, list) or len(raw_results) != len(assignments):
        raise ValueError("formal chunk result count mismatch")
    for assignment, raw_result in zip(assignments, raw_results, strict=True):
        result = _mapping(raw_result, f"formal result {assignment.env_index}")
        measurement = _measurement_from_mapping(
            _mapping(result.get("measurement"), "measurement")
        )
        rebuilt = classify_candidate_world(assignment, measurement)
        if result != rebuilt:
            raise ValueError(
                f"formal environment {assignment.env_index} label drift"
            )

    wall_seconds = _finite(
        payload.get("batched_execution_wall_seconds"),
        "batched_execution_wall_seconds",
    )
    if wall_seconds <= 0.0:
        raise ValueError("batched_execution_wall_seconds must be positive")
    if require_radeon:
        _validate_radeon_identity(payload, label="Radeon V2 formal chunk")

    without_hash = {
        key: value for key, value in payload.items() if key != "report_sha256"
    }
    if payload.get("report_sha256") != _sha256_json(without_hash):
        raise ValueError("Safety Swarm V2 formal chunk hash mismatch")
    return {
        "status": "passed",
        "schema_version": SAFETY_SWARM_V2_SCHEMA_VERSION,
        "mode": "radeon_formal_chunk",
        "formal_protocol_sha256": protocol["protocol_sha256"],
        "chunk_index": chunk_index,
        "candidate_id": assignments[0].candidate_id,
        "candidate_world_count": len(assignments),
        "showcase_ready": False,
        "report_sha256": payload["report_sha256"],
    }


def _aggregate_gpu_telemetry(
    chunks: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    telemetry_values = [
        _mapping(chunk.get("gpu_telemetry"), "gpu_telemetry")
        for chunk in chunks
    ]
    sample_counts = [int(value["sample_count"]) for value in telemetry_values]
    total_samples = sum(sample_counts)
    if total_samples < 1:
        raise ValueError("formal report has no ROCm telemetry")
    mean_utilization = sum(
        float(value["mean_gpu_utilization_pct"]) * sample_count
        for value, sample_count in zip(
            telemetry_values,
            sample_counts,
            strict=True,
        )
    ) / total_samples
    total_vram_values = {
        float(value["total_vram_bytes"]) for value in telemetry_values
    }
    if len(total_vram_values) != 1:
        raise ValueError("formal chunks disagree on total VRAM")
    return {
        "sample_count": total_samples,
        "mean_gpu_utilization_pct": mean_utilization,
        "max_gpu_utilization_pct": max(
            float(value["max_gpu_utilization_pct"])
            for value in telemetry_values
        ),
        "max_vram_used_bytes": max(
            float(value["max_vram_used_bytes"]) for value in telemetry_values
        ),
        "total_vram_bytes": total_vram_values.pop(),
        "sampling_errors": [
            error
            for value in telemetry_values
            for error in value.get("sampling_errors", [])
        ],
    }


def assemble_safety_swarm_v2_formal_report(
    chunks: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Aggregate all 18 validated chunks into the sole formal report."""

    protocol = build_safety_swarm_v2_formal_protocol()
    expected_chunk_count = int(protocol["candidate_count"])
    if len(chunks) != expected_chunk_count:
        raise ValueError("formal report requires all 18 chunks")

    validated_chunks: list[Mapping[str, object]] = []
    for expected_index, chunk in enumerate(chunks):
        validation = validate_safety_swarm_v2_formal_chunk_report(
            chunk,
            require_radeon=True,
        )
        if validation["chunk_index"] != expected_index:
            raise ValueError("formal chunks must be supplied in frozen order")
        validated_chunks.append(chunk)

    first_device, _, first_commit = _validate_radeon_identity(
        validated_chunks[0],
        label="Radeon V2 formal chunk",
    )
    for chunk in validated_chunks[1:]:
        device, _, commit = _validate_radeon_identity(
            chunk,
            label="Radeon V2 formal chunk",
        )
        if device != first_device:
            raise ValueError("formal chunks disagree on device identity")
        if commit != first_commit:
            raise ValueError("formal chunks disagree on source commit")

    results = [
        result
        for chunk in validated_chunks
        for result in chunk["results"]
    ]
    wall_seconds = sum(
        _finite(
            chunk["batched_execution_wall_seconds"],
            "batched_execution_wall_seconds",
        )
        for chunk in validated_chunks
    )
    candidate_summaries, summary = summarize_candidate_selection(
        results,
        protocol=protocol,
        wall_seconds=wall_seconds,
    )
    summary["formal_status"] = summary.pop("smoke_status")
    payload: dict[str, object] = {
        "schema_version": SAFETY_SWARM_V2_SCHEMA_VERSION,
        "report_name": SAFETY_SWARM_V2_FORMAL_REPORT_NAME,
        "mode": "radeon_formal",
        "backend": "genesis_gpu_batched",
        "evidence_status": "complete_formal_candidate_selection",
        "showcase_ready": True,
        "claim_boundary": protocol["evidence_scope"],
        "source": {"commit": first_commit},
        "protocol": protocol,
        "device": dict(first_device),
        "gpu_telemetry": _aggregate_gpu_telemetry(validated_chunks),
        "chunk_receipts": [
            {
                "chunk_index": index,
                "candidate_id": chunk["chunk"]["candidate_id"],
                "candidate_world_count": chunk["chunk"]["candidate_world_count"],
                "source_commit": chunk["source"]["commit"],
                "device_sha256": _sha256_json(chunk["device"]),
                "batched_execution_wall_seconds": chunk[
                    "batched_execution_wall_seconds"
                ],
                "scene_build_seconds": chunk.get("scene_build_seconds"),
                "gpu_telemetry": chunk["gpu_telemetry"],
                "report_sha256": chunk["report_sha256"],
            }
            for index, chunk in enumerate(validated_chunks)
        ],
        "results": results,
        "candidate_summaries": candidate_summaries,
        "summary": summary,
    }
    scene_build_values = [
        chunk.get("scene_build_seconds") for chunk in validated_chunks
    ]
    if all(value is not None for value in scene_build_values):
        payload["total_scene_build_seconds"] = sum(
            _finite(value, "scene_build_seconds") for value in scene_build_values
        )
    payload["report_sha256"] = _sha256_json(payload)
    validate_safety_swarm_v2_formal_report(payload, require_radeon=True)
    return payload


def validate_safety_swarm_v2_formal_report(
    payload: Mapping[str, object],
    *,
    require_radeon: bool = False,
) -> dict[str, object]:
    """Strictly reconstruct the complete 4,608-pair formal selection report."""

    if payload.get("schema_version") != SAFETY_SWARM_V2_SCHEMA_VERSION:
        raise ValueError("unsupported Safety Swarm V2 schema")
    if payload.get("report_name") != SAFETY_SWARM_V2_FORMAL_REPORT_NAME:
        raise ValueError("unexpected Safety Swarm V2 formal report name")
    if payload.get("mode") != "radeon_formal":
        raise ValueError("unexpected Safety Swarm V2 formal mode")
    if payload.get("evidence_status") != "complete_formal_candidate_selection":
        raise ValueError("formal report evidence status mismatch")
    if not bool(payload.get("showcase_ready")):
        raise ValueError("complete formal report must be showcase-ready")

    protocol = build_safety_swarm_v2_formal_protocol()
    if payload.get("protocol") != protocol:
        raise ValueError("Safety Swarm V2 formal protocol mismatch")
    if payload.get("claim_boundary") != protocol["evidence_scope"]:
        raise ValueError("Safety Swarm V2 formal claim boundary mismatch")
    if require_radeon:
        _validate_radeon_identity(payload, label="Radeon V2 formal report")

    candidate_ids = [str(value) for value in protocol["candidate_ids"]]
    world_ids = [int(value) for value in protocol["world_ids"]]
    assignments = assign_candidate_worlds(candidate_ids, world_ids)
    raw_results = payload.get("results")
    if not isinstance(raw_results, list) or len(raw_results) != len(assignments):
        raise ValueError("Safety Swarm V2 formal result count mismatch")
    rebuilt_results: list[dict[str, object]] = []
    for assignment, raw_result in zip(assignments, raw_results, strict=True):
        result = _mapping(raw_result, f"formal result {assignment.env_index}")
        measurement = _measurement_from_mapping(
            _mapping(result.get("measurement"), "measurement")
        )
        rebuilt = classify_candidate_world(assignment, measurement)
        if result != rebuilt:
            raise ValueError(
                f"formal environment {assignment.env_index} label drift"
            )
        rebuilt_results.append(rebuilt)

    receipts = payload.get("chunk_receipts")
    if not isinstance(receipts, list) or len(receipts) != 18:
        raise ValueError("formal report chunk receipts mismatch")
    source = _mapping(payload.get("source"), "source")
    device = _mapping(payload.get("device"), "device")
    for chunk_index, receipt_value in enumerate(receipts):
        receipt = _mapping(receipt_value, "chunk receipt")
        expected = {
            "chunk_index": chunk_index,
            "candidate_id": candidate_ids[chunk_index],
            "candidate_world_count": SAFETY_SWARM_V2_FORMAL_BATCH_CHUNK_SIZE,
            "source_commit": source.get("commit"),
            "device_sha256": _sha256_json(device),
            "batched_execution_wall_seconds": receipt.get(
                "batched_execution_wall_seconds"
            ),
            "scene_build_seconds": receipt.get("scene_build_seconds"),
            "gpu_telemetry": receipt.get("gpu_telemetry"),
            "report_sha256": receipt.get("report_sha256"),
        }
        if receipt != expected or not str(receipt["report_sha256"]).strip():
            raise ValueError("formal report chunk receipt mismatch")
        _finite(
            receipt["batched_execution_wall_seconds"],
            "batched_execution_wall_seconds",
        )
        if receipt["scene_build_seconds"] is not None:
            _finite(receipt["scene_build_seconds"], "scene_build_seconds")
        _validate_radeon_identity(
            {
                "source": {"commit": receipt["source_commit"]},
                "backend": "genesis_gpu_batched",
                "device": device,
                "gpu_telemetry": receipt["gpu_telemetry"],
            },
            label="Radeon V2 formal receipt",
        )

    summary = _mapping(payload.get("summary"), "summary")
    wall_seconds = _finite(
        summary.get("batched_execution_wall_seconds"),
        "batched_execution_wall_seconds",
    )
    receipt_wall_seconds = sum(
        float(receipt["batched_execution_wall_seconds"])
        for receipt in receipts
    )
    if wall_seconds != receipt_wall_seconds:
        raise ValueError("formal report wall-time aggregation mismatch")
    expected_telemetry = _aggregate_gpu_telemetry(receipts)
    if payload.get("gpu_telemetry") != expected_telemetry:
        raise ValueError("formal report telemetry aggregation mismatch")
    receipt_scene_build_values = [
        receipt["scene_build_seconds"] for receipt in receipts
    ]
    if all(value is not None for value in receipt_scene_build_values):
        expected_scene_build = sum(
            float(value) for value in receipt_scene_build_values
        )
        if payload.get("total_scene_build_seconds") != expected_scene_build:
            raise ValueError("formal report scene-build aggregation mismatch")
    elif "total_scene_build_seconds" in payload:
        raise ValueError("formal report has incomplete scene-build receipts")
    expected_candidates, expected_summary = summarize_candidate_selection(
        rebuilt_results,
        protocol=protocol,
        wall_seconds=wall_seconds,
    )
    expected_summary["formal_status"] = expected_summary.pop("smoke_status")
    if payload.get("candidate_summaries") != expected_candidates:
        raise ValueError("formal candidate summaries mismatch")
    if summary != expected_summary:
        raise ValueError("formal selection summary mismatch")

    without_hash = {
        key: value for key, value in payload.items() if key != "report_sha256"
    }
    if payload.get("report_sha256") != _sha256_json(without_hash):
        raise ValueError("Safety Swarm V2 formal report hash mismatch")
    return {
        "status": "passed",
        "schema_version": SAFETY_SWARM_V2_SCHEMA_VERSION,
        "mode": "radeon_formal",
        "protocol_sha256": protocol["protocol_sha256"],
        "candidate_world_count": len(assignments),
        "formal_status": expected_summary["formal_status"],
        "decision": expected_summary["decision"],
        "selected_candidate_id": expected_summary["selected_candidate_id"],
        "showcase_ready": True,
        "report_sha256": payload["report_sha256"],
    }


def validate_safety_swarm_v2_smoke_report(
    payload: Mapping[str, object],
    *,
    require_radeon: bool = False,
) -> dict[str, object]:
    """Strictly reconstruct a V2 smoke report and its selection decision."""

    if payload.get("schema_version") != SAFETY_SWARM_V2_SCHEMA_VERSION:
        raise ValueError("unsupported Safety Swarm V2 schema")
    if payload.get("report_name") != SAFETY_SWARM_V2_REPORT_NAME:
        raise ValueError("unexpected Safety Swarm V2 report name")
    tier = str(payload.get("tier"))
    protocol = build_safety_swarm_v2_smoke_protocol(tier)
    if payload.get("protocol") != protocol:
        raise ValueError("Safety Swarm V2 protocol mismatch")
    if payload.get("claim_boundary") != protocol["evidence_scope"]:
        raise ValueError("Safety Swarm V2 claim boundary mismatch")

    mode = str(payload.get("mode"))
    if mode not in {"offline_fixture", "radeon_engineering_smoke"}:
        raise ValueError("unexpected Safety Swarm V2 mode")
    expected_status = (
        "ui_validation_only"
        if mode == "offline_fixture"
        else "partial_executor_validation"
    )
    if payload.get("evidence_status") != expected_status:
        raise ValueError("Safety Swarm V2 evidence status mismatch")
    if bool(payload.get("showcase_ready")):
        raise ValueError("Safety Swarm V2 smoke cannot be showcase-ready")

    source = _mapping(payload.get("source"), "source")
    if mode == "radeon_engineering_smoke":
        commit = str(source.get("commit", ""))
        if len(commit) < 7 or any(
            character not in "0123456789abcdef" for character in commit
        ):
            raise ValueError("Radeon V2 smoke requires a Git commit")
        if payload.get("backend") != "genesis_gpu_batched":
            raise ValueError("Radeon V2 smoke requires Genesis GPU batching")
        device = _mapping(payload.get("device"), "device")
        if "amd" not in str(device.get("name", "")).lower():
            raise ValueError("Radeon V2 smoke does not identify an AMD GPU")
        if not str(device.get("hip_version", "")).strip():
            raise ValueError("Radeon V2 smoke is missing HIP")
        telemetry = _mapping(payload.get("gpu_telemetry"), "gpu_telemetry")
        if int(telemetry.get("sample_count", 0)) < 1:
            raise ValueError("Radeon V2 smoke has no ROCm telemetry")
    if require_radeon and mode != "radeon_engineering_smoke":
        raise ValueError("strict Radeon validation requires a Radeon V2 smoke")

    assignments = assign_candidate_worlds(
        [str(value) for value in protocol["candidate_ids"]],
        [int(value) for value in protocol["world_ids"]],
    )
    raw_results = payload.get("results")
    if not isinstance(raw_results, list) or len(raw_results) != len(assignments):
        raise ValueError("Safety Swarm V2 result count mismatch")
    rebuilt_results: list[dict[str, object]] = []
    for assignment, raw_result in zip(assignments, raw_results, strict=True):
        result = _mapping(raw_result, f"result {assignment.env_index}")
        if result.get("perturbation") != safety_swarm_world_asdict(
            build_safety_swarm_matrix()[assignment.world_id]
        ):
            raise ValueError(
                f"Safety Swarm V2 environment {assignment.env_index} matrix drift"
            )
        measurement = _measurement_from_mapping(
            _mapping(result.get("measurement"), "measurement")
        )
        rebuilt = classify_candidate_world(assignment, measurement)
        if result != rebuilt:
            raise ValueError(
                f"Safety Swarm V2 environment {assignment.env_index} label drift"
            )
        rebuilt_results.append(rebuilt)

    summary = _mapping(payload.get("summary"), "summary")
    wall_seconds = _finite(
        summary.get("batched_execution_wall_seconds"),
        "batched_execution_wall_seconds",
    )
    expected_candidates, expected_summary = summarize_candidate_selection(
        rebuilt_results,
        protocol=protocol,
        wall_seconds=wall_seconds,
    )
    if payload.get("candidate_summaries") != expected_candidates:
        raise ValueError("Safety Swarm V2 candidate summaries mismatch")
    if summary != expected_summary:
        raise ValueError("Safety Swarm V2 selection summary mismatch")

    without_hash = {
        key: value for key, value in payload.items() if key != "report_sha256"
    }
    if payload.get("report_sha256") != _sha256_json(without_hash):
        raise ValueError("Safety Swarm V2 report hash mismatch")
    return {
        "status": "passed",
        "schema_version": SAFETY_SWARM_V2_SCHEMA_VERSION,
        "mode": mode,
        "tier": tier,
        "protocol_sha256": protocol["protocol_sha256"],
        "formal_protocol_sha256": protocol["formal_protocol_sha256"],
        "candidate_world_count": len(assignments),
        "smoke_status": expected_summary["smoke_status"],
        "decision": expected_summary["decision"],
        "selected_candidate_id": expected_summary["selected_candidate_id"],
        "showcase_ready": False,
        "report_sha256": payload["report_sha256"],
    }


def build_safety_swarm_v2_offline_fixture_measurements(
    tier: str = "triad-4",
) -> tuple[CandidateWorldMeasurement, ...]:
    """Build deterministic mixed outcomes for UI and validator calibration."""

    candidate_ids, world_ids = safety_swarm_v2_tier_definition(tier)
    winner_id = "yaw_+67.5_retreat_+0.000_approach_+0.140"
    measurements: list[CandidateWorldMeasurement] = []
    for candidate_id in candidate_ids:
        for position, world_id in enumerate(world_ids):
            if candidate_id == winner_id:
                clearance = 0.018 + position * 0.0004
                stability = 0.92 - position * 0.005
                task_completed = True
                contact = False
            elif candidate_id == "yaw_+00.0_offset_+0.000":
                clearance = 0.008 if position == 0 else 0.015
                stability = 0.90
                task_completed = True
                contact = False
            else:
                clearance = 0.030
                stability = 0.0
                task_completed = False
                contact = False
            measurements.append(
                CandidateWorldMeasurement(
                    candidate_id=candidate_id,
                    world_id=world_id,
                    minimum_clearance_m=clearance,
                    stability=stability,
                    reachable=True,
                    task_completed=task_completed,
                    clutter_contact=contact,
                    elapsed_environment_steps=499,
                )
            )
    return tuple(measurements)
