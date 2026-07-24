#!/usr/bin/env python3
"""Run five fixed-state GuardianSim grasp candidates in Genesis."""

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
from guardian_sim.reference_backend import GenesisSceneDriver, ReferenceSceneRolloutBackend
from guardian_sim.scoring import rank_candidates
from guardian_sim.serialization import json_default


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpu", action="store_true")
    parser.add_argument("--pick", default="011_banana")
    parser.add_argument("--seed", type=int, default=41)
    parser.add_argument(
        "--yaws",
        type=float,
        nargs="+",
        default=(-45.0, -22.5, 0.0, 22.5, 45.0),
    )
    parser.add_argument("--offset", type=float, default=0.0)
    parser.add_argument("--output", default="outputs/guardian_dry_run/candidates.json")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    gs.init(backend=gs.cpu if args.cpu else gs.gpu)
    bundle = build_scene(
        n_envs=1,
        add_world_cam=False,
        add_wrist_cam=False,
    )
    _settle(bundle, 60)
    target_xyz = tuple(_to_numpy(bundle.ycb[args.pick].get_pos())[:3])
    candidates = tuple(
        generate_grasp_candidates(
            target_xyz,
            yaw_degrees=args.yaws,
            lateral_offsets_m=(args.offset,),
        )
    )
    driver = GenesisSceneDriver(
        bundle,
        seed=args.seed,
        rollout=lambda scene_bundle, candidate: run_grasp_candidate(
            scene_bundle,
            candidate,
            pick_object=args.pick,
        ),
    )
    backend = ReferenceSceneRolloutBackend.from_current_state(driver)
    metrics_by_id = evaluate_candidates(GenesisCandidateEvaluator(backend), candidates)
    ranked = rank_candidates(candidates, metrics_by_id)

    payload = {
        "schema_version": 1,
        "data_source": "genesis_counterfactual_rollout",
        "seed": args.seed,
        "pick_object": args.pick,
        "snapshot_fingerprint": backend.snapshot.fingerprint(),
        "candidate_count": len(candidates),
        "measurement_notes": {
            "clearance": "minimum sampled AABB separation from distal arm links to non-target obstacles",
            "perception_uncertainty": "fixed 0.05 prior for this simulator-state dry run",
            "retained_lift": "object height retained after a requested 0.10 m gripper lift",
        },
        "ranking": [
            {
                "rank": index,
                "candidate": asdict(item.candidate),
                "metrics": asdict(item.metrics),
                "utility": item.utility,
                "risk": item.risk,
                "success_probability": item.success_probability,
            }
            for index, item in enumerate(ranked, start=1)
        ],
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, default=json_default, indent=2, sort_keys=True)
    output_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
