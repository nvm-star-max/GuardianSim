#!/usr/bin/env python3
"""Run independently executed baseline-vs-GuardianSim Genesis episodes."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import genesis as gs

from franka_fruit_pick.build_scene import build_scene
from franka_fruit_pick.grasp_demo import _settle, _to_numpy
from franka_fruit_pick.guardian_rollout import run_grasp_candidate
from guardian_sim.candidates import generate_grasp_candidates
from guardian_sim.evaluator import evaluate_candidates
from guardian_sim.genesis_adapter import GenesisCandidateEvaluator
from guardian_sim.real_benchmark import (
    execution_succeeded,
    perturb_snapshot,
    summarize_real_benchmark,
)
from guardian_sim.reference_backend import (
    EpisodeSnapshot,
    GenesisSceneDriver,
    ReferenceSceneRolloutBackend,
)
from guardian_sim.scoring import rank_candidates, score_candidate
from guardian_sim.serialization import json_default

NOMINAL_CANDIDATE_ID = "yaw_+00.0_offset_+0.000"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpu", action="store_true")
    parser.add_argument("--pick", default="011_banana")
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--seed-start", type=int, default=101)
    parser.add_argument("--xy-jitter-m", type=float, default=0.015)
    parser.add_argument("--settle-steps", type=int, default=30)
    parser.add_argument("--minimum-stability", type=float, default=0.60)
    parser.add_argument("--output", default="outputs/fixed_seed_benchmark/report.json")
    return parser


def _write_report(
    output_path: Path,
    *,
    args: argparse.Namespace,
    episodes: list[dict[str, object]],
) -> None:
    payload = {
        "schema_version": 1,
        "data_source": "independent_genesis_execution",
        "pick_object": args.pick,
        "requested_episode_count": args.episodes,
        "completed_episode_count": len(episodes),
        "seed_start": args.seed_start,
        "xy_jitter_m": args.xy_jitter_m,
        "minimum_stability": args.minimum_stability,
        "summary": summarize_real_benchmark(episodes),
        "episodes": episodes,
    }
    rendered = json.dumps(payload, default=json_default, indent=2, sort_keys=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    if args.episodes < 1:
        raise ValueError("episodes must be positive")
    if args.settle_steps < 0:
        raise ValueError("settle_steps cannot be negative")

    gs.init(backend=gs.cpu if args.cpu else gs.gpu)
    bundle = build_scene(
        n_envs=1,
        add_world_cam=False,
        add_wrist_cam=False,
    )
    _settle(bundle, 60)
    driver = GenesisSceneDriver(
        bundle,
        seed=args.seed_start,
        rollout=lambda scene_bundle, candidate: run_grasp_candidate(
            scene_bundle,
            candidate,
            pick_object=args.pick,
        ),
    )
    base_snapshot = driver.capture_snapshot()
    output_path = Path(args.output)
    episodes: list[dict[str, object]] = []

    for episode_index in range(args.episodes):
        seed = args.seed_start + episode_index
        driver.restore_snapshot(
            perturb_snapshot(
                base_snapshot,
                seed=seed,
                xy_jitter_m=args.xy_jitter_m,
            )
        )
        _settle(bundle, args.settle_steps)
        settled_snapshot = driver.capture_snapshot()
        episode_snapshot = EpisodeSnapshot(
            seed=seed,
            robot_qpos=settled_snapshot.robot_qpos,
            object_poses=settled_snapshot.object_poses,
        )
        target_xyz = tuple(_to_numpy(bundle.ycb[args.pick].get_pos())[:3])
        candidates = tuple(generate_grasp_candidates(target_xyz))
        backend = ReferenceSceneRolloutBackend(driver, episode_snapshot)
        evaluator = GenesisCandidateEvaluator(backend)
        metrics_by_id = evaluate_candidates(evaluator, candidates)
        ranked = rank_candidates(candidates, metrics_by_id)
        nominal = next(
            candidate
            for candidate in candidates
            if candidate.candidate_id == NOMINAL_CANDIDATE_ID
        )
        guardian = ranked[0].candidate

        baseline_execution = evaluator.evaluate(nominal)
        guardian_execution = evaluator.evaluate(guardian)
        baseline_score = score_candidate(nominal, metrics_by_id[nominal.candidate_id])
        guardian_score = ranked[0]

        episode = {
            "episode_index": episode_index,
            "seed": seed,
            "snapshot_fingerprint": episode_snapshot.fingerprint(),
            "target_xyz": target_xyz,
            "baseline": {
                "candidate": asdict(nominal),
                "counterfactual_score": {
                    "utility": baseline_score.utility,
                    "risk": baseline_score.risk,
                    "success_probability": baseline_score.success_probability,
                },
                "execution_metrics": asdict(baseline_execution),
                "succeeded": execution_succeeded(
                    baseline_execution,
                    minimum_stability=args.minimum_stability,
                ),
            },
            "guardiansim": {
                "candidate": asdict(guardian),
                "counterfactual_score": {
                    "utility": guardian_score.utility,
                    "risk": guardian_score.risk,
                    "success_probability": guardian_score.success_probability,
                },
                "execution_metrics": asdict(guardian_execution),
                "succeeded": execution_succeeded(
                    guardian_execution,
                    minimum_stability=args.minimum_stability,
                ),
            },
        }
        episodes.append(episode)
        _write_report(output_path, args=args, episodes=episodes)
        print(
            f"episode={episode_index + 1}/{args.episodes} seed={seed} "
            f"baseline={episode['baseline']['succeeded']} "
            f"guardian={episode['guardiansim']['succeeded']} "
            f"selected={guardian.candidate_id}",
            flush=True,
        )

    print(json.dumps(summarize_real_benchmark(episodes), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
