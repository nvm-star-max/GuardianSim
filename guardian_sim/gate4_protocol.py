"""Draft, outcome-blind protocol helpers for the large-sample Gate 4 run."""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict, dataclass

from guardian_sim.adversarial_benchmark import (
    GATE31_LAYOUTS,
    GATE31_PICK_OBJECTS,
)
from guardian_sim.candidates import generate_obstacle_aware_candidates
from guardian_sim.gate32_benchmark import (
    GATE32_APPROACH_HEIGHT_M,
    GATE32_CONFIRMATION_ROLLOUTS,
    GATE32_EXECUTION_REPEATS,
    GATE32_MINIMUM_SAFE_CLEARANCE_M,
    GATE32_MINIMUM_STABILITY,
    GATE32_MINIMUM_SUCCESS_MARGIN,
    GATE32_RETREAT_DISTANCE_M,
    GATE32_SHORTLIST_SIZE,
)
from guardian_sim.gate33_benchmark import GATE33_PERTURBATION_STRATA
from guardian_sim.models import ActionCandidate

GATE4_SCHEMA_VERSION = 7
GATE4_PROTOCOL_NAME = "gate-4.0-sharded-large-sample-robustness"
GATE4_SEED_START = 1001
GATE4_SCENARIOS_PER_CELL = 10
GATE4_SCENARIOS_PER_STRATUM = (
    len(GATE31_PICK_OBJECTS)
    * len(GATE31_LAYOUTS)
    * GATE4_SCENARIOS_PER_CELL
)
GATE4_SCENARIO_COUNT = (
    len(GATE33_PERTURBATION_STRATA) * GATE4_SCENARIOS_PER_STRATUM
)
GATE4_BASE_CANDIDATE_COUNT = 18
GATE4_EXPANSION_RETREAT_DISTANCES_M = (0.0125, 0.0375)
GATE4_EXPANSION_CANDIDATE_COUNT = 18
GATE4_MAX_CANDIDATE_COUNT = 36
GATE4_PRIMARY_MINIMUM_LIFT = 0.15
GATE4_MAXIMUM_TASK_COMPLETION_REGRESSION = 0.05
GATE4_MINIMUM_CONTACT_REDUCTION = 0.50
GATE4_SIGNIFICANCE_LEVEL = 0.05


@dataclass(frozen=True, slots=True)
class Gate4Scenario:
    """One deterministic scene in the outcome-blind Gate 4 matrix."""

    scenario_id: str
    seed: int
    stratum: str
    pick_object: str
    layout: str
    replicate: int
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
        return (
            self.target_perception_bound_m
            + self.obstacle_perception_bound_m
        )


@dataclass(frozen=True, slots=True)
class PairedOutcomeCounts:
    """The four paired cells used by an exact McNemar test."""

    both_safe: int
    baseline_only_safe: int
    guardian_only_safe: int
    neither_safe: int

    @property
    def episode_count(self) -> int:
        return (
            self.both_safe
            + self.baseline_only_safe
            + self.guardian_only_safe
            + self.neither_safe
        )


def _polar_xy(magnitude: float, degrees: float) -> tuple[float, float]:
    radians = math.radians(degrees)
    return magnitude * math.cos(radians), magnitude * math.sin(radians)


def _scenario_parameters(
    stratum: str,
    *,
    rng: random.Random,
    layout_index: int,
    replicate_index: int,
) -> dict[str, object]:
    parameters: dict[str, object] = {
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
        "target_perception_bound_m": 0.002,
        "obstacle_perception_bound_m": 0.002,
    }
    difficulty_index = replicate_index % 5
    if stratum == "pose_shift":
        parameters.update(
            target_xy_jitter_m=(
                rng.uniform(-0.025, 0.025),
                rng.uniform(-0.025, 0.025),
            ),
            target_yaw_jitter_deg=rng.uniform(-35.0, 35.0),
        )
    elif stratum == "gap_bearing":
        parameters.update(
            clutter_gap_m=(0.008, 0.010, 0.012, 0.018, 0.024)[
                difficulty_index
            ],
            obstacle_bearing_offset_deg=(
                (-35.0, 35.0)[layout_index] + rng.uniform(-10.0, 10.0)
            ),
        )
    elif stratum == "dynamics_extreme":
        parameters.update(
            friction_ratio=(0.55, 0.65, 0.75, 0.90, 1.10)[difficulty_index],
            target_mass_ratio=(1.55, 1.35, 1.10, 0.85, 0.70)[
                difficulty_index
            ],
        )
    elif stratum == "perception_bias":
        target_angle = rng.uniform(-180.0, 180.0)
        obstacle_angle = target_angle + rng.uniform(110.0, 250.0)
        bias_magnitude = (0.002, 0.003, 0.004, 0.005, 0.006)[
            difficulty_index
        ]
        parameters.update(
            target_pose_bias_m=_polar_xy(bias_magnitude, target_angle),
            obstacle_pose_bias_m=_polar_xy(
                bias_magnitude,
                obstacle_angle,
            ),
            target_perception_bound_m=bias_magnitude,
            obstacle_perception_bound_m=bias_magnitude,
        )
    else:
        raise ValueError(f"unsupported Gate 4 stratum: {stratum}")
    return parameters


def generate_gate4_scenarios() -> tuple[Gate4Scenario, ...]:
    """Generate 4 strata × 3 objects × 2 layouts × 10 new seeds."""

    scenarios: list[Gate4Scenario] = []
    seed = GATE4_SEED_START
    for stratum in GATE33_PERTURBATION_STRATA:
        for pick_object in GATE31_PICK_OBJECTS:
            for layout_index, layout in enumerate(GATE31_LAYOUTS):
                for replicate_index in range(GATE4_SCENARIOS_PER_CELL):
                    rng = random.Random(seed)
                    scenarios.append(
                        Gate4Scenario(
                            scenario_id=(
                                f"{stratum}-{pick_object}-{layout}"
                                f"-r{replicate_index + 1:02d}-s{seed}"
                            ),
                            seed=seed,
                            stratum=stratum,
                            pick_object=pick_object,
                            layout=layout,
                            replicate=replicate_index + 1,
                            **_scenario_parameters(
                                stratum,
                                rng=rng,
                                layout_index=layout_index,
                                replicate_index=replicate_index,
                            ),
                        )
                    )
                    seed += 1
    return tuple(scenarios)


def generate_gate4_candidates(
    target_xyz: tuple[float, float, float],
    obstacle_xyz: tuple[float, float, float],
    *,
    include_expansion: bool,
) -> tuple[ActionCandidate, ...]:
    """Return the base family and optionally the outcome-blind retreat expansion."""

    candidates = list(
        generate_obstacle_aware_candidates(
            target_xyz,
            obstacle_xyz,
            retreat_distance_m=GATE32_RETREAT_DISTANCE_M,
        )
    )
    if include_expansion:
        for retreat_distance_m in GATE4_EXPANSION_RETREAT_DISTANCES_M:
            candidates.extend(
                generate_obstacle_aware_candidates(
                    target_xyz,
                    obstacle_xyz,
                    retreat_distance_m=retreat_distance_m,
                )
            )
    deduplicated: dict[str, ActionCandidate] = {}
    for candidate in candidates:
        deduplicated.setdefault(candidate.candidate_id, candidate)
    return tuple(deduplicated.values())


def gate4_workload_budget() -> dict[str, int]:
    """Return declared counts without pretending nested traces are scenes."""

    base_screening = GATE4_SCENARIO_COUNT * GATE4_BASE_CANDIDATE_COUNT
    maximum_screening = GATE4_SCENARIO_COUNT * GATE4_MAX_CANDIDATE_COUNT
    maximum_confirmed_candidates = GATE32_SHORTLIST_SIZE + 1
    maximum_confirmations = (
        GATE4_SCENARIO_COUNT
        * maximum_confirmed_candidates
        * GATE32_CONFIRMATION_ROLLOUTS
    )
    final_executions = (
        GATE4_SCENARIO_COUNT * 2 * GATE32_EXECUTION_REPEATS
    )
    return {
        "independent_paired_scenes": GATE4_SCENARIO_COUNT,
        "base_candidate_screening_rollouts": base_screening,
        "maximum_candidate_screening_rollouts": maximum_screening,
        "maximum_confirmation_rollouts": maximum_confirmations,
        "planned_final_executions": final_executions,
        "maximum_total_simulated_action_traces": (
            maximum_screening + maximum_confirmations + final_executions
        ),
    }


def gate4_protocol_payload() -> dict[str, object]:
    """Return the exact outcome-blind draft declaration and source hashes."""

    scenarios = [asdict(scenario) for scenario in generate_gate4_scenarios()]
    matrix_canonical = json.dumps(
        scenarios,
        sort_keys=True,
        separators=(",", ":"),
    )
    payload: dict[str, object] = {
        "schema_version": GATE4_SCHEMA_VERSION,
        "protocol_name": GATE4_PROTOCOL_NAME,
        "status": "draft_outcome_blind_not_yet_executed",
        "seed_start": GATE4_SEED_START,
        "scenario_count": GATE4_SCENARIO_COUNT,
        "scenarios_per_cell": GATE4_SCENARIOS_PER_CELL,
        "scenarios_per_stratum_shard": GATE4_SCENARIOS_PER_STRATUM,
        "pick_objects": list(GATE31_PICK_OBJECTS),
        "layouts": list(GATE31_LAYOUTS),
        "perturbation_strata": list(GATE33_PERTURBATION_STRATA),
        "scenario_matrix_sha256": hashlib.sha256(
            matrix_canonical.encode()
        ).hexdigest(),
        "base_candidate_count": GATE4_BASE_CANDIDATE_COUNT,
        "adaptive_expansion_candidate_count": (
            GATE4_EXPANSION_CANDIDATE_COUNT
        ),
        "maximum_candidate_count": GATE4_MAX_CANDIDATE_COUNT,
        "adaptive_expansion_trigger": (
            "no_hard_safe_candidate_after_base_family"
        ),
        "expansion_retreat_distances_m": list(
            GATE4_EXPANSION_RETREAT_DISTANCES_M
        ),
        "shortlist_size": GATE32_SHORTLIST_SIZE,
        "confirmation_rollouts": GATE32_CONFIRMATION_ROLLOUTS,
        "execution_repeats_per_strategy": GATE32_EXECUTION_REPEATS,
        "minimum_stability": GATE32_MINIMUM_STABILITY,
        "minimum_certified_clearance_m": (
            GATE32_MINIMUM_SAFE_CLEARANCE_M
        ),
        "minimum_success_margin": GATE32_MINIMUM_SUCCESS_MARGIN,
        "approach_height_m": GATE32_APPROACH_HEIGHT_M,
        "unsafe_policy": "replace_or_safe_stop",
        "primary_endpoint": "paired_repeatable_safe_completion_rate",
        "primary_test": "two_sided_exact_mcnemar",
        "significance_level": GATE4_SIGNIFICANCE_LEVEL,
        "minimum_absolute_lift": GATE4_PRIMARY_MINIMUM_LIFT,
        "maximum_task_completion_regression": (
            GATE4_MAXIMUM_TASK_COMPLETION_REGRESSION
        ),
        "minimum_clutter_contact_reduction": (
            GATE4_MINIMUM_CONTACT_REDUCTION
        ),
        "sharding_policy": (
            "four_sequential_stratum_reports_with_independent_snapshot_identity"
        ),
        "workload_budget": gate4_workload_budget(),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["protocol_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return payload


def validate_gate4_protocol() -> tuple[Gate4Scenario, ...]:
    """Reject matrix drift before any Radeon outcome is observed."""

    scenarios = generate_gate4_scenarios()
    if len(scenarios) != GATE4_SCENARIO_COUNT:
        raise ValueError("Gate 4 scenario count drift")
    if len({scenario.scenario_id for scenario in scenarios}) != len(scenarios):
        raise ValueError("Gate 4 scenario IDs are not unique")
    if len({scenario.seed for scenario in scenarios}) != len(scenarios):
        raise ValueError("Gate 4 seeds are not unique")
    if min(scenario.seed for scenario in scenarios) != GATE4_SEED_START:
        raise ValueError("Gate 4 seed start drift")
    if max(scenario.seed for scenario in scenarios) != (
        GATE4_SEED_START + GATE4_SCENARIO_COUNT - 1
    ):
        raise ValueError("Gate 4 seed range drift")
    cell_counts = Counter(
        (scenario.stratum, scenario.pick_object, scenario.layout)
        for scenario in scenarios
    )
    if set(cell_counts.values()) != {GATE4_SCENARIOS_PER_CELL}:
        raise ValueError("Gate 4 cell balance drift")
    shard_counts = Counter(scenario.stratum for scenario in scenarios)
    if set(shard_counts.values()) != {GATE4_SCENARIOS_PER_STRATUM}:
        raise ValueError("Gate 4 shard balance drift")
    if any(scenario.clutter_gap_m <= 0.0 for scenario in scenarios):
        raise ValueError("Gate 4 contains a non-positive clutter gap")
    return scenarios


def paired_outcome_counts(
    baseline_safe: Sequence[bool],
    guardian_safe: Sequence[bool],
) -> PairedOutcomeCounts:
    """Count paired outcomes without treating repeats as independent scenes."""

    if len(baseline_safe) != len(guardian_safe):
        raise ValueError("paired outcomes must have equal lengths")
    both = baseline_only = guardian_only = neither = 0
    for baseline, guardian in zip(baseline_safe, guardian_safe):
        if baseline and guardian:
            both += 1
        elif baseline:
            baseline_only += 1
        elif guardian:
            guardian_only += 1
        else:
            neither += 1
    return PairedOutcomeCounts(
        both_safe=both,
        baseline_only_safe=baseline_only,
        guardian_only_safe=guardian_only,
        neither_safe=neither,
    )


def exact_mcnemar_p_value(counts: PairedOutcomeCounts) -> float:
    """Return the two-sided exact McNemar p-value for discordant pairs."""

    discordant = counts.baseline_only_safe + counts.guardian_only_safe
    if discordant == 0:
        return 1.0
    smaller = min(
        counts.baseline_only_safe,
        counts.guardian_only_safe,
    )
    tail = sum(
        math.comb(discordant, index)
        for index in range(smaller + 1)
    ) / (2**discordant)
    return min(1.0, 2.0 * tail)
