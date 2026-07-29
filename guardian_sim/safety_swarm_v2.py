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
    world = build_safety_swarm_matrix()[assignment.world_id]
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
