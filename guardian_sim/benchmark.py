"""Reproducible baseline-vs-GuardianSim benchmark and artifact export."""

from __future__ import annotations

import csv
import json
import random
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from guardian_sim.candidates import generate_grasp_candidates
from guardian_sim.failure import diagnose_outcome
from guardian_sim.models import ActionCandidate, CandidateMetrics, ExecutionOutcome
from guardian_sim.planner import execute_ranked_plan
from guardian_sim.scoring import score_candidate


@dataclass(frozen=True, slots=True)
class BenchmarkEpisode:
    episode_id: str
    candidates: tuple[ActionCandidate, ...]
    metrics_by_id: Mapping[str, CandidateMetrics]
    outcomes_by_id: Mapping[str, ExecutionOutcome]


@dataclass(frozen=True, slots=True)
class BenchmarkRow:
    episode_id: str
    strategy: str
    succeeded: bool
    collision: bool
    attempts: int
    final_failure_type: str
    selected_candidates: str


def run_benchmark(
    episodes: Iterable[BenchmarkEpisode],
    *,
    max_attempts: int = 3,
) -> list[BenchmarkRow]:
    """Compare first-proposal execution with risk-ranked bounded recovery."""

    rows: list[BenchmarkRow] = []
    for episode in episodes:
        if not episode.candidates:
            raise ValueError(f"episode {episode.episode_id} has no candidates")

        baseline_candidate = episode.candidates[0]
        baseline_outcome = episode.outcomes_by_id[baseline_candidate.candidate_id]
        baseline_diagnosis = diagnose_outcome(baseline_outcome)
        rows.append(
            BenchmarkRow(
                episode_id=episode.episode_id,
                strategy="baseline_first_candidate",
                succeeded=baseline_diagnosis.succeeded,
                collision=baseline_outcome.collision,
                attempts=1,
                final_failure_type=baseline_diagnosis.failure_type.value,
                selected_candidates=baseline_candidate.candidate_id,
            )
        )

        result = execute_ranked_plan(
            episode.candidates,
            episode.metrics_by_id,
            lambda candidate: episode.outcomes_by_id[candidate.candidate_id],
            max_attempts=max_attempts,
        )
        final_trace = result.attempts[-1]
        rows.append(
            BenchmarkRow(
                episode_id=episode.episode_id,
                strategy="guardiansim",
                succeeded=result.succeeded,
                collision=any(trace.outcome.collision for trace in result.attempts),
                attempts=len(result.attempts),
                final_failure_type=final_trace.diagnosis.failure_type.value,
                selected_candidates="|".join(trace.score.candidate.candidate_id for trace in result.attempts),
            )
        )
    return rows


def summarize(rows: Sequence[BenchmarkRow]) -> dict[str, dict[str, float | int]]:
    """Aggregate decision metrics separately for each strategy."""

    by_strategy: dict[str, list[BenchmarkRow]] = {}
    for row in rows:
        by_strategy.setdefault(row.strategy, []).append(row)

    summary: dict[str, dict[str, float | int]] = {}
    for strategy, strategy_rows in sorted(by_strategy.items()):
        count = len(strategy_rows)
        summary[strategy] = {
            "episodes": count,
            "success_rate": sum(row.succeeded for row in strategy_rows) / count,
            "collision_rate": sum(row.collision for row in strategy_rows) / count,
            "mean_attempts": sum(row.attempts for row in strategy_rows) / count,
        }
    return summary


def write_report(
    rows: Sequence[BenchmarkRow],
    output_dir: str | Path,
    *,
    metadata: Mapping[str, object] | None = None,
) -> tuple[Path, Path]:
    """Write judge-friendly episode CSV and aggregate JSON files."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    csv_path = output_path / "episodes.csv"
    json_path = output_path / "summary.json"

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(rows[0]).keys()) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(asdict(row) for row in rows)

    payload = {
        "metadata": dict(metadata or {}),
        "summary": summarize(rows),
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return csv_path, json_path


def generate_synthetic_episodes(count: int, *, seed: int = 7) -> list[BenchmarkEpisode]:
    """Create smoke-test episodes; these are not competition evaluation results."""

    if count < 1:
        raise ValueError("count must be positive")
    rng = random.Random(seed)
    episodes: list[BenchmarkEpisode] = []
    for episode_index in range(count):
        target = (rng.uniform(0.43, 0.53), rng.uniform(-0.06, 0.06), 0.04)
        candidates = tuple(generate_grasp_candidates(target))
        metrics_by_id: dict[str, CandidateMetrics] = {}
        outcomes_by_id: dict[str, ExecutionOutcome] = {}
        for candidate in candidates:
            alignment = max(0.0, 1.0 - abs(candidate.yaw_degrees) / 70.0)
            clearance = rng.uniform(0.005, 0.10)
            metrics = CandidateMetrics(
                collision_margin_m=clearance,
                reachability=rng.uniform(0.72, 1.0),
                grasp_alignment=alignment,
                predicted_stability=_bounded(rng.uniform(0.55, 0.98) * (0.65 + 0.35 * alignment)),
                path_length_m=rng.uniform(0.32, 0.78),
                perception_uncertainty=rng.uniform(0.02, 0.24),
            )
            metrics_by_id[candidate.candidate_id] = metrics
            score = score_candidate(candidate, metrics)
            collision = clearance < 0.018 and rng.random() < 0.75
            succeeded = not collision and rng.random() < score.success_probability
            outcomes_by_id[candidate.candidate_id] = (
                ExecutionOutcome(True, 0.08, 0.025, 4.0, 0.006)
                if succeeded
                else ExecutionOutcome(False, 0.0, 0.30, 3.0, 0.0, collision=collision)
            )
        episodes.append(
            BenchmarkEpisode(
                episode_id=f"synthetic-{episode_index:04d}",
                candidates=candidates,
                metrics_by_id=metrics_by_id,
                outcomes_by_id=outcomes_by_id,
            )
        )
    return episodes


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))
