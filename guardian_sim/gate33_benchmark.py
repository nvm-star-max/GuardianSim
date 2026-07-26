"""Pure Gate 3.3 helpers for multi-factor uncertainty breadth testing."""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, replace
from numbers import Real
from statistics import fmean

from guardian_sim.adversarial_benchmark import (
    GATE31_LAYOUTS,
    GATE31_PICK_OBJECTS,
    PRIMARY_OBSTACLE_BY_PICK,
    ExecutionClassification,
    Gate31Scenario,
    apply_gate31_scenario,
)
from guardian_sim.candidates import (
    OBSTACLE_AWARE_YAWS,
    generate_obstacle_aware_candidates,
)
from guardian_sim.gate32_benchmark import (
    GATE32_APPROACH_HEIGHT_M,
    GATE32_CANDIDATE_COUNT,
    GATE32_CONFIRMATION_ROLLOUTS,
    GATE32_MINIMUM_SAFE_CLEARANCE_M,
    GATE32_MINIMUM_STABILITY,
    GATE32_MINIMUM_SUCCESS_MARGIN,
    GATE32_NOMINAL_CANDIDATE_ID,
    GATE32_RETREAT_DISTANCE_M,
    GATE32_SHORTLIST_SIZE,
)
from guardian_sim.models import CandidateMetrics, ClearanceDiagnostic
from guardian_sim.reference_backend import EntityPose, EpisodeSnapshot

GATE33_SCHEMA_VERSION = 6
GATE33_PROTOCOL_NAME = "gate-3.3-multifactor-uncertainty-breadth-smoke"
GATE33_SEED_START = 501
GATE33_PERTURBATION_STRATA = (
    "pose_shift",
    "gap_bearing",
    "dynamics_extreme",
    "perception_bias",
)
GATE33_SCENARIOS_PER_STRATUM = 6
GATE33_EXECUTION_REPEATS = 1
GATE33_TARGET_PERCEPTION_BOUND_M = 0.002
GATE33_OBSTACLE_PERCEPTION_BOUND_M = 0.002
GATE33_HIGH_PERCEPTION_BOUND_M = 0.006
GATE33_STOP_MAX_TASK_FAILURE_RATE = 0.25
GATE33_STOP_MAX_NO_SAFE_CANDIDATE_RATE = 0.20


@dataclass(frozen=True, slots=True)
class Gate33Scenario:
    """One deterministic multi-factor breadth-smoke scenario."""

    scenario_id: str
    seed: int
    stratum: str
    pick_object: str
    layout: str
    target_xy_jitter_m: tuple[float, float]
    target_yaw_jitter_deg: float
    friction_ratio: float
    target_mass_ratio: float
    clutter_gap_m: float
    obstacle_bearing_offset_deg: float
    target_pose_bias_m: tuple[float, float]
    obstacle_pose_bias_m: tuple[float, float]
    target_perception_bound_m: float
    obstacle_perception_bound_m: float

    @property
    def relative_position_uncertainty_bound_m(self) -> float:
        """Worst-case target/obstacle relative-position error."""

        return (
            self.target_perception_bound_m
            + self.obstacle_perception_bound_m
        )


@dataclass(frozen=True, slots=True)
class RiskCertificate:
    """Explain why a measured candidate is or is not safe under uncertainty."""

    observed_clearance_m: float
    relative_position_uncertainty_bound_m: float
    certified_clearance_lower_bound_m: float
    required_clearance_m: float
    observed_stability: float
    required_stability: float
    reachable: bool
    physical_overlap: bool
    hard_safe: bool
    failed_gates: tuple[str, ...]


def _polar_xy(magnitude: float, degrees: float) -> tuple[float, float]:
    radians = math.radians(degrees)
    return magnitude * math.cos(radians), magnitude * math.sin(radians)


def _scenario_parameters(
    stratum: str,
    *,
    rng: random.Random,
    layout_index: int,
) -> dict[str, object]:
    common: dict[str, object] = {
        "target_xy_jitter_m": (
            rng.uniform(-0.010, 0.010),
            rng.uniform(-0.010, 0.010),
        ),
        "target_yaw_jitter_deg": rng.uniform(-15.0, 15.0),
        "friction_ratio": rng.uniform(0.75, 0.95),
        "target_mass_ratio": rng.uniform(0.90, 1.25),
        "clutter_gap_m": 0.012,
        "obstacle_bearing_offset_deg": 0.0,
        "target_pose_bias_m": (0.0, 0.0),
        "obstacle_pose_bias_m": (0.0, 0.0),
        "target_perception_bound_m": GATE33_TARGET_PERCEPTION_BOUND_M,
        "obstacle_perception_bound_m": GATE33_OBSTACLE_PERCEPTION_BOUND_M,
    }
    if stratum == "pose_shift":
        common.update(
            target_xy_jitter_m=(
                rng.uniform(-0.025, 0.025),
                rng.uniform(-0.025, 0.025),
            ),
            target_yaw_jitter_deg=rng.uniform(-35.0, 35.0),
        )
    elif stratum == "gap_bearing":
        common.update(
            clutter_gap_m=(0.006, 0.024)[layout_index],
            obstacle_bearing_offset_deg=(-35.0, 35.0)[layout_index],
        )
    elif stratum == "dynamics_extreme":
        common.update(
            friction_ratio=(0.55, 1.10)[layout_index],
            target_mass_ratio=(1.55, 0.70)[layout_index],
        )
    elif stratum == "perception_bias":
        target_angle = rng.uniform(-180.0, 180.0)
        obstacle_angle = target_angle + rng.uniform(110.0, 250.0)
        common.update(
            target_pose_bias_m=_polar_xy(0.005, target_angle),
            obstacle_pose_bias_m=_polar_xy(0.006, obstacle_angle),
            target_perception_bound_m=GATE33_HIGH_PERCEPTION_BOUND_M,
            obstacle_perception_bound_m=GATE33_HIGH_PERCEPTION_BOUND_M,
        )
    else:
        raise ValueError(f"unsupported Gate 3.3 stratum: {stratum}")
    return common


def generate_gate33_scenarios() -> tuple[Gate33Scenario, ...]:
    """Generate 4 strata x 3 objects x 2 layouts on unseen seeds 501–524."""

    scenarios = []
    seed = GATE33_SEED_START
    for stratum in GATE33_PERTURBATION_STRATA:
        for pick_object in GATE31_PICK_OBJECTS:
            for layout_index, layout in enumerate(GATE31_LAYOUTS):
                rng = random.Random(seed)
                scenarios.append(
                    Gate33Scenario(
                        scenario_id=(
                            f"{stratum}-{pick_object}-{layout}-s{seed}"
                        ),
                        seed=seed,
                        stratum=stratum,
                        pick_object=pick_object,
                        layout=layout,
                        **_scenario_parameters(
                            stratum,
                            rng=rng,
                            layout_index=layout_index,
                        ),
                    )
                )
                seed += 1
    return tuple(scenarios)


def gate33_scenario_asdict(scenario: Gate33Scenario) -> dict[str, object]:
    """Return the JSON-stable scenario identity used by strict validation."""

    return json.loads(json.dumps(asdict(scenario), sort_keys=True))


def gate33_protocol_payload() -> dict[str, object]:
    """Return the immutable reader-facing Gate 3.3 smoke declaration."""

    scenario_matrix = [
        gate33_scenario_asdict(scenario)
        for scenario in generate_gate33_scenarios()
    ]
    matrix_canonical = json.dumps(
        scenario_matrix,
        sort_keys=True,
        separators=(",", ":"),
    )
    payload = {
        "schema_version": GATE33_SCHEMA_VERSION,
        "protocol_name": GATE33_PROTOCOL_NAME,
        "status": "engineering_smoke_not_formal_performance_evidence",
        "pick_objects": list(GATE31_PICK_OBJECTS),
        "layouts": list(GATE31_LAYOUTS),
        "perturbation_strata": list(GATE33_PERTURBATION_STRATA),
        "scenarios_per_stratum": GATE33_SCENARIOS_PER_STRATUM,
        "scenario_count": len(scenario_matrix),
        "seed_start": GATE33_SEED_START,
        "scenario_matrix_sha256": hashlib.sha256(
            matrix_canonical.encode()
        ).hexdigest(),
        "candidate_count": GATE32_CANDIDATE_COUNT,
        "candidate_yaws_degrees": list(OBSTACLE_AWARE_YAWS),
        "obstacle_retreat_distance_m": GATE32_RETREAT_DISTANCE_M,
        "approach_height_m": GATE32_APPROACH_HEIGHT_M,
        "shortlist_size": GATE32_SHORTLIST_SIZE,
        "confirmation_rollouts": GATE32_CONFIRMATION_ROLLOUTS,
        "minimum_stability": GATE32_MINIMUM_STABILITY,
        "minimum_physical_clearance_m": GATE32_MINIMUM_SAFE_CLEARANCE_M,
        "minimum_success_margin": GATE32_MINIMUM_SUCCESS_MARGIN,
        "uncertainty_policy": (
            "subtract_sum_of_target_and_obstacle_position_error_bounds"
        ),
        "unsafe_policy": "replace_or_safe_stop",
        "execution_repeats_per_strategy": GATE33_EXECUTION_REPEATS,
        "primary_diagnostic": "engineering_safe_completion_rate",
        "not_a_claim": (
            "outcomes may find implementation defects but are excluded from "
            "formal performance claims"
        ),
        "stop_conditions": {
            "evaluate_after_each_completed_stratum": (
                GATE33_SCENARIOS_PER_STRATUM
            ),
            "snapshot_or_validator_failure": True,
            "guardian_task_failure_rate_above": (
                GATE33_STOP_MAX_TASK_FAILURE_RATE
            ),
            "unexplained_collision_regression": True,
            "no_hard_safe_candidate_rate_above": (
                GATE33_STOP_MAX_NO_SAFE_CANDIDATE_RATE
            ),
        },
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["protocol_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return payload


def apply_gate33_scenario(
    snapshot: EpisodeSnapshot,
    scenario: Gate33Scenario,
    *,
    footprint_radii_m: Mapping[str, float],
) -> EpisodeSnapshot:
    """Apply physical perturbations while preserving a declared initial gap."""

    gate31_scenario = Gate31Scenario(
        scenario_id=scenario.scenario_id,
        seed=scenario.seed,
        pick_object=scenario.pick_object,
        layout=scenario.layout,
        replicate=1,
        target_xy_jitter_m=scenario.target_xy_jitter_m,
        target_yaw_jitter_deg=scenario.target_yaw_jitter_deg,
        friction_ratio=scenario.friction_ratio,
        target_mass_ratio=scenario.target_mass_ratio,
    )
    challenged = apply_gate31_scenario(
        snapshot,
        gate31_scenario,
        footprint_radii_m=footprint_radii_m,
        clutter_gap_m=scenario.clutter_gap_m,
    )
    if scenario.obstacle_bearing_offset_deg == 0.0:
        return challenged

    target = challenged.object_poses[scenario.pick_object]
    obstacle_name = PRIMARY_OBSTACLE_BY_PICK[scenario.pick_object]
    obstacle = challenged.object_poses[obstacle_name]
    dx = obstacle.position[0] - target.position[0]
    dy = obstacle.position[1] - target.position[1]
    radians = math.radians(scenario.obstacle_bearing_offset_deg)
    rotated_dx = dx * math.cos(radians) - dy * math.sin(radians)
    rotated_dy = dx * math.sin(radians) + dy * math.cos(radians)
    poses = dict(challenged.object_poses)
    poses[obstacle_name] = EntityPose(
        position=(
            target.position[0] + rotated_dx,
            target.position[1] + rotated_dy,
            obstacle.position[2],
        ),
        quaternion=obstacle.quaternion,
    )
    return EpisodeSnapshot(
        seed=challenged.seed,
        robot_qpos=challenged.robot_qpos,
        object_poses=poses,
    )


def perceived_positions(
    scenario: Gate33Scenario,
    target_xyz: tuple[float, float, float],
    obstacle_xyz: tuple[float, float, float],
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Apply deterministic sensor bias to the planner's scene observation."""

    target = (
        target_xyz[0] + scenario.target_pose_bias_m[0],
        target_xyz[1] + scenario.target_pose_bias_m[1],
        target_xyz[2],
    )
    obstacle = (
        obstacle_xyz[0] + scenario.obstacle_pose_bias_m[0],
        obstacle_xyz[1] + scenario.obstacle_pose_bias_m[1],
        obstacle_xyz[2],
    )
    return target, obstacle


def certify_candidate_metrics(
    metrics: CandidateMetrics,
    *,
    relative_position_uncertainty_bound_m: float,
    minimum_clearance_m: float = GATE32_MINIMUM_SAFE_CLEARANCE_M,
    minimum_stability: float = GATE32_MINIMUM_STABILITY,
) -> tuple[CandidateMetrics, RiskCertificate]:
    """Convert a point measurement into a conservative uncertainty certificate."""

    if relative_position_uncertainty_bound_m < 0.0:
        raise ValueError("relative position uncertainty bound cannot be negative")
    if minimum_clearance_m < 0.0:
        raise ValueError("minimum clearance cannot be negative")
    if not 0.0 <= minimum_stability <= 1.0:
        raise ValueError("minimum stability must be in [0, 1]")

    diagnostic = metrics.clearance_diagnostic
    overlaps = bool(diagnostic is not None and diagnostic.overlaps)
    lower_bound = (
        metrics.collision_margin_m
        - relative_position_uncertainty_bound_m
    )
    reachable = metrics.reachability >= 1.0
    failed_gates = []
    if not reachable:
        failed_gates.append("unreachable")
    if metrics.predicted_stability < minimum_stability:
        failed_gates.append("stability_below_minimum")
    if overlaps:
        failed_gates.append("physical_overlap")
    if lower_bound < minimum_clearance_m:
        failed_gates.append("certified_clearance_below_minimum")
    certificate = RiskCertificate(
        observed_clearance_m=metrics.collision_margin_m,
        relative_position_uncertainty_bound_m=(
            relative_position_uncertainty_bound_m
        ),
        certified_clearance_lower_bound_m=lower_bound,
        required_clearance_m=minimum_clearance_m,
        observed_stability=metrics.predicted_stability,
        required_stability=minimum_stability,
        reachable=reachable,
        physical_overlap=overlaps,
        hard_safe=not failed_gates,
        failed_gates=tuple(failed_gates),
    )
    certified = replace(
        metrics,
        collision_margin_m=max(0.0, lower_bound),
        perception_uncertainty=max(
            metrics.perception_uncertainty,
            min(1.0, relative_position_uncertainty_bound_m / 0.05),
        ),
    )
    return certified, certificate


def _candidate_metrics_from_mapping(
    payload: Mapping[str, object],
) -> CandidateMetrics:
    """Reconstruct nested diagnostics from a round-tripped report mapping."""

    values = dict(payload)
    for key in ("clearance_diagnostic", "support_contact_diagnostic"):
        diagnostic = values.get(key)
        if isinstance(diagnostic, Mapping):
            values[key] = ClearanceDiagnostic(**diagnostic)
    return CandidateMetrics(**values)


def generate_gate33_candidates(
    scenario: Gate33Scenario,
    target_xyz: tuple[float, float, float],
    obstacle_xyz: tuple[float, float, float],
):
    """Generate actions from the biased observation, not privileged true poses."""

    perceived_target, perceived_obstacle = perceived_positions(
        scenario,
        target_xyz,
        obstacle_xyz,
    )
    return tuple(
        generate_obstacle_aware_candidates(
            perceived_target,
            perceived_obstacle,
        )
    )


def _strategy_summary(
    records: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    executed = [
        record["execution"]
        for record in records
        if record["execution"] is not None
    ]
    classifications = [item["classification"] for item in executed]
    metrics = [item["execution_metrics"] for item in executed]
    safe = [bool(item["safe_completion"]) for item in classifications]
    task = [bool(item["task_succeeded"]) for item in classifications]
    contacts = [bool(item["clutter_contact"]) for item in classifications]
    failures = Counter(str(item["failure_type"]) for item in classifications)
    failures.update(
        {"safe_stop": sum(bool(record["safe_stopped"]) for record in records)}
    )
    return {
        "episode_count": len(records),
        "execution_count": len(executed),
        "safe_completion_count": sum(safe),
        "safe_completion_rate": fmean(safe) if safe else 0.0,
        "task_success_count": sum(task),
        "task_success_rate": fmean(task) if task else 0.0,
        "clutter_contact_count": sum(contacts),
        "clutter_contact_rate": fmean(contacts) if contacts else 0.0,
        "safe_stop_count": sum(bool(record["safe_stopped"]) for record in records),
        "safe_stop_rate": (
            fmean(bool(record["safe_stopped"]) for record in records)
            if records
            else 0.0
        ),
        "mean_clutter_clearance_m": (
            fmean(float(item["collision_margin_m"]) for item in metrics)
            if metrics
            else 0.0
        ),
        "mean_stability": (
            fmean(float(item["predicted_stability"]) for item in metrics)
            if metrics
            else 0.0
        ),
        "failure_types": {
            key: value
            for key, value in sorted(failures.items())
            if value
        },
    }


def summarize_gate33(
    episodes: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Summarize engineering-only outcomes by strategy and perturbation stratum."""

    summary: dict[str, object] = {"episode_count": len(episodes)}
    for strategy in ("baseline", "guardiansim"):
        summary[strategy] = _strategy_summary(
            [episode[strategy] for episode in episodes]
        )
    summary["absolute_safe_completion_rate_lift"] = (
        float(summary["guardiansim"]["safe_completion_rate"])
        - float(summary["baseline"]["safe_completion_rate"])
    )
    grouped: defaultdict[str, list[Mapping[str, object]]] = defaultdict(list)
    for episode in episodes:
        grouped[str(episode["stratum"])].append(episode)
    summary["strata"] = {
        stratum: {
            strategy: _strategy_summary(
                [episode[strategy] for episode in group]
            )
            for strategy in ("baseline", "guardiansim")
        }
        for stratum, group in sorted(grouped.items())
    }
    return summary


def gate33_stop_reasons(
    episodes: Sequence[Mapping[str, object]],
) -> tuple[str, ...]:
    """Evaluate frozen smoke stop rules after each six-scenario stratum."""

    if not episodes or len(episodes) % GATE33_SCENARIOS_PER_STRATUM:
        return ()
    guardian_records = [episode["guardiansim"] for episode in episodes]
    task_successes = sum(
        bool(record["execution"]["classification"]["task_succeeded"])
        for record in guardian_records
        if record["execution"] is not None
    )
    task_failure_rate = 1.0 - task_successes / len(guardian_records)
    safe_stop_rate = (
        sum(bool(record["safe_stopped"]) for record in guardian_records)
        / len(guardian_records)
    )
    unexplained_regression = any(
        bool(episode["guardiansim"]["execution"])
        and bool(
            episode["guardiansim"]["execution"]["classification"][
                "clutter_contact"
            ]
        )
        and not bool(
            episode["baseline"]["execution"]["classification"][
                "clutter_contact"
            ]
        )
        for episode in episodes
    )
    reasons = []
    if task_failure_rate > GATE33_STOP_MAX_TASK_FAILURE_RATE:
        reasons.append("guardian_task_failure_rate_above_0.25")
    if unexplained_regression:
        reasons.append("unexplained_collision_regression")
    if safe_stop_rate > GATE33_STOP_MAX_NO_SAFE_CANDIDATE_RATE:
        reasons.append("no_hard_safe_candidate_rate_above_0.20")
    return tuple(reasons)


def validate_gate33_payload(
    payload: Mapping[str, object],
    *,
    require_complete: bool = True,
) -> list[Mapping[str, object]]:
    """Strictly validate Gate 3.3 identity, certificates, and executions."""

    if payload.get("schema_version") != GATE33_SCHEMA_VERSION:
        raise ValueError("Gate 3.3 report must use schema version 6")
    if payload.get("protocol") != gate33_protocol_payload():
        raise ValueError("Gate 3.3 protocol does not match the frozen declaration")
    episodes = payload.get("episodes")
    if not isinstance(episodes, list) or not all(
        isinstance(episode, Mapping) for episode in episodes
    ):
        raise ValueError("Gate 3.3 report has no valid episodes list")
    scenarios = generate_gate33_scenarios()
    if payload.get("requested_episode_count") != len(scenarios):
        raise ValueError("Gate 3.3 requested episode count must remain 24")
    if payload.get("seed_start") != GATE33_SEED_START:
        raise ValueError("Gate 3.3 seed start does not match the protocol")
    if payload.get("completed_episode_count") != len(episodes):
        raise ValueError("Gate 3.3 completed episode count mismatch")
    if len(episodes) > len(scenarios):
        raise ValueError("Gate 3.3 report contains too many episodes")
    if require_complete and len(episodes) != len(scenarios):
        raise ValueError(
            f"Gate 3.3 report is incomplete: {len(episodes)}/{len(scenarios)}"
        )

    metric_fields = {field.name for field in fields(CandidateMetrics)}
    certificate_fields = {field.name for field in fields(RiskCertificate)}
    expected_candidate_ids = {
        candidate.candidate_id
        for candidate in generate_obstacle_aware_candidates(
            (0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
        )
    }
    fingerprints = []
    for index, episode in enumerate(episodes):
        scenario = scenarios[index]
        expected_identity = {
            "episode_index": index,
            "seed": scenario.seed,
            "scenario_id": scenario.scenario_id,
            "stratum": scenario.stratum,
            "pick_object": scenario.pick_object,
            "layout": scenario.layout,
            "primary_obstacle": PRIMARY_OBSTACLE_BY_PICK[scenario.pick_object],
            "scenario": gate33_scenario_asdict(scenario),
        }
        mismatches = {
            key: (episode.get(key), value)
            for key, value in expected_identity.items()
            if episode.get(key) != value
        }
        if mismatches:
            raise ValueError(
                f"Gate 3.3 episode {index} identity mismatch: {mismatches}"
            )
        fingerprint = episode.get("snapshot_fingerprint")
        if not isinstance(fingerprint, str) or not fingerprint:
            raise ValueError(f"Gate 3.3 episode {index} has no fingerprint")
        fingerprints.append(fingerprint)
        position_fields = (
            "target_xyz",
            "obstacle_xyz",
            "perceived_target_xyz",
            "perceived_obstacle_xyz",
        )
        if any(
            not isinstance(episode.get(key), (list, tuple))
            or len(episode[key]) != 3
            or not all(isinstance(value, Real) for value in episode[key])
            for key in position_fields
        ):
            raise ValueError(
                f"Gate 3.3 episode {index} has malformed pose evidence"
            )
        expected_perceived = perceived_positions(
            scenario,
            tuple(float(value) for value in episode["target_xyz"]),
            tuple(float(value) for value in episode["obstacle_xyz"]),
        )
        stored_perceived = (
            tuple(float(value) for value in episode["perceived_target_xyz"]),
            tuple(float(value) for value in episode["perceived_obstacle_xyz"]),
        )
        if any(
            not math.isclose(expected, stored, abs_tol=1e-12)
            for expected_pose, stored_pose in zip(
                expected_perceived,
                stored_perceived,
            )
            for expected, stored in zip(expected_pose, stored_pose)
        ):
            raise ValueError(
                f"Gate 3.3 episode {index} true/perceived pose mismatch"
            )
        if not math.isclose(
            float(episode.get("relative_position_uncertainty_bound_m", -1.0)),
            scenario.relative_position_uncertainty_bound_m,
            abs_tol=1e-12,
        ):
            raise ValueError(
                f"Gate 3.3 episode {index} uncertainty-bound mismatch"
            )

        selection = episode.get("selection")
        if not isinstance(selection, Mapping):
            raise ValueError(f"Gate 3.3 episode {index} lacks selection evidence")
        for key in (
            "initial_raw_metrics_by_id",
            "initial_certified_metrics_by_id",
            "initial_risk_certificates_by_id",
        ):
            values = selection.get(key)
            if not isinstance(values, Mapping) or set(values) != expected_candidate_ids:
                raise ValueError(
                    f"Gate 3.3 episode {index} has incomplete {key}"
                )
            expected_fields = (
                certificate_fields
                if key == "initial_risk_certificates_by_id"
                else metric_fields
            )
            if not all(
                isinstance(value, Mapping) and set(value) == expected_fields
                for value in values.values()
            ):
                raise ValueError(
                    f"Gate 3.3 episode {index} has malformed {key}"
                )
        certificates = selection["initial_risk_certificates_by_id"]
        raw_metrics = selection["initial_raw_metrics_by_id"]
        certified_metrics = selection["initial_certified_metrics_by_id"]
        for candidate_id in expected_candidate_ids:
            certificate = certificates[candidate_id]
            certified = certified_metrics[candidate_id]
            expected_certified, expected_certificate = certify_candidate_metrics(
                _candidate_metrics_from_mapping(raw_metrics[candidate_id]),
                relative_position_uncertainty_bound_m=(
                    scenario.relative_position_uncertainty_bound_m
                ),
            )
            expected_certified_payload = json.loads(
                json.dumps(asdict(expected_certified), sort_keys=True)
            )
            expected_certificate_payload = json.loads(
                json.dumps(asdict(expected_certificate), sort_keys=True)
            )
            certified_payload = json.loads(
                json.dumps(certified, sort_keys=True)
            )
            certificate_payload = json.loads(
                json.dumps(certificate, sort_keys=True)
            )
            if (
                certified_payload != expected_certified_payload
                or certificate_payload != expected_certificate_payload
            ):
                raise ValueError(
                    f"Gate 3.3 episode {index} certificate/metric mismatch"
                )
        observations = selection.get("observations_by_id")
        confirmed_ids = selection.get("confirmed_candidate_ids")
        if (
            not isinstance(observations, Mapping)
            or not isinstance(confirmed_ids, list)
            or confirmed_ids != sorted(observations)
            or not set(observations) <= expected_candidate_ids
            or GATE32_NOMINAL_CANDIDATE_ID not in observations
            or len(observations) > GATE32_SHORTLIST_SIZE + 1
        ):
            raise ValueError(
                f"Gate 3.3 episode {index} has invalid confirmation evidence"
            )
        required_observations = GATE32_CONFIRMATION_ROLLOUTS + 1
        for candidate_id, candidate_observations in observations.items():
            if (
                not isinstance(candidate_observations, list)
                or len(candidate_observations) != required_observations
                or not all(
                    isinstance(value, Mapping) and set(value) == metric_fields
                    for value in candidate_observations
                )
                or candidate_observations[0]
                != certified_metrics[candidate_id]
            ):
                raise ValueError(
                    f"Gate 3.3 episode {index} candidate {candidate_id} "
                    f"requires {required_observations} certified observations"
                )

        selected_id = selection.get("selected_candidate_id")
        decision = selection.get("decision")
        if decision not in {
            "safe_stop",
            "unsafe_nominal_replaced",
            "higher_margin_alternative",
            "eligible_nominal_fallback",
        }:
            raise ValueError(f"Gate 3.3 episode {index} has invalid decision")
        timing = episode.get("timing")
        if (
            not isinstance(timing, Mapping)
            or not isinstance(timing.get("planning_wall_seconds"), (int, float))
            or float(timing["planning_wall_seconds"]) < 0.0
            or not isinstance(
                timing.get("baseline_execution_wall_seconds"),
                (int, float),
            )
            or float(timing["baseline_execution_wall_seconds"]) < 0.0
        ):
            raise ValueError(
                f"Gate 3.3 episode {index} has invalid timing evidence"
            )
        for strategy in ("baseline", "guardiansim"):
            record = episode.get(strategy)
            if not isinstance(record, Mapping):
                raise ValueError(
                    f"Gate 3.3 episode {index} lacks {strategy} evidence"
                )
            safe_stopped = bool(record.get("safe_stopped"))
            execution = record.get("execution")
            if strategy == "baseline" and safe_stopped:
                raise ValueError("Gate 3.3 baseline cannot safe-stop")
            if safe_stopped:
                if record.get("candidate") is not None or execution is not None:
                    raise ValueError(
                        f"Gate 3.3 episode {index} safe-stop executed an action"
                    )
            else:
                if not isinstance(record.get("candidate"), Mapping):
                    raise ValueError(
                        f"Gate 3.3 episode {index} lacks {strategy} candidate"
                    )
                if not isinstance(execution, Mapping):
                    raise ValueError(
                        f"Gate 3.3 episode {index} lacks {strategy} execution"
                    )
                metrics = execution.get("execution_metrics")
                classification = execution.get("classification")
                if (
                    not isinstance(metrics, Mapping)
                    or set(metrics) != metric_fields
                    or not isinstance(classification, Mapping)
                    or set(classification)
                    != {field.name for field in fields(ExecutionClassification)}
                ):
                    raise ValueError(
                        f"Gate 3.3 episode {index} has malformed execution"
                    )
        guardian = episode["guardiansim"]
        if bool(guardian["safe_stopped"]) != (decision == "safe_stop"):
            raise ValueError(
                f"Gate 3.3 episode {index} decision/safe-stop mismatch"
            )
        guardian_candidate = guardian.get("candidate")
        guardian_id = (
            guardian_candidate.get("candidate_id")
            if isinstance(guardian_candidate, Mapping)
            else None
        )
        if guardian_id != selected_id:
            raise ValueError(
                f"Gate 3.3 episode {index} selected candidate mismatch"
            )
        if selected_id is not None and selected_id not in observations:
            raise ValueError(
                f"Gate 3.3 episode {index} selected candidate was not confirmed"
            )
        guardian_timing = timing.get("guardiansim_execution_wall_seconds")
        if (
            (guardian["safe_stopped"] and guardian_timing is not None)
            or (
                not guardian["safe_stopped"]
                and (
                    not isinstance(guardian_timing, (int, float))
                    or float(guardian_timing) < 0.0
                )
            )
        ):
            raise ValueError(
                f"Gate 3.3 episode {index} Guardian timing mismatch"
            )
        baseline_candidate = episode["baseline"]["candidate"]
        if (
            not isinstance(baseline_candidate, Mapping)
            or baseline_candidate.get("candidate_id")
            != GATE32_NOMINAL_CANDIDATE_ID
        ):
            raise ValueError(
                f"Gate 3.3 episode {index} baseline is not nominal"
            )
        decision_kind = {
            "safe_stop": None,
            "unsafe_nominal_replaced": "alternative",
            "higher_margin_alternative": "alternative",
            "eligible_nominal_fallback": "nominal",
        }[decision]
        if (
            (decision_kind is None and selected_id is not None)
            or (
                decision_kind == "nominal"
                and selected_id != GATE32_NOMINAL_CANDIDATE_ID
            )
            or (
                decision_kind == "alternative"
                and (
                    selected_id is None
                    or selected_id == GATE32_NOMINAL_CANDIDATE_ID
                )
            )
        ):
            raise ValueError(
                f"Gate 3.3 episode {index} decision/candidate mismatch"
            )
    if len(fingerprints) != len(set(fingerprints)):
        raise ValueError("Gate 3.3 episode fingerprints are not unique")
    expected_stop_reasons = list(gate33_stop_reasons(episodes))
    if payload.get("stop_reasons") != expected_stop_reasons:
        raise ValueError("Gate 3.3 stored stop reasons do not match raw episodes")
    if payload.get("summary") != summarize_gate33(episodes):
        raise ValueError("Gate 3.3 stored summary does not match raw episodes")
    return episodes
