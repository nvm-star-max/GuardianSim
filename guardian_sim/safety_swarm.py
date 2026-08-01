"""Frozen protocol and evidence helpers for Radeon Safety Swarm.

Safety Swarm takes one already-selected robot action and evaluates it in a
fixed 16 x 16 uncertainty matrix.  The helpers in this module are deliberately
simulator-independent: Genesis produces the measurements, while this module
owns matrix identity, typed safety costs, aggregation, and strict validation.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from statistics import NormalDist

from guardian_sim.gate32_benchmark import (
    GATE32_MINIMUM_SAFE_CLEARANCE_M,
    GATE32_MINIMUM_STABILITY,
)

SAFETY_SWARM_SCHEMA_VERSION = 1
SAFETY_SWARM_REPORT_NAME = "radeon-safety-swarm"
SAFETY_SWARM_SMOKE_SCHEMA_VERSION = 1
SAFETY_SWARM_SMOKE_REPORT_NAME = "radeon-safety-swarm-smoke"
SAFETY_SWARM_GRID_SIZE = 16
SAFETY_SWARM_WORLD_COUNT = SAFETY_SWARM_GRID_SIZE**2
SAFETY_SWARM_CONFIDENCE_LEVEL = 0.95
SAFETY_SWARM_SMOKE_WORLD_COUNTS = (4, 16)

# The 256 worlds are the Cartesian product of four four-level factor groups.
# Grouping correlated physical values keeps the V1 workload exactly 4^4 while
# retaining every perturbation promised by the public implementation plan.
TARGET_POSE_LEVELS = (
    {
        "level": "target_nw",
        "target_dx_m": -0.008,
        "target_dy_m": 0.004,
        "target_yaw_bias_deg": -6.0,
    },
    {
        "level": "target_ne",
        "target_dx_m": 0.008,
        "target_dy_m": 0.004,
        "target_yaw_bias_deg": 6.0,
    },
    {
        "level": "target_sw",
        "target_dx_m": -0.008,
        "target_dy_m": -0.004,
        "target_yaw_bias_deg": 6.0,
    },
    {
        "level": "target_se",
        "target_dx_m": 0.008,
        "target_dy_m": -0.004,
        "target_yaw_bias_deg": -6.0,
    },
)

CLUTTER_GEOMETRY_LEVELS = (
    {
        "level": "tight_clockwise",
        "clutter_gap_delta_m": -0.006,
        "clutter_bearing_bias_deg": -15.0,
    },
    {
        "level": "tight_counterclockwise",
        "clutter_gap_delta_m": -0.006,
        "clutter_bearing_bias_deg": 15.0,
    },
    {
        "level": "wide_clockwise",
        "clutter_gap_delta_m": 0.006,
        "clutter_bearing_bias_deg": -15.0,
    },
    {
        "level": "wide_counterclockwise",
        "clutter_gap_delta_m": 0.006,
        "clutter_bearing_bias_deg": 15.0,
    },
)

END_EFFECTOR_BIAS_LEVELS = (
    {
        "level": "ee_nw",
        "end_effector_dx_m": -0.004,
        "end_effector_dy_m": 0.003,
    },
    {
        "level": "ee_ne",
        "end_effector_dx_m": 0.004,
        "end_effector_dy_m": 0.003,
    },
    {
        "level": "ee_sw",
        "end_effector_dx_m": -0.004,
        "end_effector_dy_m": -0.003,
    },
    {
        "level": "ee_se",
        "end_effector_dx_m": 0.004,
        "end_effector_dy_m": -0.003,
    },
)

ACTION_DELAY_LEVELS = (
    {"level": "delay_0", "action_start_delay_steps": 0},
    {"level": "delay_1", "action_start_delay_steps": 1},
    {"level": "delay_2", "action_start_delay_steps": 2},
    {"level": "delay_4", "action_start_delay_steps": 4},
)

STOP_REASON_ORDER = (
    "clutter_contact",
    "unreachable",
    "clearance_below_minimum",
    "stability_below_minimum",
    "task_failure",
)


@dataclass(frozen=True, slots=True)
class SafetySwarmWorld:
    """One row of the frozen 256-world uncertainty matrix."""

    world_id: int
    row: int
    column: int
    target_pose_level: int
    clutter_geometry_level: int
    end_effector_bias_level: int
    action_delay_level: int
    target_dx_m: float
    target_dy_m: float
    target_yaw_bias_deg: float
    clutter_gap_delta_m: float
    clutter_bearing_bias_deg: float
    end_effector_dx_m: float
    end_effector_dy_m: float
    action_start_delay_steps: int


@dataclass(frozen=True, slots=True)
class SafetySwarmMeasurement:
    """Simulator measurements for one uncertainty world."""

    world_id: int
    minimum_clearance_m: float
    stability: float
    reachable: bool
    task_completed: bool
    clutter_contact: bool
    elapsed_environment_steps: int


@dataclass(frozen=True, slots=True)
class SafetyCostVector:
    """Typed costs kept separate from utility or reward."""

    contact: int
    clearance_m: float
    stability: float
    task_failure: int


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode()).hexdigest()


def safety_swarm_world_asdict(world: SafetySwarmWorld) -> dict[str, object]:
    """Return a JSON-native matrix row."""

    return asdict(world)


def build_safety_swarm_matrix() -> tuple[SafetySwarmWorld, ...]:
    """Build the deterministic 4 x 4 x 4 x 4 uncertainty matrix."""

    worlds: list[SafetySwarmWorld] = []
    for target_index, target in enumerate(TARGET_POSE_LEVELS):
        for clutter_index, clutter in enumerate(CLUTTER_GEOMETRY_LEVELS):
            for end_effector_index, end_effector in enumerate(
                END_EFFECTOR_BIAS_LEVELS
            ):
                for delay_index, delay in enumerate(ACTION_DELAY_LEVELS):
                    world_id = len(worlds)
                    worlds.append(
                        SafetySwarmWorld(
                            world_id=world_id,
                            row=world_id // SAFETY_SWARM_GRID_SIZE,
                            column=world_id % SAFETY_SWARM_GRID_SIZE,
                            target_pose_level=target_index,
                            clutter_geometry_level=clutter_index,
                            end_effector_bias_level=end_effector_index,
                            action_delay_level=delay_index,
                            target_dx_m=float(target["target_dx_m"]),
                            target_dy_m=float(target["target_dy_m"]),
                            target_yaw_bias_deg=float(
                                target["target_yaw_bias_deg"]
                            ),
                            clutter_gap_delta_m=float(
                                clutter["clutter_gap_delta_m"]
                            ),
                            clutter_bearing_bias_deg=float(
                                clutter["clutter_bearing_bias_deg"]
                            ),
                            end_effector_dx_m=float(
                                end_effector["end_effector_dx_m"]
                            ),
                            end_effector_dy_m=float(
                                end_effector["end_effector_dy_m"]
                            ),
                            action_start_delay_steps=int(
                                delay["action_start_delay_steps"]
                            ),
                        )
                    )
    if len(worlds) != SAFETY_SWARM_WORLD_COUNT:
        raise AssertionError("Safety Swarm matrix must contain exactly 256 worlds")
    return tuple(worlds)


def safety_swarm_matrix_sha256() -> str:
    """Return the identity of the complete ordered matrix."""

    return _sha256_json(
        [safety_swarm_world_asdict(world) for world in build_safety_swarm_matrix()]
    )


def build_safety_swarm_protocol() -> dict[str, object]:
    """Freeze the V1 uncertainty envelope and all decision thresholds."""

    protocol: dict[str, object] = {
        "report_name": SAFETY_SWARM_REPORT_NAME,
        "world_count": SAFETY_SWARM_WORLD_COUNT,
        "grid_shape": [SAFETY_SWARM_GRID_SIZE, SAFETY_SWARM_GRID_SIZE],
        "matrix_design": (
            "Cartesian product of four declared factor groups with four levels "
            "each: target pose, clutter geometry, end-effector bias, start delay"
        ),
        "factor_levels": {
            "target_pose": list(TARGET_POSE_LEVELS),
            "clutter_geometry": list(CLUTTER_GEOMETRY_LEVELS),
            "end_effector_bias": list(END_EFFECTOR_BIAS_LEVELS),
            "action_delay": list(ACTION_DELAY_LEVELS),
        },
        "matrix_sha256": safety_swarm_matrix_sha256(),
        "minimum_safe_clearance_m": GATE32_MINIMUM_SAFE_CLEARANCE_M,
        "minimum_stability": GATE32_MINIMUM_STABILITY,
        "required_safe_world_count": SAFETY_SWARM_WORLD_COUNT,
        "maximum_contact_world_count": 0,
        "confidence_level": SAFETY_SWARM_CONFIDENCE_LEVEL,
        "stop_reason_order": list(STOP_REASON_ORDER),
        "unsafe_policy": "execute_only_if_all_256_worlds_pass_else_safe_stop",
        "evidence_scope": (
            "Engineering uncertainty stress-test population. It is separate "
            "from Gate 3.2 formal scenarios and is not a physical-robot safety "
            "guarantee."
        ),
    }
    protocol["protocol_sha256"] = _sha256_json(protocol)
    return protocol


def safety_swarm_smoke_world_ids(world_count: int) -> tuple[int, ...]:
    """Return a fixed balanced subset for a 4- or 16-world engineering smoke.

    The four-world diagonal exercises every level of every factor once.  The
    sixteen-world orthogonal subset exercises each level four times while
    keeping every selected row tied to the frozen 256-world matrix.
    """

    if world_count not in SAFETY_SWARM_SMOKE_WORLD_COUNTS:
        raise ValueError("Safety Swarm smoke world_count must be 4 or 16")
    if world_count == 4:
        factor_rows = ((level, level, level, level) for level in range(4))
    else:
        factor_rows = (
            (
                target,
                clutter,
                (target + clutter) % 4,
                (target + 2 * clutter) % 4,
            )
            for target in range(4)
            for clutter in range(4)
        )
    return tuple(
        (((target * 4 + clutter) * 4 + end_effector) * 4 + delay)
        for target, clutter, end_effector, delay in factor_rows
    )


def build_safety_swarm_smoke_protocol(world_count: int) -> dict[str, object]:
    """Freeze a partial engineering smoke without changing the formal protocol."""

    formal_protocol = build_safety_swarm_protocol()
    protocol: dict[str, object] = {
        "report_name": SAFETY_SWARM_SMOKE_REPORT_NAME,
        "world_count": world_count,
        "world_ids": list(safety_swarm_smoke_world_ids(world_count)),
        "selection_design": (
            "Predeclared balanced subset of the frozen 256-world matrix; "
            "not a formal population result"
        ),
        "formal_report_name": SAFETY_SWARM_REPORT_NAME,
        "formal_protocol_sha256": formal_protocol["protocol_sha256"],
        "formal_matrix_sha256": formal_protocol["matrix_sha256"],
        "minimum_safe_clearance_m": formal_protocol[
            "minimum_safe_clearance_m"
        ],
        "minimum_stability": formal_protocol["minimum_stability"],
        "maximum_contact_world_count": 0,
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
        "unsafe_policy": "continue_only_if_every_smoke_world_passes",
        "evidence_scope": (
            "Radeon engineering smoke for executor validation only. It cannot "
            "replace or be merged into the frozen 256-world formal report."
        ),
    }
    protocol["protocol_sha256"] = _sha256_json(protocol)
    return protocol


def _finite(value: object, label: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
    ):
        raise ValueError(f"{label} must be finite")
    return float(value)


def _measurement_from_mapping(
    value: Mapping[str, object] | SafetySwarmMeasurement,
) -> SafetySwarmMeasurement:
    if isinstance(value, SafetySwarmMeasurement):
        return value
    return SafetySwarmMeasurement(
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


def classify_safety_swarm_world(
    world: SafetySwarmWorld,
    measurement: SafetySwarmMeasurement,
    *,
    minimum_clearance_m: float = GATE32_MINIMUM_SAFE_CLEARANCE_M,
    minimum_stability: float = GATE32_MINIMUM_STABILITY,
) -> dict[str, object]:
    """Convert raw measurements into typed costs and a hard-safe label."""

    if measurement.world_id != world.world_id:
        raise ValueError("measurement world_id does not match matrix row")
    if not 0.0 <= measurement.stability <= 1.0:
        raise ValueError("stability must be in [0, 1]")
    if measurement.elapsed_environment_steps < 1:
        raise ValueError("elapsed_environment_steps must be positive")

    failed_gates: list[str] = []
    if measurement.clutter_contact:
        failed_gates.append("clutter_contact")
    if not measurement.reachable:
        failed_gates.append("unreachable")
    if measurement.minimum_clearance_m < minimum_clearance_m:
        failed_gates.append("clearance_below_minimum")
    if measurement.stability < minimum_stability:
        failed_gates.append("stability_below_minimum")
    if not measurement.task_completed:
        failed_gates.append("task_failure")

    costs = SafetyCostVector(
        contact=int(measurement.clutter_contact),
        clearance_m=max(
            0.0,
            minimum_clearance_m - measurement.minimum_clearance_m,
        ),
        stability=max(0.0, minimum_stability - measurement.stability),
        task_failure=int(not measurement.task_completed),
    )
    return {
        "world_id": world.world_id,
        "perturbation": safety_swarm_world_asdict(world),
        "measurement": asdict(measurement),
        "costs": asdict(costs),
        "hard_safe": not failed_gates,
        "primary_stop_reason": failed_gates[0] if failed_gates else "safe",
        "failed_gates": failed_gates,
    }


def wilson_lower_bound(
    successes: int,
    total: int,
    *,
    confidence_level: float = SAFETY_SWARM_CONFIDENCE_LEVEL,
) -> float:
    """Return the two-sided Wilson interval's lower bound."""

    if total < 1 or not 0 <= successes <= total:
        raise ValueError("Wilson inputs must satisfy 0 <= successes <= total")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be in (0, 1)")
    z = NormalDist().inv_cdf(0.5 + confidence_level / 2.0)
    proportion = successes / total
    denominator = 1.0 + z * z / total
    centre = proportion + z * z / (2.0 * total)
    radius = z * math.sqrt(
        proportion * (1.0 - proportion) / total
        + z * z / (4.0 * total * total)
    )
    return max(0.0, (centre - radius) / denominator)


def _percentile(values: Sequence[float], percentile: float) -> float:
    if not values:
        raise ValueError("percentile requires values")
    if not 0.0 <= percentile <= 1.0:
        raise ValueError("percentile must be in [0, 1]")
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def summarize_safety_swarm(
    results: Sequence[Mapping[str, object]],
    *,
    wall_seconds: float,
) -> dict[str, object]:
    """Recompute every judge-facing aggregate from world-level evidence."""

    if len(results) != SAFETY_SWARM_WORLD_COUNT:
        raise ValueError("Safety Swarm summary requires exactly 256 worlds")
    if wall_seconds <= 0.0 or not math.isfinite(wall_seconds):
        raise ValueError("wall_seconds must be positive and finite")

    safe_count = sum(bool(result["hard_safe"]) for result in results)
    measurements = [
        result["measurement"]
        for result in results
        if isinstance(result.get("measurement"), Mapping)
    ]
    if len(measurements) != SAFETY_SWARM_WORLD_COUNT:
        raise ValueError("every world requires a measurement")
    clearances = [
        _finite(value["minimum_clearance_m"], "minimum_clearance_m")
        for value in measurements
    ]
    stabilities = [
        _finite(value["stability"], "stability") for value in measurements
    ]
    total_environment_steps = sum(
        int(value["elapsed_environment_steps"]) for value in measurements
    )
    failure_histogram = Counter(
        str(result["primary_stop_reason"]) for result in results
    )
    contact_world_count = sum(
        bool(value["clutter_contact"]) for value in measurements
    )
    decision = (
        "execute"
        if safe_count == SAFETY_SWARM_WORLD_COUNT and contact_world_count == 0
        else "safe_stop"
    )
    return {
        "decision": decision,
        "safe_world_count": safe_count,
        "unsafe_world_count": SAFETY_SWARM_WORLD_COUNT - safe_count,
        "safe_world_rate": safe_count / SAFETY_SWARM_WORLD_COUNT,
        "safe_world_rate_wilson_lower_bound": wilson_lower_bound(
            safe_count,
            SAFETY_SWARM_WORLD_COUNT,
        ),
        "contact_world_count": contact_world_count,
        "worst_case_clearance_m": min(clearances),
        "fifth_percentile_clearance_m": _percentile(clearances, 0.05),
        "minimum_stability": min(stabilities),
        "failure_histogram": {
            reason: failure_histogram.get(reason, 0)
            for reason in ("safe", *STOP_REASON_ORDER)
        },
        "batched_execution_wall_seconds": wall_seconds,
        "total_environment_steps": total_environment_steps,
        "environment_steps_per_second": total_environment_steps / wall_seconds,
    }


def _summarize_safety_swarm_smoke(
    results: Sequence[Mapping[str, object]],
    *,
    wall_seconds: float,
) -> dict[str, object]:
    if not results:
        raise ValueError("Safety Swarm smoke requires results")
    if wall_seconds <= 0.0 or not math.isfinite(wall_seconds):
        raise ValueError("wall_seconds must be positive and finite")
    count = len(results)
    measurements = [
        _mapping(result.get("measurement"), "measurement") for result in results
    ]
    safe_count = sum(bool(result["hard_safe"]) for result in results)
    contact_count = sum(bool(value["clutter_contact"]) for value in measurements)
    clearances = [
        _finite(value["minimum_clearance_m"], "minimum_clearance_m")
        for value in measurements
    ]
    stabilities = [
        _finite(value["stability"], "stability") for value in measurements
    ]
    environment_steps = sum(
        int(value["elapsed_environment_steps"]) for value in measurements
    )
    histogram = Counter(str(result["primary_stop_reason"]) for result in results)
    return {
        "smoke_status": (
            "passed"
            if safe_count == count and contact_count == 0
            else "failed"
        ),
        "safe_world_count": safe_count,
        "unsafe_world_count": count - safe_count,
        "contact_world_count": contact_count,
        "worst_case_clearance_m": min(clearances),
        "minimum_stability": min(stabilities),
        "failure_histogram": {
            reason: histogram.get(reason, 0)
            for reason in ("safe", *STOP_REASON_ORDER)
        },
        "batched_execution_wall_seconds": wall_seconds,
        "total_environment_steps": environment_steps,
        "environment_steps_per_second": environment_steps / wall_seconds,
    }


def assemble_safety_swarm_smoke_report(
    measurements: Sequence[Mapping[str, object] | SafetySwarmMeasurement],
    *,
    candidate_id: str,
    wall_seconds: float,
    source_commit: str,
    backend: str,
    device: Mapping[str, object],
    gpu_telemetry: Mapping[str, object],
) -> dict[str, object]:
    """Assemble a strict Radeon engineering-smoke report."""

    count = len(measurements)
    protocol = build_safety_swarm_smoke_protocol(count)
    matrix = build_safety_swarm_matrix()
    worlds = tuple(matrix[world_id] for world_id in protocol["world_ids"])
    parsed = [_measurement_from_mapping(value) for value in measurements]
    results = [
        classify_safety_swarm_world(world, measurement)
        for world, measurement in zip(worlds, parsed, strict=True)
    ]
    payload: dict[str, object] = {
        "schema_version": SAFETY_SWARM_SMOKE_SCHEMA_VERSION,
        "report_name": SAFETY_SWARM_SMOKE_REPORT_NAME,
        "mode": "radeon_engineering_smoke",
        "backend": backend,
        "evidence_status": "partial_executor_validation",
        "showcase_ready": False,
        "claim_boundary": protocol["evidence_scope"],
        "source": {
            "commit": source_commit,
            "candidate_id": candidate_id,
        },
        "protocol": protocol,
        "device": dict(device),
        "gpu_telemetry": dict(gpu_telemetry),
        "results": results,
        "summary": _summarize_safety_swarm_smoke(
            results,
            wall_seconds=wall_seconds,
        ),
    }
    payload["report_sha256"] = _sha256_json(payload)
    validate_safety_swarm_smoke_report(payload, require_radeon=True)
    return payload


def assemble_safety_swarm_report(
    measurements: Sequence[Mapping[str, object] | SafetySwarmMeasurement],
    *,
    candidate_id: str,
    wall_seconds: float,
    mode: str,
    backend: str,
    source_commit: str,
    device: Mapping[str, object] | None = None,
    gpu_telemetry: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Assemble a hashed report from raw per-world measurements."""

    if mode not in {"offline_fixture", "radeon_formal"}:
        raise ValueError("mode must be offline_fixture or radeon_formal")
    if not candidate_id.strip():
        raise ValueError("candidate_id is required")
    matrix = build_safety_swarm_matrix()
    parsed = [_measurement_from_mapping(value) for value in measurements]
    if len(parsed) != len(matrix):
        raise ValueError("Safety Swarm requires exactly 256 measurements")
    results = [
        classify_safety_swarm_world(world, measurement)
        for world, measurement in zip(matrix, parsed, strict=True)
    ]
    protocol = build_safety_swarm_protocol()
    payload: dict[str, object] = {
        "schema_version": SAFETY_SWARM_SCHEMA_VERSION,
        "report_name": SAFETY_SWARM_REPORT_NAME,
        "mode": mode,
        "backend": backend,
        "evidence_status": (
            "ui_validation_only"
            if mode == "offline_fixture"
            else "preserved_radeon_run"
        ),
        "showcase_ready": mode == "radeon_formal",
        "claim_boundary": protocol["evidence_scope"],
        "source": {
            "commit": source_commit,
            "candidate_id": candidate_id,
        },
        "protocol": protocol,
        "device": dict(device or {}),
        "gpu_telemetry": dict(gpu_telemetry or {}),
        "results": results,
        "summary": summarize_safety_swarm(results, wall_seconds=wall_seconds),
    }
    payload["report_sha256"] = _sha256_json(payload)
    validate_safety_swarm_report(payload)
    return payload


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return value


def _assert_close(actual: object, expected: float, label: str) -> None:
    value = _finite(actual, label)
    if not math.isclose(value, expected, rel_tol=1e-9, abs_tol=1e-12):
        raise ValueError(f"{label} mismatch")


def validate_safety_swarm_report(
    payload: Mapping[str, object],
    *,
    require_radeon: bool = False,
) -> dict[str, object]:
    """Strictly validate matrix identity, world labels, aggregates, and hashes."""

    if payload.get("schema_version") != SAFETY_SWARM_SCHEMA_VERSION:
        raise ValueError("unsupported Safety Swarm schema")
    if payload.get("report_name") != SAFETY_SWARM_REPORT_NAME:
        raise ValueError("unexpected Safety Swarm report name")
    if payload.get("protocol") != build_safety_swarm_protocol():
        raise ValueError("Safety Swarm protocol does not match the frozen declaration")
    if payload.get("claim_boundary") != payload["protocol"]["evidence_scope"]:
        raise ValueError("Safety Swarm claim boundary mismatch")

    mode = str(payload.get("mode"))
    if mode not in {"offline_fixture", "radeon_formal"}:
        raise ValueError("unexpected Safety Swarm mode")
    expected_status = (
        "ui_validation_only" if mode == "offline_fixture" else "preserved_radeon_run"
    )
    if payload.get("evidence_status") != expected_status:
        raise ValueError("Safety Swarm evidence status mismatch")
    if bool(payload.get("showcase_ready")) != (mode == "radeon_formal"):
        raise ValueError("Safety Swarm showcase-ready label mismatch")

    source = _mapping(payload.get("source"), "source")
    if not str(source.get("candidate_id", "")).strip():
        raise ValueError("Safety Swarm source candidate is missing")
    if mode == "radeon_formal":
        commit = str(source.get("commit", ""))
        if len(commit) < 7 or any(character not in "0123456789abcdef" for character in commit):
            raise ValueError("Radeon formal report requires a Git commit")

    raw_results = payload.get("results")
    if not isinstance(raw_results, list) or len(raw_results) != SAFETY_SWARM_WORLD_COUNT:
        raise ValueError("Safety Swarm result count mismatch")
    matrix = build_safety_swarm_matrix()
    rebuilt_results: list[dict[str, object]] = []
    for world, raw_result in zip(matrix, raw_results, strict=True):
        result = _mapping(raw_result, f"result {world.world_id}")
        if result.get("perturbation") != safety_swarm_world_asdict(world):
            raise ValueError(f"Safety Swarm world {world.world_id} matrix drift")
        measurement = _measurement_from_mapping(
            _mapping(result.get("measurement"), "measurement")
        )
        rebuilt = classify_safety_swarm_world(world, measurement)
        if result != rebuilt:
            raise ValueError(f"Safety Swarm world {world.world_id} label or cost drift")
        rebuilt_results.append(rebuilt)

    summary = _mapping(payload.get("summary"), "summary")
    wall_seconds = _finite(
        summary.get("batched_execution_wall_seconds"),
        "batched_execution_wall_seconds",
    )
    rebuilt_summary = summarize_safety_swarm(
        rebuilt_results,
        wall_seconds=wall_seconds,
    )
    if set(summary) != set(rebuilt_summary):
        raise ValueError("Safety Swarm summary fields mismatch")
    for key, expected in rebuilt_summary.items():
        if isinstance(expected, float):
            _assert_close(summary.get(key), expected, f"summary.{key}")
        elif summary.get(key) != expected:
            raise ValueError(f"summary.{key} mismatch")

    without_hash = {
        key: value for key, value in payload.items() if key != "report_sha256"
    }
    if payload.get("report_sha256") != _sha256_json(without_hash):
        raise ValueError("Safety Swarm report hash mismatch")

    if require_radeon and mode != "radeon_formal":
        raise ValueError("validation requires a Radeon formal report")
    if mode == "radeon_formal":
        if payload.get("backend") != "genesis_gpu_batched":
            raise ValueError("Radeon formal report requires Genesis GPU batching")
        device = _mapping(payload.get("device"), "device")
        if "amd" not in str(device.get("name", "")).lower():
            raise ValueError("Radeon formal report does not identify an AMD GPU")
        if not str(device.get("hip_version", "")).strip():
            raise ValueError("Radeon formal report is missing HIP")
        telemetry = _mapping(payload.get("gpu_telemetry"), "gpu_telemetry")
        if int(telemetry.get("sample_count", 0)) < 1:
            raise ValueError("Radeon formal report has no ROCm telemetry")
    elif payload.get("backend") != "deterministic_fixture":
        raise ValueError("offline fixture must use the deterministic fixture backend")

    return {
        "status": "passed",
        "schema_version": SAFETY_SWARM_SCHEMA_VERSION,
        "mode": mode,
        "protocol_sha256": payload["protocol"]["protocol_sha256"],
        "matrix_sha256": payload["protocol"]["matrix_sha256"],
        "report_sha256": payload["report_sha256"],
        "world_count": SAFETY_SWARM_WORLD_COUNT,
        "decision": summary["decision"],
        "safe_world_count": summary["safe_world_count"],
        "showcase_ready": payload["showcase_ready"],
    }


def validate_safety_swarm_smoke_report(
    payload: Mapping[str, object],
    *,
    require_radeon: bool = False,
) -> dict[str, object]:
    """Strictly validate a partial executor smoke against its frozen subset."""

    if payload.get("schema_version") != SAFETY_SWARM_SMOKE_SCHEMA_VERSION:
        raise ValueError("unsupported Safety Swarm smoke schema")
    if payload.get("report_name") != SAFETY_SWARM_SMOKE_REPORT_NAME:
        raise ValueError("unexpected Safety Swarm smoke report name")
    raw_results = payload.get("results")
    if not isinstance(raw_results, list):
        raise ValueError("Safety Swarm smoke results must be a list")
    protocol = build_safety_swarm_smoke_protocol(len(raw_results))
    if payload.get("protocol") != protocol:
        raise ValueError("Safety Swarm smoke protocol drift")
    if payload.get("claim_boundary") != protocol["evidence_scope"]:
        raise ValueError("Safety Swarm smoke claim boundary mismatch")
    if payload.get("mode") != "radeon_engineering_smoke":
        raise ValueError("unexpected Safety Swarm smoke mode")
    if payload.get("evidence_status") != "partial_executor_validation":
        raise ValueError("Safety Swarm smoke evidence status mismatch")
    if payload.get("showcase_ready") is not False:
        raise ValueError("Safety Swarm smoke must never be showcase-ready")

    source = _mapping(payload.get("source"), "source")
    if not str(source.get("candidate_id", "")).strip():
        raise ValueError("Safety Swarm smoke candidate is missing")
    commit = str(source.get("commit", ""))
    if len(commit) < 7 or any(
        character not in "0123456789abcdef" for character in commit
    ):
        raise ValueError("Safety Swarm smoke requires a Git commit")

    matrix = build_safety_swarm_matrix()
    worlds = tuple(matrix[world_id] for world_id in protocol["world_ids"])
    rebuilt_results: list[dict[str, object]] = []
    for world, raw_result in zip(worlds, raw_results, strict=True):
        result = _mapping(raw_result, f"smoke result {world.world_id}")
        if result.get("perturbation") != safety_swarm_world_asdict(world):
            raise ValueError(f"Safety Swarm smoke world {world.world_id} matrix drift")
        measurement = _measurement_from_mapping(
            _mapping(result.get("measurement"), "measurement")
        )
        rebuilt = classify_safety_swarm_world(world, measurement)
        if result != rebuilt:
            raise ValueError(
                f"Safety Swarm smoke world {world.world_id} label or cost drift"
            )
        rebuilt_results.append(rebuilt)

    summary = _mapping(payload.get("summary"), "summary")
    wall_seconds = _finite(
        summary.get("batched_execution_wall_seconds"),
        "batched_execution_wall_seconds",
    )
    rebuilt_summary = _summarize_safety_swarm_smoke(
        rebuilt_results,
        wall_seconds=wall_seconds,
    )
    if set(summary) != set(rebuilt_summary):
        raise ValueError("Safety Swarm smoke summary fields mismatch")
    for key, expected in rebuilt_summary.items():
        if isinstance(expected, float):
            _assert_close(summary.get(key), expected, f"summary.{key}")
        elif summary.get(key) != expected:
            raise ValueError(f"summary.{key} mismatch")

    without_hash = {
        key: value for key, value in payload.items() if key != "report_sha256"
    }
    if payload.get("report_sha256") != _sha256_json(without_hash):
        raise ValueError("Safety Swarm smoke report hash mismatch")

    if payload.get("backend") != "genesis_gpu_batched":
        raise ValueError("Safety Swarm smoke requires Genesis GPU batching")
    device = _mapping(payload.get("device"), "device")
    if "amd" not in str(device.get("name", "")).lower():
        raise ValueError("Safety Swarm smoke does not identify an AMD GPU")
    if not str(device.get("hip_version", "")).strip():
        raise ValueError("Safety Swarm smoke is missing HIP")
    telemetry = _mapping(payload.get("gpu_telemetry"), "gpu_telemetry")
    if int(telemetry.get("sample_count", 0)) < 1:
        raise ValueError("Safety Swarm smoke has no ROCm telemetry")
    if require_radeon and payload.get("mode") != "radeon_engineering_smoke":
        raise ValueError("validation requires a Radeon smoke report")

    return {
        "status": "passed",
        "schema_version": SAFETY_SWARM_SMOKE_SCHEMA_VERSION,
        "mode": payload["mode"],
        "protocol_sha256": protocol["protocol_sha256"],
        "formal_protocol_sha256": protocol["formal_protocol_sha256"],
        "formal_matrix_sha256": protocol["formal_matrix_sha256"],
        "report_sha256": payload["report_sha256"],
        "world_count": len(rebuilt_results),
        "smoke_status": summary["smoke_status"],
        "safe_world_count": summary["safe_world_count"],
        "showcase_ready": False,
    }


def build_offline_fixture_measurements() -> tuple[SafetySwarmMeasurement, ...]:
    """Create deterministic UI-only measurements for local rendering tests."""

    measurements = []
    for world in build_safety_swarm_matrix():
        clearance = (
            0.0175
            + 0.65 * world.clutter_gap_delta_m
            - 0.30 * abs(world.target_dx_m)
            - 0.35 * abs(world.end_effector_dx_m)
            - 0.00055 * world.action_start_delay_steps
            - 0.00004 * abs(world.clutter_bearing_bias_deg)
        )
        stability = (
            0.86
            - 0.012 * world.action_start_delay_steps
            - 0.0015 * abs(world.target_yaw_bias_deg)
            - 0.4 * abs(world.end_effector_dy_m)
        )
        clutter_contact = clearance < 0.0065
        task_completed = not (
            world.action_start_delay_steps == 4
            and world.clutter_gap_delta_m < 0.0
            and world.end_effector_dy_m < 0.0
        )
        measurements.append(
            SafetySwarmMeasurement(
                world_id=world.world_id,
                minimum_clearance_m=clearance,
                stability=stability,
                reachable=True,
                task_completed=task_completed,
                clutter_contact=clutter_contact,
                elapsed_environment_steps=640
                + world.action_start_delay_steps,
            )
        )
    return tuple(measurements)
