"""Build a scene-held-out surrogate-inference dataset from preserved rollouts."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass

from guardian_sim.adversarial_benchmark import (
    GATE31_LAYOUTS,
    GATE31_PICK_OBJECTS,
)
from guardian_sim.candidates import generate_obstacle_aware_candidates
from guardian_sim.gate32_benchmark import (
    GATE32_MINIMUM_SAFE_CLEARANCE_M,
    GATE32_MINIMUM_STABILITY,
)
from guardian_sim.gate33_benchmark import GATE33_PERTURBATION_STRATA

CRITIC_FEATURE_NAMES = (
    "target_x_m",
    "target_y_m",
    "target_z_m",
    "obstacle_dx_m",
    "obstacle_dy_m",
    "obstacle_distance_m",
    "candidate_yaw_degrees",
    "candidate_lateral_offset_m",
    "candidate_target_offset_x_m",
    "candidate_target_offset_y_m",
    "candidate_approach_height_m",
    "candidate_gripper_width_m",
    "is_nominal",
    *(f"pick_object::{value}" for value in GATE31_PICK_OBJECTS),
    *(f"layout::{value}" for value in GATE31_LAYOUTS),
    "stratum::gate32_formal",
    *(f"stratum::{value}" for value in GATE33_PERTURBATION_STRATA),
    "friction_ratio",
    "target_mass_ratio",
    "clutter_gap_m",
    "obstacle_bearing_offset_deg",
    "relative_position_uncertainty_bound_m",
)
CRITIC_TARGET_NAMES = (
    "hard_safe",
    "collision_margin_m",
    "predicted_stability",
    "path_length_m",
)


@dataclass(frozen=True, slots=True)
class SafetyCriticRow:
    """One unique physical candidate rollout and its scene-level features."""

    source_gate: str
    scenario_id: str
    seed: int
    candidate_id: str
    observation_index: int
    features: tuple[float, ...]
    hard_safe: int
    collision_margin_m: float
    predicted_stability: float
    path_length_m: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return value


def _xyz(value: object, label: str) -> tuple[float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError(f"{label} must contain xyz")
    return tuple(float(item) for item in value)


def _one_hot(value: str, vocabulary: Sequence[str], label: str) -> tuple[float, ...]:
    if value not in vocabulary:
        raise ValueError(f"unsupported {label}: {value}")
    return tuple(float(value == item) for item in vocabulary)


def _scenario_scalar(
    scenario: Mapping[str, object],
    key: str,
    default: float,
) -> float:
    value = scenario.get(key, default)
    if not isinstance(value, (int, float)):
        raise TypeError(f"scenario.{key} must be numeric")
    return float(value)


def _episode_rows(
    raw_episode: object,
    *,
    source_gate: str,
) -> list[SafetyCriticRow]:
    episode = _mapping(raw_episode, f"{source_gate} episode")
    selection = _mapping(episode.get("selection"), "selection")
    if source_gate == "gate32_formal":
        initial_key = "initial_metrics_by_id"
        target_xyz = _xyz(episode.get("target_xyz"), "target_xyz")
        obstacle_xyz = _xyz(episode.get("obstacle_xyz"), "obstacle_xyz")
        stratum = "gate32_formal"
        relative_uncertainty = 0.0
    elif source_gate == "gate33_engineering":
        initial_key = "initial_raw_metrics_by_id"
        target_xyz = _xyz(
            episode.get("perceived_target_xyz"),
            "perceived_target_xyz",
        )
        obstacle_xyz = _xyz(
            episode.get("perceived_obstacle_xyz"),
            "perceived_obstacle_xyz",
        )
        stratum = str(episode.get("stratum"))
        relative_uncertainty = float(
            episode.get("relative_position_uncertainty_bound_m", 0.0)
        )
    else:
        raise ValueError(f"unsupported source gate: {source_gate}")

    pick_object = str(episode.get("pick_object"))
    layout = str(episode.get("layout"))
    scenario = _mapping(episode.get("scenario"), "scenario")
    candidates = {
        candidate.candidate_id: candidate
        for candidate in generate_obstacle_aware_candidates(
            target_xyz,
            obstacle_xyz,
        )
    }
    initial_metrics = _mapping(selection.get(initial_key), initial_key)
    observations_by_id = _mapping(
        selection.get("observations_by_id"),
        "observations_by_id",
    )

    delta_x = obstacle_xyz[0] - target_xyz[0]
    delta_y = obstacle_xyz[1] - target_xyz[1]
    base_features = (
        *target_xyz,
        delta_x,
        delta_y,
        math.hypot(delta_x, delta_y),
    )
    context_features = (
        *_one_hot(pick_object, GATE31_PICK_OBJECTS, "pick object"),
        *_one_hot(layout, GATE31_LAYOUTS, "layout"),
        *_one_hot(
            stratum,
            ("gate32_formal", *GATE33_PERTURBATION_STRATA),
            "stratum",
        ),
        _scenario_scalar(scenario, "friction_ratio", 1.0),
        _scenario_scalar(scenario, "target_mass_ratio", 1.0),
        _scenario_scalar(scenario, "clutter_gap_m", 0.012),
        _scenario_scalar(scenario, "obstacle_bearing_offset_deg", 0.0),
        relative_uncertainty,
    )

    rows: list[SafetyCriticRow] = []
    for candidate_id, raw_initial in sorted(initial_metrics.items()):
        try:
            candidate = candidates[str(candidate_id)]
        except KeyError as error:
            raise ValueError(f"unknown candidate id: {candidate_id}") from error
        candidate_features = (
            candidate.yaw_degrees,
            candidate.lateral_offset_m,
            *candidate.target_offset_xy_m,
            candidate.approach_height_m,
            candidate.gripper_width_m,
            float(candidate.candidate_id == "yaw_+00.0_offset_+0.000"),
        )
        observations: list[object] = [raw_initial]
        extra = observations_by_id.get(candidate_id)
        if extra is not None:
            if not isinstance(extra, list) or not extra:
                raise ValueError(f"observations for {candidate_id} are malformed")
            # The first observation repeats the already-counted initial rollout.
            observations.extend(extra[1:])

        for observation_index, raw_metrics in enumerate(observations):
            metrics = _mapping(raw_metrics, f"metrics for {candidate_id}")
            collision_margin_m = float(metrics["collision_margin_m"])
            predicted_stability = float(metrics["predicted_stability"])
            path_length_m = float(metrics["path_length_m"])
            reachability = float(metrics["reachability"])
            hard_safe = int(
                reachability >= 1.0
                and collision_margin_m >= GATE32_MINIMUM_SAFE_CLEARANCE_M
                and predicted_stability >= GATE32_MINIMUM_STABILITY
            )
            features = (
                *base_features,
                *candidate_features,
                *context_features,
            )
            if len(features) != len(CRITIC_FEATURE_NAMES):
                raise AssertionError("critic feature schema drift")
            rows.append(
                SafetyCriticRow(
                    source_gate=source_gate,
                    scenario_id=str(episode["scenario_id"]),
                    seed=int(episode["seed"]),
                    candidate_id=str(candidate_id),
                    observation_index=observation_index,
                    features=tuple(float(value) for value in features),
                    hard_safe=hard_safe,
                    collision_margin_m=collision_margin_m,
                    predicted_stability=predicted_stability,
                    path_length_m=path_length_m,
                )
            )
    return rows


def extract_safety_critic_rows(
    gate32_payload: Mapping[str, object],
    gate33_payload: Mapping[str, object],
) -> tuple[SafetyCriticRow, ...]:
    """Extract unique rollout rows while preserving scene-group identities."""

    if gate32_payload.get("schema_version") != 5:
        raise ValueError("Gate 3.2 report must use schema 5")
    if gate33_payload.get("schema_version") != 6:
        raise ValueError("Gate 3.3 report must use schema 6")
    gate32_episodes = gate32_payload.get("episodes")
    gate33_episodes = gate33_payload.get("episodes")
    if not isinstance(gate32_episodes, list) or not isinstance(gate33_episodes, list):
        raise TypeError("report episodes must be lists")

    rows = [
        *(
            row
            for episode in gate32_episodes
            for row in _episode_rows(episode, source_gate="gate32_formal")
        ),
        *(
            row
            for episode in gate33_episodes
            for row in _episode_rows(
                episode,
                source_gate="gate33_engineering",
            )
        ),
    ]
    identities = {
        (
            row.source_gate,
            row.seed,
            row.candidate_id,
            row.observation_index,
        )
        for row in rows
    }
    if len(identities) != len(rows):
        raise ValueError("critic dataset contains duplicate rollout identities")
    return tuple(rows)


def split_rows_by_scene(
    rows: Sequence[SafetyCriticRow],
    *,
    test_seed_modulo: int = 5,
    test_seed_remainder: int = 0,
) -> tuple[tuple[SafetyCriticRow, ...], tuple[SafetyCriticRow, ...]]:
    """Create a deterministic seed-held-out split with no scene leakage."""

    if test_seed_modulo < 2:
        raise ValueError("test seed modulo must be at least two")
    train = tuple(
        row
        for row in rows
        if row.seed % test_seed_modulo != test_seed_remainder
    )
    test = tuple(
        row
        for row in rows
        if row.seed % test_seed_modulo == test_seed_remainder
    )
    if not train or not test:
        raise ValueError("scene split produced an empty partition")
    train_scenes = {(row.source_gate, row.seed) for row in train}
    test_scenes = {(row.source_gate, row.seed) for row in test}
    if train_scenes & test_scenes:
        raise AssertionError("scene leakage detected")
    return train, test
