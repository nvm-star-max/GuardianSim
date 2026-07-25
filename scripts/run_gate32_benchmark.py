#!/usr/bin/env python3
"""Run the frozen Gate 3.2 obstacle-aware repeatable-safety benchmark."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path

import genesis as gs
from run_gate31_adversarial_benchmark import RuntimeDynamicsController

from franka_fruit_pick.build_scene import build_scene
from franka_fruit_pick.grasp_demo import _settle, _to_numpy
from franka_fruit_pick.guardian_rollout import run_grasp_candidate
from franka_fruit_pick.scene_config import get_ycb_assets
from guardian_sim.adversarial_benchmark import (
    PRIMARY_OBSTACLE_BY_PICK,
    apply_gate31_scenario,
    classify_gate31_execution,
    scenario_asdict,
)
from guardian_sim.candidates import generate_obstacle_aware_candidates
from guardian_sim.evaluator import evaluate_candidates
from guardian_sim.gate32_benchmark import (
    GATE32_CONFIRMATION_ROLLOUTS,
    GATE32_EXECUTION_REPEATS,
    GATE32_MINIMUM_SAFE_CLEARANCE_M,
    GATE32_MINIMUM_STABILITY,
    GATE32_MINIMUM_SUCCESS_MARGIN,
    GATE32_SHORTLIST_SIZE,
    aggregate_repeatable_executions,
    gate32_protocol_payload,
    generate_gate32_scenarios,
    safe_stop_aggregate,
    summarize_gate32,
    validate_gate32_payload,
)
from guardian_sim.genesis_adapter import GenesisCandidateEvaluator
from guardian_sim.real_benchmark import validate_resume_payload
from guardian_sim.reference_backend import (
    EpisodeSnapshot,
    GenesisSceneDriver,
    ReferenceSceneRolloutBackend,
)
from guardian_sim.robust_selection import select_safety_first_candidate
from guardian_sim.serialization import json_default

NOMINAL_CANDIDATE_ID = "yaw_+00.0_offset_+0.000"
SETTLE_STEPS = 40


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpu", action="store_true")
    parser.add_argument(
        "--output",
        default="outputs/gate-3-2/report.json",
    )
    parser.add_argument(
        "--max-new-scenarios",
        type=int,
        default=None,
        help=(
            "run at most this many new scenarios while preserving the frozen "
            "30-scenario protocol"
        ),
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="discard an existing report instead of resuming its completed prefix",
    )
    return parser


def _report_configuration(
    *,
    base_snapshot_fingerprint: str,
) -> dict[str, object]:
    scenarios = generate_gate32_scenarios()
    return {
        "schema_version": 5,
        "data_source": "independent_genesis_execution",
        "protocol": gate32_protocol_payload(),
        "requested_episode_count": len(scenarios),
        "seed_start": scenarios[0].seed,
        "base_snapshot_fingerprint": base_snapshot_fingerprint,
    }


def _load_completed_episodes(
    output_path: Path,
    *,
    fresh: bool,
    base_snapshot_fingerprint: str,
) -> list[dict[str, object]]:
    if fresh or not output_path.exists():
        return []
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    scenarios = generate_gate32_scenarios()
    episodes = validate_resume_payload(
        payload,
        expected_configuration=_report_configuration(
            base_snapshot_fingerprint=base_snapshot_fingerprint,
        ),
        requested_episode_count=len(scenarios),
        seed_start=scenarios[0].seed,
    )
    validate_gate32_payload(payload, require_complete=False)
    return episodes


def _write_report(
    output_path: Path,
    *,
    base_snapshot_fingerprint: str,
    episodes: list[dict[str, object]],
) -> None:
    payload = {
        **_report_configuration(
            base_snapshot_fingerprint=base_snapshot_fingerprint,
        ),
        "completed_episode_count": len(episodes),
        "summary": summarize_gate32(episodes),
        "episodes": episodes,
    }
    validate_gate32_payload(payload, require_complete=False)
    rendered = json.dumps(payload, default=json_default, indent=2, sort_keys=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered + "\n", encoding="utf-8")


def _execute_repeats(evaluator, candidate):
    records = []
    classifications = []
    timings = []
    for repeat_index in range(GATE32_EXECUTION_REPEATS):
        started = time.perf_counter()
        metrics = evaluator.evaluate(candidate)
        timings.append(time.perf_counter() - started)
        classification = classify_gate31_execution(
            metrics,
            minimum_stability=GATE32_MINIMUM_STABILITY,
            minimum_safe_clearance_m=GATE32_MINIMUM_SAFE_CLEARANCE_M,
        )
        classifications.append(classification)
        records.append(
            {
                "repeat_index": repeat_index,
                "execution_metrics": asdict(metrics),
                "classification": asdict(classification),
            }
        )
    return (
        records,
        asdict(aggregate_repeatable_executions(classifications)),
        timings,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.max_new_scenarios is not None and args.max_new_scenarios < 1:
        raise ValueError("--max-new-scenarios must be positive")

    scenarios = generate_gate32_scenarios()
    protocol = gate32_protocol_payload()
    print(
        f"Gate 3.2 protocol={protocol['protocol_sha256']} "
        f"scenarios={len(scenarios)}",
        flush=True,
    )

    gs.init(backend=gs.cpu if args.cpu else gs.gpu)
    bundle = build_scene(
        n_envs=1,
        add_world_cam=False,
        add_wrist_cam=False,
    )
    _settle(bundle, 60)

    active_pick = {"name": scenarios[0].pick_object}
    driver = GenesisSceneDriver(
        bundle,
        seed=scenarios[0].seed,
        rollout=lambda scene_bundle, candidate: run_grasp_candidate(
            scene_bundle,
            candidate,
            pick_object=active_pick["name"],
        ),
    )
    base_snapshot = driver.capture_snapshot()
    base_snapshot_fingerprint = base_snapshot.fingerprint()
    dynamics = RuntimeDynamicsController(bundle)
    footprint_radii = {
        name: asset.radius_xy for name, asset in get_ycb_assets().items()
    }

    output_path = Path(args.output)
    episodes = _load_completed_episodes(
        output_path,
        fresh=args.fresh,
        base_snapshot_fingerprint=base_snapshot_fingerprint,
    )
    if episodes:
        print(
            f"resuming {len(episodes)}/{len(scenarios)} completed scenarios",
            flush=True,
        )

    stop_index = len(scenarios)
    if args.max_new_scenarios is not None:
        stop_index = min(
            stop_index,
            len(episodes) + args.max_new_scenarios,
        )

    for episode_index in range(len(episodes), stop_index):
        scenario = scenarios[episode_index]
        active_pick["name"] = scenario.pick_object
        challenge_snapshot = apply_gate31_scenario(
            base_snapshot,
            scenario,
            footprint_radii_m=footprint_radii,
        )
        driver.restore_snapshot(challenge_snapshot)
        dynamics.apply(
            pick_object=scenario.pick_object,
            friction_ratio=scenario.friction_ratio,
            target_mass_ratio=scenario.target_mass_ratio,
        )
        _settle(bundle, SETTLE_STEPS)
        settled_snapshot = driver.capture_snapshot()
        episode_snapshot = EpisodeSnapshot(
            seed=scenario.seed,
            robot_qpos=settled_snapshot.robot_qpos,
            object_poses=settled_snapshot.object_poses,
        )

        obstacle_name = PRIMARY_OBSTACLE_BY_PICK[scenario.pick_object]
        target_xyz = tuple(
            _to_numpy(bundle.ycb[scenario.pick_object].get_pos())[:3]
        )
        obstacle_xyz = tuple(_to_numpy(bundle.ycb[obstacle_name].get_pos())[:3])
        candidates = tuple(
            generate_obstacle_aware_candidates(target_xyz, obstacle_xyz)
        )
        nominal = next(
            candidate
            for candidate in candidates
            if candidate.candidate_id == NOMINAL_CANDIDATE_ID
        )
        backend = ReferenceSceneRolloutBackend(driver, episode_snapshot)
        evaluator = GenesisCandidateEvaluator(backend)

        planning_started = time.perf_counter()
        initial_metrics_by_id = evaluate_candidates(evaluator, candidates)
        selection = select_safety_first_candidate(
            candidates,
            initial_metrics_by_id,
            evaluator,
            nominal_candidate_id=nominal.candidate_id,
            shortlist_size=GATE32_SHORTLIST_SIZE,
            confirmation_rollouts=GATE32_CONFIRMATION_ROLLOUTS,
            minimum_stability=GATE32_MINIMUM_STABILITY,
            minimum_clearance_m=GATE32_MINIMUM_SAFE_CLEARANCE_M,
            minimum_success_margin=GATE32_MINIMUM_SUCCESS_MARGIN,
        )
        planning_wall_seconds = time.perf_counter() - planning_started

        (
            baseline_executions,
            baseline_aggregate,
            baseline_timings,
        ) = _execute_repeats(evaluator, nominal)
        if selection.selected is None:
            guardian_executions = []
            guardian_aggregate = asdict(safe_stop_aggregate())
            guardian_timings = []
            guardian_candidate = None
        else:
            guardian_candidate = selection.selected.candidate
            (
                guardian_executions,
                guardian_aggregate,
                guardian_timings,
            ) = _execute_repeats(evaluator, guardian_candidate)

        episode = {
            "episode_index": episode_index,
            "seed": scenario.seed,
            "scenario_id": scenario.scenario_id,
            "pick_object": scenario.pick_object,
            "layout": scenario.layout,
            "primary_obstacle": obstacle_name,
            "scenario": scenario_asdict(scenario),
            "snapshot_fingerprint": episode_snapshot.fingerprint(),
            "target_xyz": target_xyz,
            "obstacle_xyz": obstacle_xyz,
            "timing": {
                "planning_wall_seconds": planning_wall_seconds,
                "baseline_execution_wall_seconds": baseline_timings,
                "guardiansim_execution_wall_seconds": guardian_timings,
            },
            "selection": {
                "decision": selection.decision,
                "selected_candidate_id": (
                    guardian_candidate.candidate_id
                    if guardian_candidate is not None
                    else None
                ),
                "initial_metrics_by_id": {
                    candidate_id: asdict(metrics)
                    for candidate_id, metrics in sorted(
                        initial_metrics_by_id.items()
                    )
                },
                "confirmed_candidate_ids": sorted(
                    selection.observations_by_id
                ),
                "observations_by_id": {
                    candidate_id: [
                        asdict(metrics) for metrics in observations
                    ]
                    for candidate_id, observations in sorted(
                        selection.observations_by_id.items()
                    )
                },
            },
            "baseline": {
                "candidate": asdict(nominal),
                "safe_stopped": False,
                "executions": baseline_executions,
                "aggregate": baseline_aggregate,
            },
            "guardiansim": {
                "candidate": (
                    asdict(guardian_candidate)
                    if guardian_candidate is not None
                    else None
                ),
                "safe_stopped": guardian_candidate is None,
                "executions": guardian_executions,
                "aggregate": guardian_aggregate,
            },
        }
        episodes.append(episode)
        _write_report(
            output_path,
            base_snapshot_fingerprint=base_snapshot_fingerprint,
            episodes=episodes,
        )
        print(
            f"scenario={episode_index + 1}/{len(scenarios)} "
            f"id={scenario.scenario_id} "
            f"decision={selection.decision} "
            f"baseline_repeatable_safe="
            f"{baseline_aggregate['repeatable_safe_completion']} "
            f"guardian_repeatable_safe="
            f"{guardian_aggregate['repeatable_safe_completion']} "
            f"planning_s={planning_wall_seconds:.2f}",
            flush=True,
        )

    print(json.dumps(summarize_gate32(episodes), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
