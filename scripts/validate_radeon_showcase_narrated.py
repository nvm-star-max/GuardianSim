#!/usr/bin/env python3
"""Strictly validate the narrated 80-second GuardianSim Radeon cut."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import cv2
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SIDECAR = (
    ROOT
    / "docs/submission/GuardianSim-Radeon-Parallel-Futures-narrated-v4.json"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(sidecar: Path = DEFAULT_SIDECAR) -> dict:
    payload = json.loads(sidecar.read_text())
    require(
        payload["kind"] == "guardiansim_radeon_parallel_futures_narrated_v4",
        "Unexpected video kind",
    )
    require(payload["team"] == "Aegis Motion", "Unexpected team")
    require(payload["project"] == "GuardianSim", "Unexpected project")
    require("not independent safety scenes" in payload["claim_boundary"], "Missing scale boundary")
    require("no physical-robot claim" in payload["claim_boundary"], "Missing simulation boundary")

    output = payload["output"]
    output_path = ROOT / output["path"]
    require(output_path.is_file(), "Missing narrated video")
    require(sha256(output_path) == output["sha256"], "Output hash mismatch")
    require(output["audio"] is True, "Narrated cut must record audio")

    capture = cv2.VideoCapture(str(output_path))
    require(capture.isOpened(), "Could not open narrated video")
    frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    decoded = 0
    for fraction in (0.0, 0.08, 0.2, 0.4, 0.55, 0.72, 0.9, 0.99):
        capture.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(frames * fraction) - 1))
        ok, frame = capture.read()
        require(ok and frame is not None and frame.size > 0, f"Decode failed at {fraction}")
        decoded += 1
    capture.release()
    duration = frames / fps
    require(width == 1920 and height == 1080, "Output must be 1920x1080")
    require(abs(fps - 20.0) < 0.01, "Output must be 20 FPS")
    require(79.9 <= duration <= 80.1, "Output duration drift")

    visual = payload["visual_source"]
    visual_path = ROOT / visual["path"]
    require(sha256(visual_path) == visual["sha256"], "Visual source hash mismatch")

    narration = payload["narration"]
    require(narration["provider"] == "Alibaba Cloud Model Studio", "Provider drift")
    require(narration["model"] == "qwen3-tts-instruct-flash-2026-01-26", "Model drift")
    require(narration["voice"] == "Ethan", "Voice drift")
    require(narration["fixed_chapter_captions"] is True, "Caption policy drift")
    caption_path = ROOT / narration["caption_file"]
    require(sha256(caption_path) == narration["caption_sha256"], "Caption hash mismatch")
    require(len(narration["segments"]) == 6, "Narration segment count drift")
    for segment in narration["segments"]:
        require(len(segment["audio_sha256"]) == 64, f"Missing audio hash: {segment['slug']}")
        require(segment["audio_duration_seconds"] < segment["end_seconds"] - segment["start_seconds"], "Audio overruns chapter")

    metrics = payload["verified_metrics"]
    require(metrics["largest_parallel_batch"] == 256, "Batch claim drift")
    require(metrics["environment_steps_per_second"] == 35166, "Throughput claim drift")
    require(metrics["speedup_vs_single_world"] == 228.16, "Speedup claim drift")
    require(metrics["parallel_future_worlds"] == 54, "Future count drift")
    require(metrics["parallel_future_hard_safe"] == 32, "Safe count drift")
    require(metrics["parallel_future_rejected"] == 22, "Rejected count drift")
    require(
        metrics["formal_repeatable_safe_scenarios"]
        == {"baseline": 18, "guardiansim": 30, "total": 30},
        "Formal claim drift",
    )

    for source in payload["sources"].values():
        source_path = ROOT / source["path"]
        require(source_path.is_file(), f"Missing source: {source_path}")
        require(sha256(source_path) == source["sha256"], f"Source hash mismatch: {source_path}")

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    full_decode = subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-i",
            str(output_path),
            "-map",
            "0:v:0",
            "-map",
            "0:a:0",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    require(full_decode.returncode == 0, f"Full A/V decode failed: {full_decode.stderr}")

    return {
        "validated": True,
        "video": output["path"],
        "sha256": output["sha256"],
        "duration_seconds": duration,
        "fps": fps,
        "width": width,
        "height": height,
        "decoded_sample_count": decoded,
        "full_audio_video_decode": True,
        "source_hashes_verified": True,
        "narration_hashes_verified": True,
        "fixed_captions_verified": True,
        "claim_boundaries_verified": True,
        "verified_metrics_locked": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("sidecar", nargs="?", type=Path, default=DEFAULT_SIDECAR)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.sidecar.resolve())
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
