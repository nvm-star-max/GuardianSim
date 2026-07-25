#!/usr/bin/env python3
"""Run the frozen Gate 3.1 multi-object adversarial Genesis benchmark."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path

import genesis as gs
import numpy as np

from franka_fruit_pick.build_scene import build_scene
from franka_fruit_pick.grasp_demo import _settle, _to_numpy
from franka_fruit_pick.guardian_rollout import run_grasp_candidate
from franka_fruit_pick.scene_config import get_ycb_assets
from guardian_sim.adversarial_benchmark import (
    GATE31_MINIMUM_STABILITY,
    PRIMARY_OBSTACLE_BY_PICK,
    apply_gate31_scenario,
    classify_gate31_execution,
    gate31_protocol_payload,
    generate_gate31_scenarios,
    scenario_asdict,
    summarize_gate31,
)
from guardian_sim.candidates import generate_grasp_candidates
from guardian_sim.evaluator import evaluate_candidates
from guardian_sim.genesis_adapter import GenesisCandidateEvaluator
from guardian_sim.real_benchmark import validate_resume_payload
from guardian_sim.reference_backend import (
    EpisodeSnapshot,
    GenesisSceneDriver,
    ReferenceSceneRolloutBackend,
)
from guardian_sim.robust_selection import select_robust_candidate
from guardian_sim.serialization import json_default

NOMINAL_CANDIDATE_ID = "yaw_+00.0_offset_+0.000"
SHORTLIST_SIZE = 3
CONFIRMATION_ROLLOUTS = 2
MINIMUM_SUCCESS_MARGIN = 0.02
SETTLE_STEPS = 40


class RuntimeDynamicsController:
    """Apply deterministic per-scenario dynamics without rebuilding Genesis."""

    def __init__(self, bundle) -> None:
        self.bundle = bundle
        self.base_mass_by_object = {
            name: self._base_mass(entity) for name, entity in bundle.ycb.items()
        }

    def apply(
        self,
        *,
        pick_object: str,
        friction_ratio: float,
        target_mass_ratio: float,
    ) -> None:
        self._set_friction_ratio(self.bundle.franka, friction_ratio)
        for entity in self.bundle.ycb.values():
            self._set_friction_ratio(entity, friction_ratio)
        for entity in self.bundle.table:
            self._set_friction_ratio(entity, friction_ratio)

        for name, entity in self.bundle.ycb.items():
            base_mass = self.base_mass_by_object[name]
            ratio = target_mass_ratio if name == pick_object else 1.0
            self._set_mass_shift(entity, base_mass * (ratio - 1.0))

    def _batch_shape(self, n_links: int) -> tuple[int, ...]:
        n_envs = self.bundle.scene.n_envs
        return (n_links,) if n_envs == 0 else (n_envs, n_links)

    @staticmethod
    def _base_mass(entity) -> np.ndarray:
        mass = np.asarray(
            entity.get_links_inertial_mass().cpu().numpy(),
            dtype=np.float64,
        )
        if mass.ndim > 1:
            mass = mass.reshape(-1, entity.n_links)[0]
        return mass.reshape(-1)[: entity.n_links]

    def _set_friction_ratio(self, entity, ratio: float) -> None:
        entity.set_friction_ratio(
            np.full(self._batch_shape(entity.n_links), ratio, dtype=np.float32),
            links_idx_local=np.arange(entity.n_links),
        )

    def _set_mass_shift(self, entity, shift_per_link: np.ndarray) -> None:
        shift = np.broadcast_to(
            np.asarray(shift_per_link, dtype=np.float32),
            (entity.n_links,),
        )
        if self.bundle.scene.n_envs == 0:
            payload = shift
        else:
            payload = np.tile(shift, (self.bundle.scene.n_envs, 1))
        entity.set_mass_shift(
            payload,
            links_idx_local=np.arange(entity.n_links),
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpu", action="store_true")
    parser.add_argument(
        "--output",
        default="outputs/gate-3-1/report.json",
    )
    parser.add_argument(
        "--max-new-scenarios",
        type=int,
        default=None,
        help=(
            "run at most this many new scenarios, preserving the same frozen "
            "30-scenario protocol for resumable cloud smoke checks"
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
    scenarios = generate_gate31_scenarios()
    return {
        "schema_version": 4,
        "data_source": "independent_genesis_execution",
        "protocol": gate31_protocol_payload(),
        "requested_episode_count": len(scenarios),
        "seed_start": scenarios[0].seed,
        "shortlist_size": SHORTLIST_SIZE,
        "confirmation_rollouts": CONFIRMATION_ROLLOUTS,
        "minimum_success_margin": MINIMUM_SUCCESS_MARGIN,
        "settle_steps": SETTLE_STEPS,
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
    scenarios = generate_gate31_scenarios()
    return validate_resume_payload(
        payload,
        expected_configuration=_report_configuration(
            base_snapshot_fingerprint=base_snapshot_fingerprint,
        ),
        requested_episode_count=len(scenarios),
        seed_start=scenarios[0].seed,
    )


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
        "summary": summarize_gate31(episodes),
        "episodes": episodes,
    }
    rendered = json.dumps(payload, default=json_default, indent=2, sort_keys=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered + "\n", encoding="utf-8")


def _timed_evaluate(evaluator, candidate):
    started = time.perf_counter()
    metrics = evaluator.evaluate(candidate)
    return metrics, time.perf_counter() - started


def main() -> None:
    args = build_parser().parse_args()
    if args.max_new_scenarios is not None and args.max_new_scenarios < 1:
        raise ValueError("--max-new-scenarios must be positive")

    scenarios = generate_gate31_scenarios()
    protocol = gate31_protocol_payload()
    print(
        f"Gate 3.1 protocol={protocol['protocol_sha256']} "
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

        target_xyz = tuple(
            _to_numpy(bundle.ycb[scenario.pick_object].get_pos())[:3]
        )
        candidates = tuple(generate_grasp_candidates(target_xyz))
        backend = ReferenceSceneRolloutBackend(driver, episode_snapshot)
        evaluator = GenesisCandidateEvaluator(backend)

        planning_started = time.perf_counter()
        metrics_by_id = evaluate_candidates(evaluator, candidates)
        nominal = next(
            candidate
            for candidate in candidates
            if candidate.candidate_id == NOMINAL_CANDIDATE_ID
        )
        selection = select_robust_candidate(
            candidates,
            metrics_by_id,
            evaluator,
            nominal_candidate_id=nominal.candidate_id,
            shortlist_size=SHORTLIST_SIZE,
            confirmation_rollouts=CONFIRMATION_ROLLOUTS,
            minimum_stability=GATE31_MINIMUM_STABILITY,
            minimum_success_margin=MINIMUM_SUCCESS_MARGIN,
        )
        planning_wall_seconds = time.perf_counter() - planning_started
        guardian = selection.selected.candidate

        baseline_execution, baseline_wall_seconds = _timed_evaluate(
            evaluator,
            nominal,
        )
        guardian_execution, guardian_wall_seconds = _timed_evaluate(
            evaluator,
            guardian,
        )
        baseline_classification = classify_gate31_execution(baseline_execution)
        guardian_classification = classify_gate31_execution(guardian_execution)

        episode = {
            "episode_index": episode_index,
            "seed": scenario.seed,
            "scenario_id": scenario.scenario_id,
            "pick_object": scenario.pick_object,
            "layout": scenario.layout,
            "primary_obstacle": PRIMARY_OBSTACLE_BY_PICK[scenario.pick_object],
            "scenario": scenario_asdict(scenario),
            "snapshot_fingerprint": episode_snapshot.fingerprint(),
            "target_xyz": target_xyz,
            "timing": {
                "planning_wall_seconds": planning_wall_seconds,
                "baseline_execution_wall_seconds": baseline_wall_seconds,
                "guardiansim_execution_wall_seconds": guardian_wall_seconds,
            },
            "selection": {
                "fallback_used": selection.fallback_used,
                "confirmed_candidate_ids": sorted(selection.observations_by_id),
                "observations_by_id": {
                    candidate_id: [asdict(metrics) for metrics in observations]
                    for candidate_id, observations in sorted(
                        selection.observations_by_id.items()
                    )
                },
            },
            "baseline": {
                "candidate": asdict(nominal),
                "counterfactual_score": {
                    "utility": selection.nominal.utility,
                    "risk": selection.nominal.risk,
                    "success_probability": selection.nominal.success_probability,
                },
                "execution_metrics": asdict(baseline_execution),
                "classification": asdict(baseline_classification),
            },
            "guardiansim": {
                "candidate": asdict(guardian),
                "counterfactual_score": {
                    "utility": selection.selected.utility,
                    "risk": selection.selected.risk,
                    "success_probability": selection.selected.success_probability,
                },
                "execution_metrics": asdict(guardian_execution),
                "classification": asdict(guardian_classification),
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
            f"baseline_safe={baseline_classification.safe_completion} "
            f"guardian_safe={guardian_classification.safe_completion} "
            f"selected={guardian.candidate_id} "
            f"planning_s={planning_wall_seconds:.2f}",
            flush=True,
        )

    print(json.dumps(summarize_gate31(episodes), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
