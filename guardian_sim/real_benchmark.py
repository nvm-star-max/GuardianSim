"""Pure helpers for fixed-seed Genesis baseline-vs-GuardianSim evaluation."""

from __future__ import annotations

import random
from collections import Counter
from collections.abc import Mapping, Sequence
from statistics import fmean

from guardian_sim.models import CandidateMetrics
from guardian_sim.reference_backend import EntityPose, EpisodeSnapshot


def perturb_snapshot(
    snapshot: EpisodeSnapshot,
    *,
    seed: int,
    xy_jitter_m: float,
) -> EpisodeSnapshot:
    """Apply deterministic XY object-pose jitter while preserving robot state."""

    if xy_jitter_m < 0.0:
        raise ValueError("xy_jitter_m cannot be negative")
    rng = random.Random(seed)
    object_poses = {}
    for name, pose in sorted(snapshot.object_poses.items()):
        x, y, z = pose.position
        object_poses[name] = EntityPose(
            position=(
                x + rng.uniform(-xy_jitter_m, xy_jitter_m),
                y + rng.uniform(-xy_jitter_m, xy_jitter_m),
                z,
            ),
            quaternion=pose.quaternion,
        )
    return EpisodeSnapshot(
        seed=seed,
        robot_qpos=snapshot.robot_qpos,
        object_poses=object_poses,
    )


def execution_succeeded(
    metrics: CandidateMetrics,
    *,
    minimum_stability: float = 0.60,
) -> bool:
    """Classify an independently executed grasp from physical measurements."""

    if not 0.0 <= minimum_stability <= 1.0:
        raise ValueError("minimum_stability must be in [0, 1]")
    diagnostic = metrics.clearance_diagnostic
    clutter_overlap = diagnostic is not None and diagnostic.overlaps
    return (
        metrics.reachability >= 1.0
        and metrics.predicted_stability >= minimum_stability
        and not clutter_overlap
    )


def summarize_real_benchmark(
    episodes: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Summarize completed real-Genesis benchmark episode records."""

    summary: dict[str, object] = {"episode_count": len(episodes)}
    for strategy in ("baseline", "guardiansim"):
        records = [episode[strategy] for episode in episodes]
        successes = [bool(record["succeeded"]) for record in records]
        stabilities = [
            float(record["execution_metrics"]["predicted_stability"])
            for record in records
        ]
        clearances = [
            float(record["execution_metrics"]["collision_margin_m"])
            for record in records
        ]
        selections = Counter(
            str(record["candidate"]["candidate_id"]) for record in records
        )
        summary[strategy] = {
            "success_count": sum(successes),
            "success_rate": fmean(successes) if successes else 0.0,
            "mean_stability": fmean(stabilities) if stabilities else 0.0,
            "mean_clutter_clearance_m": fmean(clearances) if clearances else 0.0,
            "candidate_selections": dict(sorted(selections.items())),
        }
    baseline_rate = float(summary["baseline"]["success_rate"])
    guardian_rate = float(summary["guardiansim"]["success_rate"])
    summary["absolute_success_rate_lift"] = guardian_rate - baseline_rate
    return summary


def validate_resume_payload(
    payload: Mapping[str, object],
    *,
    expected_configuration: Mapping[str, object],
    requested_episode_count: int,
    seed_start: int,
) -> list[dict[str, object]]:
    """Return a valid contiguous episode prefix or reject incompatible evidence."""

    mismatches = {
        key: (payload.get(key), value)
        for key, value in expected_configuration.items()
        if payload.get(key) != value
    }
    if mismatches:
        raise ValueError(
            "existing report configuration does not match this run; "
            f"use --fresh to replace it: {mismatches}"
        )
    episodes = payload.get("episodes")
    if not isinstance(episodes, list) or not all(
        isinstance(episode, dict) for episode in episodes
    ):
        raise ValueError("existing report has no valid episodes list")
    expected_seeds = list(range(seed_start, seed_start + len(episodes)))
    actual_seeds = [episode.get("seed") for episode in episodes]
    if actual_seeds != expected_seeds:
        raise ValueError(
            "existing report episodes are not a contiguous seed prefix: "
            f"{actual_seeds}"
        )
    if len(episodes) > requested_episode_count:
        raise ValueError("existing report contains more episodes than requested")
    return episodes
