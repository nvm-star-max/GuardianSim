#!/usr/bin/env python3
"""Add natural Qwen narration and fixed captions to the 90-second Scale V3 cut."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

import imageio_ffmpeg
import numpy as np

if __package__:
    from scripts.qwen_tts import DEFAULT_INSTRUCTIONS, synthesize_text
else:
    from qwen_tts import DEFAULT_INSTRUCTIONS, synthesize_text


ROOT = Path(__file__).resolve().parents[1]
SILENT_VIDEO = (
    ROOT
    / "docs/submission/GuardianSim-Radeon-Scale-V3-review-v2.mp4"
)
SILENT_SIDECAR = (
    ROOT
    / "docs/submission/GuardianSim-Radeon-Scale-V3-review-v2.json"
)
OUTPUT = (
    ROOT
    / "docs/submission/GuardianSim-Radeon-Scale-V3-narrated-v3.mp4"
)
SIDECAR = (
    ROOT
    / "docs/submission/GuardianSim-Radeon-Scale-V3-narrated-v3.json"
)
CAPTIONS = (
    ROOT
    / "docs/submission/GuardianSim-Radeon-Scale-V3-narrated-v3.ass"
)
CACHE = ROOT / "tmp/qwen-narration/radeon-scale-v3"
MIX_WAV = CACHE / "full-mix.wav"
NORMALIZED_WAV = CACHE / "full-mix-normalized.wav"

INSTRUCTIONS = (
    DEFAULT_INSTRUCTIONS
    + " Keep the delivery concise and intelligent. Let the numbers breathe. "
    "Sound like a real engineer speaking to another engineer, not a commercial."
)


@dataclass(frozen=True)
class Chapter:
    slug: str
    start: float
    end: float
    title: str
    narration: str
    caption: str


CHAPTERS = [
    Chapter(
        "compute-hook",
        0.0,
        6.0,
        "Think thousands. Execute one.",
        (
            "Think sixteen thousand three hundred eighty-four worlds. "
            "Execute one."
        ),
        "Think 16,384 worlds. Execute one.",
    ),
    Chapter(
        "radeon-scale",
        6.0,
        24.0,
        "Sustained Radeon scale",
        (
            "On AMD Radeon Cloud, 16,384 full Genesis worlds sustained a median "
            "278,051 environment steps per second. The frozen suite measured "
            "293.6 million steps across fifteen independent runs."
        ),
        "16,384 full worlds · 278,051 env-steps/s P50 · 293.6M measured steps.",
    ),
    Chapter(
        "safety-swarm",
        24.0,
        40.0,
        "From parallel worlds to one action",
        (
            "That scale is useful at decision time. Eighteen proposed actions face two "
            "hundred fifty-six uncertainty worlds each: four thousand six hundred eight "
            "candidate-world pairs. Five clear every hard gate. One is selected."
        ),
        "Safety Swarm: 4,608 candidate-world pairs → 5 eligible → 1 selected.",
    ),
    Chapter(
        "seed-411",
        40.0,
        58.0,
        "Formal Seed 411",
        (
            "Here is formal seed four eleven. Same task, same initial state. The nominal "
            "path overlaps clutter by one point four two millimeters. GuardianSim chooses "
            "a different approach with seventeen point one millimeters of clearance, "
            "safe in all three repeats."
        ),
        "Seed 411: 1.42 mm overlap becomes 17.1 mm clearance.",
    ),
    Chapter(
        "formal-proof",
        58.0,
        72.0,
        "Frozen 30-scenario result",
        (
            "Across the frozen thirty-scenario set, repeatable safe completion rose from "
            "eighteen to thirty. Across ninety independent Genesis simulations, safe "
            "executions rose from fifty-eight to ninety, while sampled clutter contacts "
            "fell from thirty to zero."
        ),
        "Frozen run: 30/30 repeatable safe; sampled contacts 30 → 0.",
    ),
    Chapter(
        "close",
        72.0,
        80.0,
        "What the demo shows",
        (
            "Radeon runs the worlds. GuardianSim reduces them. The robot moves only when "
            "one action survives every check."
        ),
        "Radeon runs the worlds → GuardianSim reduces them → robot moves or stops.",
    ),
    Chapter(
        "simulation-finale",
        80.0,
        90.0,
        "Visible simulation result",
        (
            "The result is visible here: contact on the left; safe clearance on the "
            "right. Think thousands. Execute one."
        ),
        "Contact on the left. Safe clearance on the right.",
    ),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wav_info(path: Path) -> tuple[wave._wave_params, np.ndarray]:
    with wave.open(str(path), "rb") as handle:
        params = handle.getparams()
        if params.nchannels != 1 or params.sampwidth != 2:
            raise ValueError(f"Expected mono 16-bit WAV: {path}")
        frames = handle.readframes(params.nframes)
    return params, np.frombuffer(frames, dtype="<i2").astype(np.float64)


def ass_time(seconds: float) -> str:
    centiseconds = round(seconds * 100)
    hours, remainder = divmod(centiseconds, 360000)
    minutes, remainder = divmod(remainder, 6000)
    secs, cents = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{cents:02d}"


def write_captions() -> None:
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Fixed,Arial,34,&H00F7FBFF,&H00F7FBFF,&H00101A22,&HCC05090D,-1,0,0,0,100,100,0,0,3,2,0,2,150,150,125,1
Style: Finale,Arial,34,&H00F7FBFF,&H00F7FBFF,&H00101A22,&HCC05090D,-1,0,0,0,100,100,0,0,3,2,0,8,150,150,82,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for chapter in CHAPTERS:
        caption = chapter.caption.replace("\n", r"\N")
        style = "Finale" if chapter.slug == "simulation-finale" else "Fixed"
        events.append(
            f"Dialogue: 0,{ass_time(chapter.start)},{ass_time(chapter.end)},"
            f"{style},,0,0,0,,{caption}"
        )
    CAPTIONS.write_text(header + "\n".join(events) + "\n")


def build_audio() -> list[dict]:
    CACHE.mkdir(parents=True, exist_ok=True)
    sample_rate: int | None = None
    chapter_audio: list[tuple[Chapter, Path, np.ndarray]] = []
    records: list[dict] = []

    for chapter in CHAPTERS:
        output = CACHE / f"{chapter.slug}.wav"
        result = synthesize_text(
            chapter.narration,
            output,
            cache_dir=CACHE / chapter.slug,
            instructions=INSTRUCTIONS,
        )
        params, samples = wav_info(output)
        if sample_rate is None:
            sample_rate = params.framerate
        if params.framerate != sample_rate:
            raise ValueError("Qwen narration sample-rate drift")
        duration = len(samples) / sample_rate
        available = chapter.end - chapter.start - 0.18
        if duration > available:
            ratio = duration / available
            if ratio > 1.12:
                raise ValueError(
                    f"{chapter.slug} narration is {duration:.2f}s for "
                    f"{available:.2f}s; shorten text instead of over-speeding it"
                )
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            fitted = CACHE / f"{chapter.slug}-fitted.wav"
            subprocess.run(
                [
                    ffmpeg,
                    "-y",
                    "-v",
                    "error",
                    "-i",
                    str(output),
                    "-filter:a",
                    f"atempo={ratio:.8f}",
                    str(fitted),
                ],
                check=True,
            )
            output = fitted
            params, samples = wav_info(output)
            duration = len(samples) / params.framerate
        chapter_audio.append((chapter, output, samples))
        records.append(
            {
                "slug": chapter.slug,
                "title": chapter.title,
                "text": chapter.narration,
                "caption": chapter.caption,
                "start_seconds": chapter.start,
                "end_seconds": chapter.end,
                "audio_duration_seconds": round(duration, 3),
                "audio_sha256": sha256(output),
                "characters": result.characters,
                "chunks": result.chunks,
            }
        )

    if sample_rate is None:
        raise RuntimeError("No narration was generated")
    total_samples = round(90.0 * sample_rate)
    timeline = np.zeros(total_samples, dtype=np.float64)

    # Very quiet original ambient bed and short transition chimes.
    times = np.arange(total_samples) / sample_rate
    timeline += 65.0 * np.sin(2 * math.pi * 55.0 * times)
    timeline += 28.0 * np.sin(2 * math.pi * 110.0 * times)
    for chapter in CHAPTERS:
        start = round(chapter.start * sample_rate)
        length = round(0.42 * sample_rate)
        local = np.arange(length) / sample_rate
        envelope = np.exp(-7.0 * local)
        chime = 420.0 * envelope * np.sin(2 * math.pi * 523.25 * local)
        chime += 230.0 * envelope * np.sin(2 * math.pi * 659.25 * local)
        timeline[start : start + length] += chime

    for chapter, _, samples in chapter_audio:
        start = round((chapter.start + 0.08) * sample_rate)
        end = min(start + len(samples), total_samples)
        timeline[start:end] += samples[: end - start]

    rendered = np.clip(timeline, -32768, 32767).astype("<i2")
    with wave.open(str(MIX_WAV), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(rendered.tobytes())

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-v",
            "error",
            "-i",
            str(MIX_WAV),
            "-filter:a",
            "loudnorm=I=-16:LRA=7:TP=-1.5",
            str(NORMALIZED_WAV),
        ],
        check=True,
    )
    return records


def mux_video() -> None:
    write_captions()
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subtitle_filter = f"ass={CAPTIONS.as_posix()}"
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-v",
            "error",
            "-i",
            str(SILENT_VIDEO),
            "-i",
            str(NORMALIZED_WAV),
            "-vf",
            subtitle_filter,
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "19",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-t",
            "90",
            "-movflags",
            "+faststart",
            str(OUTPUT),
        ],
        check=True,
    )


def main() -> None:
    silent = json.loads(SILENT_SIDECAR.read_text())
    if silent["output"]["sha256"] != sha256(SILENT_VIDEO):
        raise ValueError("Silent review source hash mismatch")
    narration = build_audio()
    mux_video()
    payload = {
        "kind": "guardiansim_radeon_scale_v3_narrated_v3",
        "team": "Aegis Motion",
        "project": "GuardianSim",
        "claim_boundary": silent["claim_boundary"],
        "output": {
            "path": str(OUTPUT.relative_to(ROOT)),
            "sha256": sha256(OUTPUT),
            "duration_seconds": 90,
            "fps": 20,
            "width": 1920,
            "height": 1080,
            "audio": True,
        },
        "visual_source": {
            "path": str(SILENT_VIDEO.relative_to(ROOT)),
            "sha256": sha256(SILENT_VIDEO),
            "sidecar_sha256": sha256(SILENT_SIDECAR),
        },
        "narration": {
            "provider": "Alibaba Cloud Model Studio",
            "model": "qwen3-tts-instruct-flash-2026-01-26",
            "voice": "Ethan",
            "instructions": INSTRUCTIONS,
            "fixed_chapter_captions": True,
            "caption_file": str(CAPTIONS.relative_to(ROOT)),
            "caption_sha256": sha256(CAPTIONS),
            "ambient_bed": "original synthesized low-volume sine bed and transition chimes",
            "segments": narration,
        },
        "verified_metrics": silent["verified_metrics"],
        "sources": silent["sources"],
    }
    SIDECAR.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload["output"], indent=2))


if __name__ == "__main__":
    main()
