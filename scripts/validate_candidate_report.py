#!/usr/bin/env python3
"""Validate a representative Genesis counterfactual-candidate smoke report."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def validate_candidate_report(payload: dict[str, object]) -> dict[str, object]:
    if payload.get("schema_version") != 3:
        raise ValueError("candidate report must use schema version 3")
    if payload.get("data_source") != "genesis_counterfactual_rollout":
        raise ValueError("candidate report must come from Genesis counterfactual rollouts")
    snapshot = payload.get("snapshot_fingerprint")
    if not isinstance(snapshot, str) or not snapshot:
        raise ValueError("candidate report is missing its snapshot fingerprint")

    ranking = payload.get("ranking")
    if not isinstance(ranking, list) or len(ranking) < 2:
        raise ValueError("candidate report must contain at least two alternatives")
    if payload.get("candidate_count") != len(ranking):
        raise ValueError("candidate_count does not match ranking length")

    expected_ranks = list(range(1, len(ranking) + 1))
    actual_ranks = [item.get("rank") for item in ranking if isinstance(item, dict)]
    if actual_ranks != expected_ranks:
        raise ValueError("candidate ranks must be a contiguous ordered sequence")

    candidate_ids: list[str] = []
    for item in ranking:
        if not isinstance(item, dict):
            raise ValueError("each ranking item must be an object")
        candidate = item.get("candidate")
        metrics = item.get("metrics")
        if not isinstance(candidate, dict) or not isinstance(metrics, dict):
            raise ValueError("each ranking item needs candidate and metrics objects")
        candidate_id = candidate.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id:
            raise ValueError("each candidate needs a non-empty candidate_id")
        candidate_ids.append(candidate_id)
        for field in (
            "collision_margin_m",
            "reachability",
            "grasp_alignment",
            "predicted_stability",
            "path_length_m",
            "perception_uncertainty",
        ):
            value = metrics.get(field)
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{candidate_id} has invalid metric {field}")
        for field in ("utility", "risk", "success_probability"):
            value = item.get(field)
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{candidate_id} has invalid score {field}")

    if len(set(candidate_ids)) != len(candidate_ids):
        raise ValueError("candidate IDs must be unique")
    return {
        "validated": True,
        "candidate_count": len(ranking),
        "snapshot_fingerprint": snapshot,
        "top_candidate_id": candidate_ids[0],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.report.read_text(encoding="utf-8"))
    print(json.dumps(validate_candidate_report(payload), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
