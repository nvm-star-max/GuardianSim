"""Audit the preserved GuardianSim evidence at its correct statistical grain."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class EvidenceScale:
    """Counts that separate independent scenes from nested action traces."""

    formal_scene_count: int
    breadth_scene_count: int
    counterfactual_rollout_count: int
    final_execution_count: int

    @property
    def paired_scene_count(self) -> int:
        return self.formal_scene_count + self.breadth_scene_count

    @property
    def simulated_action_trace_count(self) -> int:
        return self.counterfactual_rollout_count + self.final_execution_count

    def as_dict(self) -> dict[str, int]:
        payload = asdict(self)
        payload["paired_scene_count"] = self.paired_scene_count
        payload["simulated_action_trace_count"] = (
            self.simulated_action_trace_count
        )
        return payload


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be a mapping")
    return value


def _list(value: object, *, label: str) -> list[object]:
    if not isinstance(value, list):
        raise TypeError(f"{label} must be a list")
    return value


def _confirmation_rollouts(selection: Mapping[str, object]) -> int:
    observations = _mapping(
        selection.get("observations_by_id"),
        label="selection.observations_by_id",
    )
    total = 0
    for candidate_id, values in observations.items():
        candidate_observations = _list(
            values,
            label=f"observations for {candidate_id}",
        )
        if not candidate_observations:
            raise ValueError(f"candidate {candidate_id} has no observations")
        # The first observation is the already-counted initial rollout.
        total += len(candidate_observations) - 1
    return total


def _gate32_counts(payload: Mapping[str, object]) -> tuple[int, int, int]:
    if payload.get("schema_version") != 5:
        raise ValueError("Gate 3.2 evidence must use schema version 5")
    episodes = _list(payload.get("episodes"), label="Gate 3.2 episodes")
    initial = 0
    confirmations = 0
    executions = 0
    for episode_index, raw_episode in enumerate(episodes):
        episode = _mapping(
            raw_episode,
            label=f"Gate 3.2 episode {episode_index}",
        )
        selection = _mapping(
            episode.get("selection"),
            label=f"Gate 3.2 episode {episode_index} selection",
        )
        initial += len(
            _mapping(
                selection.get("initial_metrics_by_id"),
                label="Gate 3.2 initial metrics",
            )
        )
        confirmations += _confirmation_rollouts(selection)
        for strategy in ("baseline", "guardiansim"):
            record = _mapping(
                episode.get(strategy),
                label=f"Gate 3.2 {strategy}",
            )
            executions += len(
                _list(
                    record.get("executions"),
                    label=f"Gate 3.2 {strategy} executions",
                )
            )
    return len(episodes), initial + confirmations, executions


def _gate33_counts(payload: Mapping[str, object]) -> tuple[int, int, int]:
    if payload.get("schema_version") != 6:
        raise ValueError("Gate 3.3 evidence must use schema version 6")
    episodes = _list(payload.get("episodes"), label="Gate 3.3 episodes")
    initial = 0
    confirmations = 0
    executions = 0
    for episode_index, raw_episode in enumerate(episodes):
        episode = _mapping(
            raw_episode,
            label=f"Gate 3.3 episode {episode_index}",
        )
        selection = _mapping(
            episode.get("selection"),
            label=f"Gate 3.3 episode {episode_index} selection",
        )
        initial += len(
            _mapping(
                selection.get("initial_raw_metrics_by_id"),
                label="Gate 3.3 initial raw metrics",
            )
        )
        confirmations += _confirmation_rollouts(selection)
        for strategy in ("baseline", "guardiansim"):
            record = _mapping(
                episode.get(strategy),
                label=f"Gate 3.3 {strategy}",
            )
            if record.get("execution") is not None:
                executions += 1
    return len(episodes), initial + confirmations, executions


def summarize_preserved_evidence(
    gate32_payload: Mapping[str, object],
    gate33_payload: Mapping[str, object],
) -> EvidenceScale:
    """Return non-inflated counts from the two preserved evidence reports."""

    formal_scenes, formal_rollouts, formal_executions = _gate32_counts(
        gate32_payload
    )
    breadth_scenes, breadth_rollouts, breadth_executions = _gate33_counts(
        gate33_payload
    )
    return EvidenceScale(
        formal_scene_count=formal_scenes,
        breadth_scene_count=breadth_scenes,
        counterfactual_rollout_count=formal_rollouts + breadth_rollouts,
        final_execution_count=formal_executions + breadth_executions,
    )
