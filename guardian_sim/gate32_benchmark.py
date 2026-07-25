"""Pure Gate 3.2 protocol helpers for repeatable safety evaluation."""

from __future__ import annotations

import hashlib
import json
import random
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields
from statistics import fmean

from guardian_sim.adversarial_benchmark import (
    GATE31_CLUTTER_GAP_M,
    GATE31_FRICTION_RATIO_RANGE,
    GATE31_LAYOUTS,
    GATE31_PICK_OBJECTS,
    GATE31_REPLICATES_PER_CELL,
    GATE31_TARGET_MASS_RATIO_RANGE,
    GATE31_TARGET_XY_JITTER_M,
    GATE31_TARGET_YAW_JITTER_DEG,
    PRIMARY_OBSTACLE_BY_PICK,
    ExecutionClassification,
    Gate31Scenario,
    scenario_asdict,
)
from guardian_sim.candidates import (
    OBSTACLE_AWARE_YAWS,
    generate_obstacle_aware_candidates,
)
from guardian_sim.models import CandidateMetrics

GATE32_SCHEMA_VERSION = 5
GATE32_PROTOCOL_NAME = "gate-3.2-obstacle-aware-repeatable-safety"
GATE32_SEED_START = 401
GATE32_EXECUTION_REPEATS = 3
GATE32_MINIMUM_STABILITY = 0.70
GATE32_MINIMUM_SAFE_CLEARANCE_M = 0.010
GATE32_RETREAT_DISTANCE_M = 0.025
GATE32_APPROACH_HEIGHT_M = 0.14
GATE32_CANDIDATE_COUNT = 18
GATE32_SHORTLIST_SIZE = 5
GATE32_CONFIRMATION_ROLLOUTS = 3
GATE32_MINIMUM_SUCCESS_MARGIN = 0.02
GATE32_NOMINAL_CANDIDATE_ID = "yaw_+00.0_offset_+0.000"


@dataclass(frozen=True, slots=True)
class RepeatableExecutionAggregate:
    """Scenario-level outcome across independent execution repeats."""

    execution_count: int
    task_success_count: int
    safe_completion_count: int
    clutter_contact_count: int
    repeatable_task_success: bool
    repeatable_safe_completion: bool
    failure_type: str


def generate_gate32_scenarios() -> tuple[Gate31Scenario, ...]:
    """Generate a fresh balanced matrix that was not used by Gate 3.1."""

    scenarios = []
    seed = GATE32_SEED_START
    for pick_object in GATE31_PICK_OBJECTS:
        for layout in GATE31_LAYOUTS:
            for replicate in range(GATE31_REPLICATES_PER_CELL):
                rng = random.Random(seed)
                scenarios.append(
                    Gate31Scenario(
                        scenario_id=(
                            f"{pick_object}-{layout}-r{replicate + 1:02d}-s{seed}"
                        ),
                        seed=seed,
                        pick_object=pick_object,
                        layout=layout,
                        replicate=replicate + 1,
                        target_xy_jitter_m=(
                            rng.uniform(
                                -GATE31_TARGET_XY_JITTER_M,
                                GATE31_TARGET_XY_JITTER_M,
                            ),
                            rng.uniform(
                                -GATE31_TARGET_XY_JITTER_M,
                                GATE31_TARGET_XY_JITTER_M,
                            ),
                        ),
                        target_yaw_jitter_deg=rng.uniform(
                            -GATE31_TARGET_YAW_JITTER_DEG,
                            GATE31_TARGET_YAW_JITTER_DEG,
                        ),
                        friction_ratio=rng.uniform(*GATE31_FRICTION_RATIO_RANGE),
                        target_mass_ratio=rng.uniform(
                            *GATE31_TARGET_MASS_RATIO_RANGE
                        ),
                    )
                )
                seed += 1
    return tuple(scenarios)


def gate32_protocol_payload() -> dict[str, object]:
    """Return the immutable reader-facing Gate 3.2 declaration."""

    scenario_matrix = [
        asdict(scenario) for scenario in generate_gate32_scenarios()
    ]
    matrix_canonical = json.dumps(
        scenario_matrix,
        sort_keys=True,
        separators=(",", ":"),
    )
    payload = {
        "schema_version": GATE32_SCHEMA_VERSION,
        "protocol_name": GATE32_PROTOCOL_NAME,
        "pick_objects": list(GATE31_PICK_OBJECTS),
        "layouts": list(GATE31_LAYOUTS),
        "replicates_per_cell": GATE31_REPLICATES_PER_CELL,
        "seed_start": GATE32_SEED_START,
        "target_xy_jitter_m": GATE31_TARGET_XY_JITTER_M,
        "target_yaw_jitter_deg": GATE31_TARGET_YAW_JITTER_DEG,
        "friction_ratio_range": list(GATE31_FRICTION_RATIO_RANGE),
        "target_mass_ratio_range": list(GATE31_TARGET_MASS_RATIO_RANGE),
        "clutter_gap_m": GATE31_CLUTTER_GAP_M,
        "scenario_count": len(scenario_matrix),
        "scenario_matrix_sha256": hashlib.sha256(
            matrix_canonical.encode()
        ).hexdigest(),
        "candidate_count": GATE32_CANDIDATE_COUNT,
        "candidate_yaws_degrees": list(OBSTACLE_AWARE_YAWS),
        "obstacle_retreat_distance_m": GATE32_RETREAT_DISTANCE_M,
        "approach_height_m": GATE32_APPROACH_HEIGHT_M,
        "nominal_approach_height_m": 0.10,
        "gripper_width_m": 0.06,
        "shortlist_size": GATE32_SHORTLIST_SIZE,
        "confirmation_rollouts": GATE32_CONFIRMATION_ROLLOUTS,
        "shortlist_policy": "initial_hard_safe_filter_then_rank",
        "minimum_stability": GATE32_MINIMUM_STABILITY,
        "minimum_safe_clearance_m": GATE32_MINIMUM_SAFE_CLEARANCE_M,
        "minimum_success_margin": GATE32_MINIMUM_SUCCESS_MARGIN,
        "execution_repeats_per_strategy": GATE32_EXECUTION_REPEATS,
        "unsafe_nominal_policy": "replace_or_safe_stop",
        "primary_endpoint": "paired_repeatable_safe_completion_rate",
        "secondary_endpoints": [
            "per_execution_safe_completion_rate",
            "repeatable_task_success_rate",
            "clutter_contact_rate",
            "safe_stop_rate",
            "mean_clutter_clearance_m",
            "mean_stability",
        ],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["protocol_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return payload


def aggregate_repeatable_executions(
    executions: Sequence[ExecutionClassification],
    *,
    required_repeats: int = GATE32_EXECUTION_REPEATS,
) -> RepeatableExecutionAggregate:
    """Require every independent execution to satisfy the scenario outcome."""

    if required_repeats < 1:
        raise ValueError("required_repeats must be positive")
    if len(executions) != required_repeats:
        raise ValueError(
            f"expected {required_repeats} executions, received {len(executions)}"
        )
    task_success_count = sum(item.task_succeeded for item in executions)
    safe_completion_count = sum(item.safe_completion for item in executions)
    clutter_contact_count = sum(item.clutter_contact for item in executions)
    first_failure = next(
        (
            item.failure_type
            for item in executions
            if item.failure_type != "safe_success"
        ),
        "safe_success",
    )
    return RepeatableExecutionAggregate(
        execution_count=len(executions),
        task_success_count=task_success_count,
        safe_completion_count=safe_completion_count,
        clutter_contact_count=clutter_contact_count,
        repeatable_task_success=task_success_count == required_repeats,
        repeatable_safe_completion=safe_completion_count == required_repeats,
        failure_type=first_failure,
    )


def safe_stop_aggregate() -> RepeatableExecutionAggregate:
    """Represent a deliberate non-execution when no action meets the safety gate."""

    return RepeatableExecutionAggregate(
        execution_count=0,
        task_success_count=0,
        safe_completion_count=0,
        clutter_contact_count=0,
        repeatable_task_success=False,
        repeatable_safe_completion=False,
        failure_type="safe_stop",
    )


def _strategy_summary(
    records: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    aggregates = [record["aggregate"] for record in records]
    repeatable_safe = [
        bool(item["repeatable_safe_completion"]) for item in aggregates
    ]
    repeatable_task = [
        bool(item["repeatable_task_success"]) for item in aggregates
    ]
    executions = [
        execution
        for record in records
        for execution in record["executions"]
    ]
    execution_safe = [
        bool(item["classification"]["safe_completion"]) for item in executions
    ]
    execution_task = [
        bool(item["classification"]["task_succeeded"]) for item in executions
    ]
    contacts = [
        bool(item["classification"]["clutter_contact"]) for item in executions
    ]
    clearances = [
        float(item["execution_metrics"]["collision_margin_m"])
        for item in executions
    ]
    stabilities = [
        float(item["execution_metrics"]["predicted_stability"])
        for item in executions
    ]
    failures = Counter(str(item["failure_type"]) for item in aggregates)
    selections = Counter(
        (
            str(record["candidate"]["candidate_id"])
            if record["candidate"] is not None
            else "safe_stop"
        )
        for record in records
    )
    return {
        "episode_count": len(records),
        "repeatable_safe_completion_count": sum(repeatable_safe),
        "repeatable_safe_completion_rate": (
            fmean(repeatable_safe) if repeatable_safe else 0.0
        ),
        "repeatable_task_success_count": sum(repeatable_task),
        "repeatable_task_success_rate": (
            fmean(repeatable_task) if repeatable_task else 0.0
        ),
        "safe_stop_count": sum(bool(record["safe_stopped"]) for record in records),
        "safe_stop_rate": (
            fmean(bool(record["safe_stopped"]) for record in records)
            if records
            else 0.0
        ),
        "execution_count": len(executions),
        "execution_safe_completion_count": sum(execution_safe),
        "execution_safe_completion_rate": (
            fmean(execution_safe) if execution_safe else 0.0
        ),
        "execution_task_success_count": sum(execution_task),
        "execution_task_success_rate": (
            fmean(execution_task) if execution_task else 0.0
        ),
        "clutter_contact_count": sum(contacts),
        "clutter_contact_rate": fmean(contacts) if contacts else 0.0,
        "mean_clutter_clearance_m": fmean(clearances) if clearances else 0.0,
        "mean_stability": fmean(stabilities) if stabilities else 0.0,
        "failure_types": dict(sorted(failures.items())),
        "candidate_selections": dict(sorted(selections.items())),
    }


def summarize_gate32(
    episodes: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Summarize repeatable scenario outcomes and individual executions."""

    summary: dict[str, object] = {"episode_count": len(episodes)}
    for strategy in ("baseline", "guardiansim"):
        summary[strategy] = _strategy_summary(
            [episode[strategy] for episode in episodes]
        )
    summary["absolute_repeatable_safe_completion_rate_lift"] = (
        float(summary["guardiansim"]["repeatable_safe_completion_rate"])
        - float(summary["baseline"]["repeatable_safe_completion_rate"])
    )
    grouped: defaultdict[
        tuple[str, str], list[Mapping[str, object]]
    ] = defaultdict(list)
    for episode in episodes:
        grouped[(str(episode["pick_object"]), str(episode["layout"]))].append(
            episode
        )
    summary["cells"] = {
        f"{pick_object}/{layout}": {
            strategy: _strategy_summary([episode[strategy] for episode in group])
            for strategy in ("baseline", "guardiansim")
        }
        for (pick_object, layout), group in sorted(grouped.items())
    }
    return summary


def validate_gate32_payload(
    payload: Mapping[str, object],
    *,
    require_complete: bool = True,
) -> list[Mapping[str, object]]:
    """Validate protocol identity, order, repeats, and safe-stop evidence."""

    if payload.get("schema_version") != GATE32_SCHEMA_VERSION:
        raise ValueError("Gate 3.2 report must use schema version 5")
    if payload.get("protocol") != gate32_protocol_payload():
        raise ValueError("Gate 3.2 protocol does not match the frozen declaration")
    episodes = payload.get("episodes")
    if not isinstance(episodes, list) or not all(
        isinstance(episode, Mapping) for episode in episodes
    ):
        raise ValueError("Gate 3.2 report has no valid episodes list")
    scenarios = generate_gate32_scenarios()
    if payload.get("requested_episode_count") != len(scenarios):
        raise ValueError("Gate 3.2 requested episode count must remain 30")
    if payload.get("seed_start") != GATE32_SEED_START:
        raise ValueError("Gate 3.2 seed start does not match the frozen protocol")
    if payload.get("completed_episode_count") != len(episodes):
        raise ValueError(
            "Gate 3.2 completed episode count does not match raw episodes"
        )
    if len(episodes) > len(scenarios):
        raise ValueError("Gate 3.2 report contains too many episodes")
    if require_complete and len(episodes) != len(scenarios):
        raise ValueError(
            f"Gate 3.2 report is incomplete: {len(episodes)}/{len(scenarios)}"
        )

    fingerprints = []
    metric_fields = {field.name for field in fields(CandidateMetrics)}

    def has_complete_metrics(value: object) -> bool:
        return isinstance(value, Mapping) and set(value) == metric_fields

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
                f"Gate 3.2 episode {index} identity mismatch: {mismatches}"
            )
        fingerprint = episode.get("snapshot_fingerprint")
        if not isinstance(fingerprint, str) or not fingerprint:
            raise ValueError(f"Gate 3.2 episode {index} has no fingerprint")
        fingerprints.append(fingerprint)

        selection = episode.get("selection")
        if not isinstance(selection, Mapping):
            raise ValueError(f"Gate 3.2 episode {index} has no selection evidence")
        timing = episode.get("timing")
        if (
            not isinstance(timing, Mapping)
            or not isinstance(timing.get("planning_wall_seconds"), (int, float))
            or float(timing["planning_wall_seconds"]) < 0.0
        ):
            raise ValueError(f"Gate 3.2 episode {index} has invalid timing evidence")
        expected_candidate_ids = {
            candidate.candidate_id
            for candidate in generate_obstacle_aware_candidates(
                (0.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
            )
        }
        initial_metrics = selection.get("initial_metrics_by_id")
        if not isinstance(initial_metrics, Mapping) or set(
            initial_metrics
        ) != expected_candidate_ids:
            raise ValueError(
                f"Gate 3.2 episode {index} must preserve all "
                f"{GATE32_CANDIDATE_COUNT} initial candidate metrics"
            )
        if not all(
            has_complete_metrics(metrics)
            for metrics in initial_metrics.values()
        ):
            raise ValueError(
                f"Gate 3.2 episode {index} has malformed initial metrics"
            )
        observations_by_id = selection.get("observations_by_id")
        confirmed_candidate_ids = selection.get("confirmed_candidate_ids")
        if not isinstance(observations_by_id, Mapping):
            raise ValueError(
                f"Gate 3.2 episode {index} has no confirmation evidence"
            )
        if (
            not isinstance(confirmed_candidate_ids, list)
            or confirmed_candidate_ids != sorted(observations_by_id)
        ):
            raise ValueError(
                f"Gate 3.2 episode {index} confirmed candidate index mismatch"
            )
        confirmed_ids = set(observations_by_id)
        if (
            not confirmed_ids
            or not confirmed_ids <= expected_candidate_ids
            or GATE32_NOMINAL_CANDIDATE_ID not in confirmed_ids
            or len(confirmed_ids) > GATE32_SHORTLIST_SIZE + 1
        ):
            raise ValueError(
                f"Gate 3.2 episode {index} has an invalid confirmed shortlist"
            )
        required_observations = GATE32_CONFIRMATION_ROLLOUTS + 1
        for candidate_id, observations in observations_by_id.items():
            if (
                not isinstance(observations, list)
                or len(observations) != required_observations
                or not all(
                    has_complete_metrics(observation)
                    for observation in observations
                )
            ):
                raise ValueError(
                    f"Gate 3.2 episode {index} candidate {candidate_id} "
                    f"requires {required_observations} observations"
                )
            if observations[0] != initial_metrics[candidate_id]:
                raise ValueError(
                    f"Gate 3.2 episode {index} candidate {candidate_id} "
                    "confirmation does not begin with its initial observation"
                )
        for strategy in ("baseline", "guardiansim"):
            record = episode.get(strategy)
            if not isinstance(record, Mapping):
                raise ValueError(
                    f"Gate 3.2 episode {index} is missing {strategy} evidence"
                )
            safe_stopped = bool(record.get("safe_stopped"))
            executions = record.get("executions")
            if not isinstance(executions, list):
                raise ValueError(
                    f"Gate 3.2 episode {index} has invalid {strategy} executions"
                )
            if strategy == "baseline" and safe_stopped:
                raise ValueError("Gate 3.2 baseline cannot safe-stop")
            if safe_stopped:
                if record.get("candidate") is not None or executions:
                    raise ValueError(
                        f"Gate 3.2 episode {index} safe-stop executed an action"
                    )
                expected_aggregate = asdict(safe_stop_aggregate())
            else:
                if not isinstance(record.get("candidate"), Mapping):
                    raise ValueError(
                        f"Gate 3.2 episode {index} has no {strategy} candidate"
                    )
                if len(executions) != GATE32_EXECUTION_REPEATS:
                    raise ValueError(
                        f"Gate 3.2 episode {index} requires "
                        f"{GATE32_EXECUTION_REPEATS} {strategy} executions"
                    )
                if [
                    execution.get("repeat_index")
                    if isinstance(execution, Mapping)
                    else None
                    for execution in executions
                ] != list(range(GATE32_EXECUTION_REPEATS)):
                    raise ValueError(
                        f"Gate 3.2 episode {index} {strategy} repeat indices "
                        "must be unique and ordered"
                    )
                classifications = []
                for execution in executions:
                    if not isinstance(execution, Mapping):
                        raise ValueError(
                            f"Gate 3.2 episode {index} has malformed execution"
                        )
                    metrics = execution.get("execution_metrics")
                    classification = execution.get("classification")
                    if not has_complete_metrics(metrics) or not isinstance(
                        classification, Mapping
                    ):
                        raise ValueError(
                            f"Gate 3.2 episode {index} lacks physical evidence"
                        )
                    classifications.append(
                        ExecutionClassification(**classification)
                    )
                expected_aggregate = asdict(
                    aggregate_repeatable_executions(classifications)
                )
            execution_timings = timing.get(
                f"{strategy}_execution_wall_seconds"
            )
            if (
                not isinstance(execution_timings, list)
                or len(execution_timings) != len(executions)
                or not all(
                    isinstance(value, (int, float)) and float(value) >= 0.0
                    for value in execution_timings
                )
            ):
                raise ValueError(
                    f"Gate 3.2 episode {index} has invalid {strategy} timing "
                    "evidence"
                )
            if record.get("aggregate") != expected_aggregate:
                raise ValueError(
                    f"Gate 3.2 episode {index} {strategy} aggregate mismatch"
                )
        guardian_stopped = bool(episode["guardiansim"]["safe_stopped"])
        if guardian_stopped != (selection.get("decision") == "safe_stop"):
            raise ValueError(
                f"Gate 3.2 episode {index} selection/safe-stop mismatch"
            )
        baseline_candidate_id = episode["baseline"]["candidate"].get(
            "candidate_id"
        )
        if baseline_candidate_id != GATE32_NOMINAL_CANDIDATE_ID:
            raise ValueError(
                f"Gate 3.2 episode {index} baseline is not the frozen nominal"
            )
        guardian_candidate = episode["guardiansim"].get("candidate")
        guardian_candidate_id = (
            guardian_candidate.get("candidate_id")
            if isinstance(guardian_candidate, Mapping)
            else None
        )
        selected_candidate_id = selection.get("selected_candidate_id")
        if (
            selected_candidate_id != guardian_candidate_id
            or (
                selected_candidate_id is not None
                and selected_candidate_id not in confirmed_ids
            )
        ):
            raise ValueError(
                f"Gate 3.2 episode {index} selected candidate mismatch"
            )
        expected_decisions = {
            "safe_stop": None,
            "unsafe_nominal_replaced": "alternative",
            "higher_margin_alternative": "alternative",
            "eligible_nominal_fallback": "nominal",
        }
        decision = selection.get("decision")
        decision_kind = expected_decisions.get(decision)
        if decision not in expected_decisions:
            raise ValueError(
                f"Gate 3.2 episode {index} has an invalid selection decision"
            )
        if (
            (decision_kind is None and selected_candidate_id is not None)
            or (
                decision_kind == "nominal"
                and selected_candidate_id != GATE32_NOMINAL_CANDIDATE_ID
            )
            or (
                decision_kind == "alternative"
                and (
                    selected_candidate_id is None
                    or selected_candidate_id == GATE32_NOMINAL_CANDIDATE_ID
                )
            )
        ):
            raise ValueError(
                f"Gate 3.2 episode {index} decision/candidate mismatch"
            )

    if len(fingerprints) != len(set(fingerprints)):
        raise ValueError("Gate 3.2 episode fingerprints are not unique")
    expected_summary = summarize_gate32(episodes)
    if payload.get("summary") != expected_summary:
        raise ValueError("stored Gate 3.2 summary does not match raw episodes")
    return episodes
