#!/usr/bin/env python3
"""Strictly validate the narrated 90-second GuardianSim Radeon Scale V3 cut."""

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
    / "docs/submission/GuardianSim-Radeon-Scale-V3-narrated-v3.json"
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
        payload["kind"] == "guardiansim_radeon_scale_v3_narrated_v3",
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
    require(89.9 <= duration <= 90.1, "Output duration drift")

    visual = payload["visual_source"]
    visual_path = ROOT / visual["path"]
    require(sha256(visual_path) == visual["sha256"], "Visual source hash mismatch")
    silent_sidecar = visual_path.with_suffix(".json")
    require(
        sha256(silent_sidecar) == visual["sidecar_sha256"],
        "Visual sidecar hash mismatch",
    )

    narration = payload["narration"]
    require(narration["provider"] == "Alibaba Cloud Model Studio", "Provider drift")
    require(narration["model"] == "qwen3-tts-instruct-flash-2026-01-26", "Model drift")
    require(narration["voice"] == "Ethan", "Voice drift")
    require(narration["fixed_chapter_captions"] is True, "Caption policy drift")
    caption_path = ROOT / narration["caption_file"]
    require(sha256(caption_path) == narration["caption_sha256"], "Caption hash mismatch")
    require(len(narration["segments"]) == 7, "Narration segment count drift")
    for segment in narration["segments"]:
        require(len(segment["audio_sha256"]) == 64, f"Missing audio hash: {segment['slug']}")
        require(segment["audio_duration_seconds"] < segment["end_seconds"] - segment["start_seconds"], "Audio overruns chapter")

    metrics = payload["verified_metrics"]
    require(metrics["measurement_count"] == 15, "Measurement count drift")
    require(metrics["largest_parallel_batch"] == 16384, "Batch claim drift")
    require(metrics["largest_batch_throughput_p50"] == 278051, "P50 claim drift")
    require(metrics["largest_batch_throughput_p95"] == 278660, "P95 claim drift")
    require(metrics["total_measured_environment_steps"] == 293601280, "Workload claim drift")
    require(metrics["mean_gpu_utilization_pct"] == 98.33, "Mean GPU claim drift")
    require(metrics["peak_gpu_utilization_pct"] == 100.0, "Peak GPU claim drift")
    require(metrics["peak_vram_used_bytes"] == 23677100032.0, "VRAM claim drift")
    require(metrics["safety_swarm_candidate_world_pairs"] == 4608, "Pair count drift")
    require(metrics["safety_swarm_qualifying_actions"] == 5, "Qualifying action count drift")
    require(metrics["safety_swarm_selected_actions"] == 1, "Selected action count drift")
    require(
        metrics["formal_repeatable_safe_scenarios"]
        == {"baseline": 18, "guardiansim": 30, "total": 30},
        "Formal claim drift",
    )
    require(
        payload["sources"]["seed411_replay"]["finale_motion_window_seconds"]
        == [5.0, 12.3],
        "Simulation finale source window drift",
    )

    for source in payload["sources"].values():
        source_path = ROOT / source["path"]
        require(source_path.is_file(), f"Missing source: {source_path}")
        require(sha256(source_path) == source["sha256"], f"Source hash mismatch: {source_path}")

    formal_path = ROOT / payload["sources"]["gate32_formal_report"]["path"]
    formal = json.loads(formal_path.read_text())
    require(
        formal["summary"]["baseline"]["execution_safe_completion_count"] == 58,
        "Formal baseline safe-execution claim drift",
    )
    require(
        formal["summary"]["guardiansim"]["execution_safe_completion_count"] == 90,
        "Formal GuardianSim safe-execution claim drift",
    )
    require(
        formal["summary"]["baseline"]["clutter_contact_count"] == 30,
        "Formal baseline contact claim drift",
    )
    require(
        formal["summary"]["guardiansim"]["clutter_contact_count"] == 0,
        "Formal GuardianSim contact claim drift",
    )

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
