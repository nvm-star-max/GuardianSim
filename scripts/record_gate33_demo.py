#!/usr/bin/env python3
"""Record an explained visual replay of one verified Gate 3.3 scenario.

The generated video re-executes Genesis from the frozen scenario declaration
and uses the GuardianSim action stored in the engineering report. It is a
presentation replay, is not appended to the report, and is not an additional
statistical trial.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import genesis as gs

from record_gate32_demo import CameraFrameRecorder, _compose_video
from run_gate31_adversarial_benchmark import RuntimeDynamicsController

from franka_fruit_pick.build_scene import build_scene
from franka_fruit_pick.grasp_demo import _settle
from franka_fruit_pick.guardian_rollout import run_grasp_candidate
from franka_fruit_pick.scene_config import get_ycb_assets
from guardian_sim.adversarial_benchmark import (
    PRIMARY_OBSTACLE_BY_PICK,
    classify_gate31_execution,
)
from guardian_sim.demo_validation import replay_retains_contact_to_safe_contrast
from guardian_sim.gate32_benchmark import (
    GATE32_MINIMUM_SAFE_CLEARANCE_M,
    GATE32_MINIMUM_STABILITY,
)
from guardian_sim.gate33_benchmark import (
    apply_gate33_scenario,
    generate_gate33_scenarios,
    validate_gate33_payload,
)
from guardian_sim.genesis_adapter import candidate_metrics_from_measurement
from guardian_sim.models import ActionCandidate
from guardian_sim.reference_backend import (
    EntityPose,
    EpisodeSnapshot,
    GenesisSceneDriver,
)
from guardian_sim.serialization import json_default

NOMINAL_CANDIDATE_ID = "yaw_+00.0_offset_+0.000"
SETTLE_STEPS = 40


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpu", action="store_true")
    parser.add_argument("--seed", type=int, default=503)
    parser.add_argument(
        "--report",
        default=(
            "docs/evidence/gate-3-3-pose-shift-stratum/raw/"
            "pose-shift-report.json"
        ),
    )
    parser.add_argument(
        "--output",
        default="outputs/demo/gate-3-3-seed-503.mp4",
    )
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument(
        "--capture-every",
        type=int,
        default=4,
        help="capture one rendered frame every N simulator control steps",
    )
    return parser


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    args = build_parser().parse_args()
    if args.capture_every < 1 or args.fps < 1:
        raise ValueError("--capture-every and --fps must be positive")

    report_path = Path(args.report)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    validate_gate33_payload(report, require_complete=False)
    formal_episode = next(
        (episode for episode in report["episodes"] if episode["seed"] == args.seed),
        None,
    )
    if formal_episode is None:
        raise ValueError(f"seed {args.seed} is not present in the Gate 3.3 report")
    if formal_episode["guardiansim"]["candidate"] is None:
        raise ValueError(f"seed {args.seed} used a safe stop and has no action replay")

    scenario = next(
        item for item in generate_gate33_scenarios() if item.seed == args.seed
    )
    if scenario.scenario_id != formal_episode["scenario_id"]:
        raise ValueError("frozen scenario identity does not match the report")

    gs.init(backend=gs.cpu if args.cpu else gs.gpu)
    bundle = build_scene(
        n_envs=1,
        add_world_cam=False,
        add_wrist_cam=False,
        add_video_cam=True,
    )
    _settle(bundle, 60)
    driver = GenesisSceneDriver(bundle, seed=scenario.seed)
    base_snapshot = driver.capture_snapshot()
    footprint_radii = {
        name: asset.radius_xy for name, asset in get_ycb_assets().items()
    }
    challenge_snapshot = apply_gate33_scenario(
        base_snapshot,
        scenario,
        footprint_radii_m=footprint_radii,
    )
    driver.restore_snapshot(challenge_snapshot)
    RuntimeDynamicsController(bundle).apply(
        pick_object=scenario.pick_object,
        friction_ratio=scenario.friction_ratio,
        target_mass_ratio=scenario.target_mass_ratio,
    )
    _settle(bundle, SETTLE_STEPS)
    settled_snapshot = driver.capture_snapshot()
    formal_object_poses = dict(settled_snapshot.object_poses)
    obstacle_name = PRIMARY_OBSTACLE_BY_PICK[scenario.pick_object]
    for object_name, report_key in (
        (scenario.pick_object, "target_xyz"),
        (obstacle_name, "obstacle_xyz"),
    ):
        current_pose = formal_object_poses[object_name]
        formal_object_poses[object_name] = EntityPose(
            position=tuple(
                float(value) for value in formal_episode[report_key]
            ),
            quaternion=current_pose.quaternion,
        )
    episode_snapshot = EpisodeSnapshot(
        seed=scenario.seed,
        robot_qpos=settled_snapshot.robot_qpos,
        object_poses=formal_object_poses,
    )

    driver.restore_snapshot(episode_snapshot)
    target_xyz = tuple(
        float(value) for value in formal_episode["target_xyz"]
    )
    obstacle_xyz = tuple(
        float(value) for value in formal_episode["obstacle_xyz"]
    )
    nominal = ActionCandidate(**formal_episode["baseline"]["candidate"])
    if nominal.candidate_id != NOMINAL_CANDIDATE_ID:
        raise ValueError("formal baseline candidate is not the frozen nominal action")
    guardian_candidate_id = formal_episode["selection"]["selected_candidate_id"]
    guardian = ActionCandidate(**formal_episode["guardiansim"]["candidate"])
    if guardian.candidate_id != guardian_candidate_id:
        raise ValueError("formal GuardianSim action does not match the selector")

    driver.restore_snapshot(episode_snapshot)
    baseline_recorder = CameraFrameRecorder(
        bundle,
        capture_every=args.capture_every,
    )
    baseline_recorder.capture()
    baseline_measurement = run_grasp_candidate(
        bundle,
        nominal,
        pick_object=scenario.pick_object,
        frame_callback=baseline_recorder,
    )
    baseline_metrics = candidate_metrics_from_measurement(baseline_measurement)
    baseline_recorder.capture()
    baseline_classification = classify_gate31_execution(
        baseline_metrics,
        minimum_stability=GATE32_MINIMUM_STABILITY,
        minimum_safe_clearance_m=GATE32_MINIMUM_SAFE_CLEARANCE_M,
    )

    driver.restore_snapshot(episode_snapshot)
    guardian_recorder = CameraFrameRecorder(
        bundle,
        capture_every=args.capture_every,
    )
    guardian_recorder.capture()
    guardian_measurement = run_grasp_candidate(
        bundle,
        guardian,
        pick_object=scenario.pick_object,
        frame_callback=guardian_recorder,
    )
    guardian_metrics = candidate_metrics_from_measurement(guardian_measurement)
    guardian_recorder.capture()
    guardian_classification = classify_gate31_execution(
        guardian_metrics,
        minimum_stability=GATE32_MINIMUM_STABILITY,
        minimum_safe_clearance_m=GATE32_MINIMUM_SAFE_CLEARANCE_M,
    )

    formal_baseline = formal_episode["baseline"]["execution"]["classification"]
    formal_guardian = formal_episode["guardiansim"]["execution"]["classification"]
    replay_baseline = asdict(baseline_classification)
    replay_guardian = asdict(guardian_classification)
    accepted = replay_retains_contact_to_safe_contrast(
        formal_baseline=formal_baseline,
        formal_guardian=formal_guardian,
        replay_baseline=replay_baseline,
        replay_guardian=replay_guardian,
    )

    output_path = Path(args.output)
    diagnostic_path = output_path.with_suffix(".diagnostic.json")
    diagnostic_path.parent.mkdir(parents=True, exist_ok=True)
    diagnostic = {
        "kind": "gate33_visual_replay_diagnostic",
        "accepted_for_presentation": accepted,
        "physics_reexecuted": True,
        "statistical_trial_added": False,
        "not_appended_to_gate33_report": True,
        "formal_geometry_reconstructed_from_report": True,
        "formal_report": str(report_path),
        "formal_report_sha256": _sha256(report_path),
        "formal_protocol_sha256": report["protocol"]["protocol_sha256"],
        "formal_matrix_sha256": report["protocol"]["scenario_matrix_sha256"],
        "seed": scenario.seed,
        "scenario_id": scenario.scenario_id,
        "formal": {
            "baseline": formal_episode["baseline"]["execution"],
            "guardiansim": formal_episode["guardiansim"]["execution"],
        },
        "visual_replay": {
            "baseline": {
                "candidate": asdict(nominal),
                "metrics": asdict(baseline_metrics),
                "classification": replay_baseline,
                "frame_count": len(baseline_recorder.frames),
            },
            "guardiansim": {
                "candidate": asdict(guardian),
                "metrics": asdict(guardian_metrics),
                "classification": replay_guardian,
                "frame_count": len(guardian_recorder.frames),
            },
        },
    }
    diagnostic_path.write_text(
        json.dumps(diagnostic, default=json_default, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    if not accepted:
        print(json.dumps(diagnostic, default=json_default, indent=2))
        raise RuntimeError(
            "fresh replay did not retain the verified contact-to-safe contrast; "
            "diagnostic preserved and presentation video rejected"
        )

    _compose_video(
        baseline_frames=baseline_recorder.frames,
        guardian_frames=guardian_recorder.frames,
        baseline_metrics=baseline_metrics,
        guardian_metrics=guardian_metrics,
        scenario_label=(
            f"GATE 3.3 VISUAL REPLAY · seed {scenario.seed} · "
            f"{scenario.pick_object} · {scenario.layout}"
        ),
        obstacle_xyz=obstacle_xyz,
        capture_every=args.capture_every,
        baseline_yaw_degrees=nominal.yaw_degrees,
        guardian_yaw_degrees=guardian.yaw_degrees,
        output_path=output_path,
        fps=args.fps,
    )

    presentation = {
        **diagnostic,
        "kind": "gate33_visual_replay_not_formal_evidence",
        "output_video": str(output_path),
        "output_video_sha256": _sha256(output_path),
        "output_fps": args.fps,
    }
    sidecar_path = output_path.with_suffix(".json")
    sidecar_path.write_text(
        json.dumps(presentation, default=json_default, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "accepted_for_presentation": True,
                "video": str(output_path),
                "video_sha256": presentation["output_video_sha256"],
                "sidecar": str(sidecar_path),
                "baseline_failure": baseline_classification.failure_type,
                "guardian_failure": guardian_classification.failure_type,
                "baseline_clearance_m": baseline_metrics.collision_margin_m,
                "guardian_clearance_m": guardian_metrics.collision_margin_m,
                "baseline_frames": len(baseline_recorder.frames),
                "guardian_frames": len(guardian_recorder.frames),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
