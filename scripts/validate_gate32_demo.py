#!/usr/bin/env python3
"""Strictly bind a Gate 3.2 visual replay and presentation to formal evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2

from guardian_sim.demo_validation import validate_gate32_replay_bundle
from guardian_sim.gate32_benchmark import validate_gate32_payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _video_metadata(path: Path) -> dict[str, object]:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError(f"cannot decode video: {path}")
    try:
        frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    finally:
        capture.release()
    if not frames or fps <= 0.0 or width < 1280 or height < 720:
        raise ValueError(f"video metadata is outside presentation bounds: {path}")
    return {
        "path": str(path),
        "sha256": _sha256(path),
        "width": width,
        "height": height,
        "frame_count": frames,
        "fps": fps,
        "duration_seconds": frames / fps,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--formal-report",
        default="docs/evidence/gate-3-2/formal-report.json",
    )
    parser.add_argument(
        "--source-sidecar",
        default="docs/demo/gate-3-2-seed-411.json",
    )
    parser.add_argument(
        "--source-video",
        default="docs/demo/gate-3-2-seed-411.mp4",
    )
    parser.add_argument("--presentation-sidecar")
    parser.add_argument("--presentation-video")
    parser.add_argument("--output")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    formal_path = Path(args.formal_report)
    replay_path = Path(args.source_sidecar)
    source_video_path = Path(args.source_video)
    formal = json.loads(formal_path.read_text(encoding="utf-8"))
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    validate_gate32_payload(formal, require_complete=True)
    result = validate_gate32_replay_bundle(
        formal_report=formal,
        replay=replay,
    )
    result["formal_report"] = {
        "path": str(formal_path),
        "sha256": _sha256(formal_path),
        "completed_episode_count": formal["completed_episode_count"],
    }
    result["source_sidecar"] = {
        "path": str(replay_path),
        "sha256": _sha256(replay_path),
    }
    result["source_video"] = _video_metadata(source_video_path)

    if bool(args.presentation_sidecar) != bool(args.presentation_video):
        raise ValueError(
            "presentation sidecar and video must be supplied together"
        )
    if args.presentation_sidecar:
        presentation_path = Path(args.presentation_sidecar)
        presentation_video_path = Path(args.presentation_video)
        presentation = json.loads(
            presentation_path.read_text(encoding="utf-8")
        )
        if presentation.get("kind") not in {
            "gate32_annotated_presentation_from_verified_replay",
            "gate32_aegis_motion_showcase_from_verified_replay",
        }:
            raise ValueError("unexpected Gate 3.2 presentation kind")
        if presentation.get("physics_reexecuted") is not False:
            raise ValueError("presentation must declare no physics re-execution")
        if presentation.get("statistical_trial_added") is not False:
            raise ValueError("presentation must declare no statistical trial")
        if (
            presentation.get("seed") != replay["seed"]
            or presentation.get("scenario_id") != replay["scenario_id"]
        ):
            raise ValueError("presentation scenario identity mismatch")
        if presentation["source_video_sha256"] != _sha256(source_video_path):
            raise ValueError("presentation source-video hash mismatch")
        if presentation["source_sidecar_sha256"] != _sha256(replay_path):
            raise ValueError("presentation source-sidecar hash mismatch")
        if (
            "formal_report_sha256" in presentation
            and presentation["formal_report_sha256"] != _sha256(formal_path)
        ):
            raise ValueError("presentation formal-report hash mismatch")
        presentation_video = _video_metadata(presentation_video_path)
        if presentation["output_video_sha256"] != presentation_video["sha256"]:
            raise ValueError("presentation output-video hash mismatch")
        result["presentation_sidecar"] = {
            "path": str(presentation_path),
            "sha256": _sha256(presentation_path),
        }
        result["presentation_video"] = presentation_video

    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
