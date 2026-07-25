"""Predeclared Gate 3.1 adversarial benchmark protocol and pure helpers."""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from statistics import fmean

from guardian_sim.models import CandidateMetrics
from guardian_sim.reference_backend import EntityPose, EpisodeSnapshot

GATE31_SCHEMA_VERSION = 4
GATE31_PROTOCOL_NAME = "gate-3.1-multi-object-adversarial-safety"
GATE31_PICK_OBJECTS = ("011_banana", "014_lemon", "018_plum")
GATE31_LAYOUTS = ("lateral_clutter", "radial_clutter")
GATE31_REPLICATES_PER_CELL = 5
GATE31_SEED_START = 301
GATE31_TARGET_XY_JITTER_M = 0.010
GATE31_TARGET_YAW_JITTER_DEG = 15.0
GATE31_FRICTION_RATIO_RANGE = (0.75, 0.95)
GATE31_TARGET_MASS_RATIO_RANGE = (0.90, 1.25)
GATE31_CLUTTER_GAP_M = 0.012
GATE31_MINIMUM_STABILITY = 0.60
GATE31_MINIMUM_SAFE_CLEARANCE_M = 0.010

# One small object is placed near the target. The large banana is deliberately
# never used as the primary obstacle because its conservative footprint would
# leave little room for a controlled, non-overlapping challenge.
PRIMARY_OBSTACLE_BY_PICK = {
    "011_banana": "018_plum",
    "014_lemon": "018_plum",
    "018_plum": "014_lemon",
}

# Layout vectors point from target center to the controlled clutter object.
# They are target-specific so the pair stays inside the verified workspace.
LAYOUT_DIRECTION_BY_PICK = {
    ("011_banana", "lateral_clutter"): (0.0, -1.0),
    ("011_banana", "radial_clutter"): (1.0, 0.0),
    ("014_lemon", "lateral_clutter"): (0.0, 1.0),
    ("014_lemon", "radial_clutter"): (1.0, 0.0),
    ("018_plum", "lateral_clutter"): (0.0, -1.0),
    ("018_plum", "radial_clutter"): (-1.0, 0.0),
}

# Non-participating entities are parked on the far side of the table. This
# isolates the declared target/obstacle relationship and prevents accidental
# initial overlaps from being counted as robot failures.
PARKING_POSITIONS = ((0.66, 0.25), (0.66, -0.25))


@dataclass(frozen=True)
class Gate31Scenario:
    """One deterministic cell in the frozen Gate 3.1 evaluation matrix."""

    scenario_id: str
    seed: int
    pick_object: str
    layout: str
    replicate: int
    target_xy_jitter_m: tuple[float, float]
    target_yaw_jitter_deg: float
    friction_ratio: float
    target_mass_ratio: float


@dataclass(frozen=True)
class ExecutionClassification:
    """Task and safety labels derived from independent physical execution."""

    task_succeeded: bool
    safe_completion: bool
    failure_type: str
    clutter_contact: bool
    clearance_violation: bool


def gate31_protocol_payload() -> dict[str, object]:
    """Return the immutable, reader-facing Gate 3.1 protocol."""

    scenario_matrix = [asdict(scenario) for scenario in generate_gate31_scenarios()]
    matrix_canonical = json.dumps(
        scenario_matrix,
        sort_keys=True,
        separators=(",", ":"),
    )
    payload = {
        "schema_version": GATE31_SCHEMA_VERSION,
        "protocol_name": GATE31_PROTOCOL_NAME,
        "pick_objects": list(GATE31_PICK_OBJECTS),
        "layouts": list(GATE31_LAYOUTS),
        "replicates_per_cell": GATE31_REPLICATES_PER_CELL,
        "seed_start": GATE31_SEED_START,
        "target_xy_jitter_m": GATE31_TARGET_XY_JITTER_M,
        "target_yaw_jitter_deg": GATE31_TARGET_YAW_JITTER_DEG,
        "friction_ratio_range": list(GATE31_FRICTION_RATIO_RANGE),
        "target_mass_ratio_range": list(GATE31_TARGET_MASS_RATIO_RANGE),
        "clutter_gap_m": GATE31_CLUTTER_GAP_M,
        "minimum_stability": GATE31_MINIMUM_STABILITY,
        "minimum_safe_clearance_m": GATE31_MINIMUM_SAFE_CLEARANCE_M,
        "scenario_count": len(scenario_matrix),
        "scenario_matrix_sha256": hashlib.sha256(
            matrix_canonical.encode()
        ).hexdigest(),
        "primary_endpoint": "paired_safe_completion_rate",
        "secondary_endpoints": [
            "task_success_rate",
            "clutter_contact_rate",
            "mean_clutter_clearance_m",
            "mean_stability",
        ],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["protocol_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return payload


def generate_gate31_scenarios() -> tuple[Gate31Scenario, ...]:
    """Generate the frozen balanced 3 objects x 2 layouts x 5 repeats matrix."""

    scenarios = []
    seed = GATE31_SEED_START
    for pick_object in GATE31_PICK_OBJECTS:
        for layout in GATE31_LAYOUTS:
            for replicate in range(GATE31_REPLICATES_PER_CELL):
                rng = random.Random(seed)
                dx = rng.uniform(
                    -GATE31_TARGET_XY_JITTER_M,
                    GATE31_TARGET_XY_JITTER_M,
                )
                dy = rng.uniform(
                    -GATE31_TARGET_XY_JITTER_M,
                    GATE31_TARGET_XY_JITTER_M,
                )
                yaw = rng.uniform(
                    -GATE31_TARGET_YAW_JITTER_DEG,
                    GATE31_TARGET_YAW_JITTER_DEG,
                )
                friction = rng.uniform(*GATE31_FRICTION_RATIO_RANGE)
                mass = rng.uniform(*GATE31_TARGET_MASS_RATIO_RANGE)
                scenarios.append(
                    Gate31Scenario(
                        scenario_id=(
                            f"{pick_object}-{layout}-r{replicate + 1:02d}-s{seed}"
                        ),
                        seed=seed,
                        pick_object=pick_object,
                        layout=layout,
                        replicate=replicate + 1,
                        target_xy_jitter_m=(dx, dy),
                        target_yaw_jitter_deg=yaw,
                        friction_ratio=friction,
                        target_mass_ratio=mass,
                    )
                )
                seed += 1
    return tuple(scenarios)


def _yaw_quaternion(degrees: float) -> tuple[float, float, float, float]:
    half = math.radians(degrees) / 2.0
    return math.cos(half), 0.0, 0.0, math.sin(half)


def _quaternion_multiply(
    left: tuple[float, float, float, float],
    right: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    """Multiply Genesis wxyz quaternions."""

    lw, lx, ly, lz = left
    rw, rx, ry, rz = right
    return (
        lw * rw - lx * rx - ly * ry - lz * rz,
        lw * rx + lx * rw + ly * rz - lz * ry,
        lw * ry - lx * rz + ly * rw + lz * rx,
        lw * rz + lx * ry - ly * rx + lz * rw,
    )


def apply_gate31_scenario(
    snapshot: EpisodeSnapshot,
    scenario: Gate31Scenario,
    *,
    footprint_radii_m: Mapping[str, float],
    clutter_gap_m: float = GATE31_CLUTTER_GAP_M,
) -> EpisodeSnapshot:
    """Create a controlled close-clutter snapshot without initial overlap."""

    if clutter_gap_m < 0.0:
        raise ValueError("clutter_gap_m cannot be negative")
    target = scenario.pick_object
    obstacle = PRIMARY_OBSTACLE_BY_PICK.get(target)
    if obstacle is None:
        raise ValueError(f"unsupported Gate 3.1 pick object: {target}")
    required = set(GATE31_PICK_OBJECTS) | {"024_bowl"}
    missing_poses = sorted(required - snapshot.object_poses.keys())
    missing_radii = sorted({target, obstacle} - footprint_radii_m.keys())
    if missing_poses:
        raise ValueError(f"snapshot is missing Gate 3.1 entities: {missing_poses}")
    if missing_radii:
        raise ValueError(f"missing footprint radii: {missing_radii}")

    poses = dict(snapshot.object_poses)
    base_target = poses[target]
    tx = base_target.position[0] + scenario.target_xy_jitter_m[0]
    ty = base_target.position[1] + scenario.target_xy_jitter_m[1]
    target_quat = _quaternion_multiply(
        _yaw_quaternion(scenario.target_yaw_jitter_deg),
        base_target.quaternion,
    )
    poses[target] = EntityPose(
        position=(tx, ty, base_target.position[2]),
        quaternion=target_quat,
    )

    direction = LAYOUT_DIRECTION_BY_PICK[(target, scenario.layout)]
    separation = (
        float(footprint_radii_m[target])
        + float(footprint_radii_m[obstacle])
        + clutter_gap_m
    )
    base_obstacle = poses[obstacle]
    poses[obstacle] = EntityPose(
        position=(
            tx + direction[0] * separation,
            ty + direction[1] * separation,
            base_obstacle.position[2],
        ),
        quaternion=base_obstacle.quaternion,
    )

    parking_iter = iter(PARKING_POSITIONS)
    for name in (*GATE31_PICK_OBJECTS, "024_bowl"):
        if name in {target, obstacle}:
            continue
        px, py = next(parking_iter)
        pose = poses[name]
        poses[name] = EntityPose(
            position=(px, py, pose.position[2]),
            quaternion=pose.quaternion,
        )

    return EpisodeSnapshot(
        seed=scenario.seed,
        robot_qpos=snapshot.robot_qpos,
        object_poses=poses,
    )


def classify_gate31_execution(
    metrics: CandidateMetrics,
    *,
    minimum_stability: float = GATE31_MINIMUM_STABILITY,
    minimum_safe_clearance_m: float = GATE31_MINIMUM_SAFE_CLEARANCE_M,
) -> ExecutionClassification:
    """Classify task success separately from margin-aware safe completion."""

    if not 0.0 <= minimum_stability <= 1.0:
        raise ValueError("minimum_stability must be in [0, 1]")
    if minimum_safe_clearance_m < 0.0:
        raise ValueError("minimum_safe_clearance_m cannot be negative")
    diagnostic = metrics.clearance_diagnostic
    clutter_contact = bool(diagnostic is not None and diagnostic.overlaps)
    clearance_violation = metrics.collision_margin_m < minimum_safe_clearance_m
    reachable = metrics.reachability >= 1.0
    stable = metrics.predicted_stability >= minimum_stability
    task_succeeded = reachable and stable and not clutter_contact
    safe_completion = task_succeeded and not clearance_violation

    if not reachable:
        failure_type = "unreachable"
    elif clutter_contact:
        failure_type = "clutter_contact"
    elif not stable:
        failure_type = "unstable_lift"
    elif clearance_violation:
        failure_type = "clearance_violation"
    else:
        failure_type = "safe_success"
    return ExecutionClassification(
        task_succeeded=task_succeeded,
        safe_completion=safe_completion,
        failure_type=failure_type,
        clutter_contact=clutter_contact,
        clearance_violation=clearance_violation,
    )


def _strategy_summary(records: Sequence[Mapping[str, object]]) -> dict[str, object]:
    safe = [bool(record["classification"]["safe_completion"]) for record in records]
    task = [bool(record["classification"]["task_succeeded"]) for record in records]
    contacts = [bool(record["classification"]["clutter_contact"]) for record in records]
    stabilities = [
        float(record["execution_metrics"]["predicted_stability"]) for record in records
    ]
    clearances = [
        float(record["execution_metrics"]["collision_margin_m"]) for record in records
    ]
    failures = Counter(
        str(record["classification"]["failure_type"]) for record in records
    )
    selections = Counter(str(record["candidate"]["candidate_id"]) for record in records)
    return {
        "episode_count": len(records),
        "safe_completion_count": sum(safe),
        "safe_completion_rate": fmean(safe) if safe else 0.0,
        "task_success_count": sum(task),
        "task_success_rate": fmean(task) if task else 0.0,
        "clutter_contact_count": sum(contacts),
        "clutter_contact_rate": fmean(contacts) if contacts else 0.0,
        "mean_stability": fmean(stabilities) if stabilities else 0.0,
        "mean_clutter_clearance_m": fmean(clearances) if clearances else 0.0,
        "failure_types": dict(sorted(failures.items())),
        "candidate_selections": dict(sorted(selections.items())),
    }


def summarize_gate31(
    episodes: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Summarize overall and per-cell paired Gate 3.1 results."""

    summary: dict[str, object] = {"episode_count": len(episodes)}
    for strategy in ("baseline", "guardiansim"):
        summary[strategy] = _strategy_summary(
            [episode[strategy] for episode in episodes]
        )
    baseline_rate = float(summary["baseline"]["safe_completion_rate"])
    guardian_rate = float(summary["guardiansim"]["safe_completion_rate"])
    summary["absolute_safe_completion_rate_lift"] = guardian_rate - baseline_rate

    grouped: defaultdict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
    for episode in episodes:
        grouped[(str(episode["pick_object"]), str(episode["layout"]))].append(episode)
    summary["cells"] = {
        f"{pick_object}/{layout}": {
            strategy: _strategy_summary([episode[strategy] for episode in group])
            for strategy in ("baseline", "guardiansim")
        }
        for (pick_object, layout), group in sorted(grouped.items())
    }
    return summary


def validate_gate31_payload(
    payload: Mapping[str, object],
    *,
    require_complete: bool = True,
) -> list[Mapping[str, object]]:
    """Validate protocol identity, scenario order, and independent evidence shape."""

    expected_protocol = gate31_protocol_payload()
    if payload.get("schema_version") != GATE31_SCHEMA_VERSION:
        raise ValueError("Gate 3.1 report must use schema version 4")
    if payload.get("protocol") != expected_protocol:
        raise ValueError("Gate 3.1 protocol does not match the frozen declaration")
    episodes = payload.get("episodes")
    if not isinstance(episodes, list) or not all(
        isinstance(episode, Mapping) for episode in episodes
    ):
        raise ValueError("Gate 3.1 report has no valid episodes list")

    scenarios = generate_gate31_scenarios()
    expected_count = len(scenarios)
    if len(episodes) > expected_count:
        raise ValueError("Gate 3.1 report contains too many episodes")
    if require_complete and len(episodes) != expected_count:
        raise ValueError(
            f"Gate 3.1 report is incomplete: {len(episodes)}/{expected_count}"
        )

    fingerprints = []
    for index, episode in enumerate(episodes):
        scenario = scenarios[index]
        expected_identity = {
            "episode_index": index,
            "seed": scenario.seed,
            "scenario_id": scenario.scenario_id,
            "pick_object": scenario.pick_object,
            "layout": scenario.layout,
            "primary_obstacle": PRIMARY_OBSTACLE_BY_PICK[scenario.pick_object],
            "scenario": scenario_asdict(scenario),
        }
        mismatches = {
            key: (episode.get(key), value)
            for key, value in expected_identity.items()
            if episode.get(key) != value
        }
        if mismatches:
            raise ValueError(
                f"Gate 3.1 episode {index} identity mismatch: {mismatches}"
            )
        fingerprint = episode.get("snapshot_fingerprint")
        if not isinstance(fingerprint, str) or not fingerprint:
            raise ValueError(f"Gate 3.1 episode {index} has no fingerprint")
        fingerprints.append(fingerprint)
        for strategy in ("baseline", "guardiansim"):
            record = episode.get(strategy)
            if not isinstance(record, Mapping):
                raise ValueError(
                    f"Gate 3.1 episode {index} is missing {strategy} evidence"
                )
            if not isinstance(record.get("execution_metrics"), Mapping):
                raise ValueError(
                    f"Gate 3.1 episode {index} has no {strategy} execution metrics"
                )
            if not isinstance(record.get("classification"), Mapping):
                raise ValueError(
                    f"Gate 3.1 episode {index} has no {strategy} classification"
                )
    if len(fingerprints) != len(set(fingerprints)):
        raise ValueError("Gate 3.1 episode fingerprints are not unique")
    return episodes


def scenario_asdict(scenario: Gate31Scenario) -> dict[str, object]:
    """Stable public serialization helper."""

    return asdict(scenario)
