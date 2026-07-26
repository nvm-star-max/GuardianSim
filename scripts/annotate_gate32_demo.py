#!/usr/bin/env python3
"""Create a slow, annotated explainer from a verified Gate 3.2 replay MP4.

This is presentation-only post-processing. It does not initialize Genesis,
execute an action, or add a statistical trial.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import cv2
from record_gate32_demo import _compose_video

SOURCE_CAPTURE_EVERY = 4
SOURCE_FRAME_TOP = 76
SOURCE_FRAME_HEIGHT = 720


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-video",
        default="docs/demo/gate-3-2-seed-411.mp4",
    )
    parser.add_argument(
        "--source-sidecar",
        default="docs/demo/gate-3-2-seed-411.json",
    )
    parser.add_argument(
        "--output",
        default="outputs/demo/gate-3-2-seed-411-explained.mp4",
    )
    parser.add_argument("--fps", type=int, default=10)
    return parser


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _namespace(value):
    if isinstance(value, dict):
        return SimpleNamespace(**{key: _namespace(item) for key, item in value.items()})
    if isinstance(value, list):
        return [_namespace(item) for item in value]
    return value


def _read_source_panels(path: Path) -> tuple[list, list]:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise RuntimeError(f"cannot open source video: {path}")
    left_frames = []
    right_frames = []
    try:
        while True:
            ok, bgr = capture.read()
            if not ok:
                break
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            height, width = rgb.shape[:2]
            if height < SOURCE_FRAME_TOP + SOURCE_FRAME_HEIGHT or width % 2:
                raise RuntimeError(
                    f"unexpected source dimensions {width}x{height}; expected the original side-by-side replay layout"
                )
            panel_width = width // 2
            bottom = SOURCE_FRAME_TOP + SOURCE_FRAME_HEIGHT
            left_frames.append(rgb[SOURCE_FRAME_TOP:bottom, :panel_width].copy())
            right_frames.append(rgb[SOURCE_FRAME_TOP:bottom, panel_width:].copy())
    finally:
        capture.release()
    if not left_frames:
        raise RuntimeError("source video contains no decodable frames")
    return left_frames, right_frames


def main() -> None:
    args = build_parser().parse_args()
    if args.fps < 1:
        raise ValueError("--fps must be positive")

    source_video = Path(args.source_video)
    source_sidecar = Path(args.source_sidecar)
    replay = json.loads(source_sidecar.read_text(encoding="utf-8"))
    if replay.get("kind") != "gate32_visual_replay_not_formal_evidence":
        raise ValueError("source sidecar is not a Gate 3.2 visual replay")

    formal_report_path = Path(replay["formal_report"])
    formal_report = json.loads(formal_report_path.read_text(encoding="utf-8"))
    formal_episode = next(item for item in formal_report["episodes"] if item["seed"] == replay["seed"])
    obstacle_xyz = tuple(float(value) for value in formal_episode["obstacle_xyz"])

    baseline_frames, guardian_frames = _read_source_panels(source_video)
    baseline = replay["visual_replay"]["baseline"]
    guardian = replay["visual_replay"]["guardiansim"]
    baseline_metrics = _namespace(baseline["metrics"])
    guardian_metrics = _namespace(guardian["metrics"])
    output_path = Path(args.output)

    _compose_video(
        baseline_frames=baseline_frames,
        guardian_frames=guardian_frames,
        baseline_metrics=baseline_metrics,
        guardian_metrics=guardian_metrics,
        scenario_label=(f"VERIFIED SOURCE MP4 · seed {replay['seed']} · {replay['pick_object']} · {replay['layout']}"),
        obstacle_xyz=obstacle_xyz,
        capture_every=SOURCE_CAPTURE_EVERY,
        baseline_yaw_degrees=float(baseline["candidate"]["yaw_degrees"]),
        guardian_yaw_degrees=float(guardian["candidate"]["yaw_degrees"]),
        output_path=output_path,
        fps=args.fps,
    )

    presentation = {
        "kind": "gate32_annotated_presentation_from_verified_replay",
        "physics_reexecuted": False,
        "statistical_trial_added": False,
        "seed": replay["seed"],
        "scenario_id": replay["scenario_id"],
        "source_video": str(source_video),
        "source_video_sha256": _sha256(source_video),
        "source_sidecar": str(source_sidecar),
        "source_sidecar_sha256": _sha256(source_sidecar),
        "output_video": str(output_path),
        "output_video_sha256": _sha256(output_path),
        "output_fps": args.fps,
        "source_frame_count": len(baseline_frames),
        "baseline": {
            "failure_type": baseline["classification"]["failure_type"],
            "clearance_m": baseline["metrics"]["collision_margin_m"],
            "overlap_depth_m": baseline["metrics"]["clearance_diagnostic"]["overlap_depth_m"],
            "stability": baseline["metrics"]["predicted_stability"],
        },
        "guardiansim": {
            "failure_type": guardian["classification"]["failure_type"],
            "clearance_m": guardian["metrics"]["collision_margin_m"],
            "overlap_depth_m": guardian["metrics"]["clearance_diagnostic"]["overlap_depth_m"],
            "stability": guardian["metrics"]["predicted_stability"],
        },
    }
    presentation_path = output_path.with_suffix(".json")
    presentation_path.write_text(
        json.dumps(presentation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(presentation, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
