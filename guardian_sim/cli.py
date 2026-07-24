"""A local synthetic demo that exercises the complete GuardianSim decision loop."""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict

from guardian_sim.candidates import generate_grasp_candidates
from guardian_sim.models import CandidateMetrics, ExecutionOutcome
from guardian_sim.planner import execute_ranked_plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the GuardianSim synthetic counterfactual planner demo.")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--max-attempts", type=int, default=3)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    rng = random.Random(args.seed)
    candidates = generate_grasp_candidates((0.48, 0.02, 0.04))
    metrics = {
        candidate.candidate_id: CandidateMetrics(
            collision_margin_m=rng.uniform(0.015, 0.10),
            reachability=rng.uniform(0.70, 1.0),
            grasp_alignment=max(0.0, 1.0 - abs(candidate.yaw_degrees) / 75.0),
            predicted_stability=rng.uniform(0.55, 0.98),
            path_length_m=rng.uniform(0.35, 0.75),
            perception_uncertainty=rng.uniform(0.02, 0.25),
        )
        for candidate in candidates
    }

    execution_count = 0

    def synthetic_executor(candidate):
        nonlocal execution_count
        execution_count += 1
        # The first attempt intentionally misses, making recovery visible.
        if execution_count == 1:
            return ExecutionOutcome(False, 0.0, 0.30, 2.0, 0.0)
        return ExecutionOutcome(True, 0.09, 0.025, 4.0, 0.008)

    result = execute_ranked_plan(candidates, metrics, synthetic_executor, max_attempts=args.max_attempts)
    payload = {
        "project": "GuardianSim",
        "seed": args.seed,
        "succeeded": result.succeeded,
        "attempts": [
            {
                "attempt": trace.attempt_number,
                "candidate": trace.score.candidate.candidate_id,
                "success_probability": round(trace.score.success_probability, 4),
                "risk": round(trace.score.risk, 4),
                "diagnosis": trace.diagnosis.failure_type,
                "recovery": trace.recovery,
                "outcome": asdict(trace.outcome),
            }
            for trace in result.attempts
        ],
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
