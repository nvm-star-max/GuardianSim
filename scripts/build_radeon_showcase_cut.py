#!/usr/bin/env python3
"""Build an 80-second scale-first GuardianSim visual review cut.

This artifact is assembled only from preserved, validated evidence. It does not
re-run Genesis, add a statistical trial, or claim that throughput worlds are
independent safety scenes. The review cut is intentionally silent; narration is
added only after the visual sequence is accepted.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import cv2
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
WIDTH = 1920
HEIGHT = 1080
FPS = 20
DURATION_SECONDS = 80

BG = (3, 9, 13)
PANEL = (7, 18, 25)
PANEL_2 = (10, 27, 35)
WHITE = (238, 249, 255)
MUTED = (128, 149, 160)
CYAN = (70, 220, 255)
GREEN = (119, 255, 178)
RED = (255, 104, 88)
ACID = (216, 255, 95)

FONT_REGULAR = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
FONT_BOLD = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")
FONT_MONO = Path("/System/Library/Fonts/Supplemental/Courier New.ttf")

SCALE_REPORT = (
    ROOT
    / "docs/evidence/radeon-p0-2026-07-29/radeon-scale/report.json"
)
SCALE_VALIDATION = (
    ROOT
    / "docs/evidence/radeon-p0-2026-07-29/radeon-scale/validation.json"
)
FUTURES_REPORT = (
    ROOT
    / "docs/evidence/radeon-p0-2026-07-29/parallel-futures/report.json"
)
FUTURES_VALIDATION = (
    ROOT
    / "docs/evidence/radeon-p0-2026-07-29/parallel-futures/validation.json"
)
FORMAL_REPORT = ROOT / "docs/evidence/gate-3-2/formal-report.json"
HERO_VIDEO = ROOT / "docs/demo/gate-3-2-seed-411-aegis-showcase-v3.mp4"

OUTPUT = (
    ROOT
    / "docs/submission/GuardianSim-Radeon-Parallel-Futures-review-v3.mp4"
)
SIDECAR = (
    ROOT
    / "docs/submission/GuardianSim-Radeon-Parallel-Futures-review-v3.json"
)
PREVIEW = (
    ROOT
    / "docs/submission/GuardianSim-Radeon-Parallel-Futures-review-v3-preview.png"
)


def font(size: int, *, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_MONO if mono else (FONT_BOLD if bold else FONT_REGULAR)
    return ImageFont.truetype(str(path), size=size)


def fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    max_width: int,
    max_size: int,
    min_size: int,
    bold: bool = False,
    mono: bool = False,
) -> ImageFont.FreeTypeFont:
    """Return the largest font that keeps the complete string inside max_width."""
    for size in range(max_size, min_size - 1, -1):
        candidate = font(size, bold=bold, mono=mono)
        box = draw.textbbox((0, 0), text, font=candidate)
        if box[2] - box[0] <= max_width:
            return candidate
    raise ValueError(f"Text cannot fit within {max_width}px: {text}")


def text_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    text_font: ImageFont.FreeTypeFont,
) -> int:
    box = draw.textbbox((0, 0), text, font=text_font)
    return box[2] - box[0]


def centered_metric_row(
    draw: ImageDraw.ImageDraw,
    before: str,
    after: str,
    *,
    left: int,
    right: int,
    max_size: int = 44,
    min_size: int = 26,
) -> tuple[
    ImageFont.FreeTypeFont,
    ImageFont.FreeTypeFont,
    int,
    int,
    int,
]:
    """Measure and center before → after as one optical group."""
    available = right - left
    for size in range(max_size, min_size - 1, -1):
        value_font = font(size, bold=True)
        arrow_font = font(max(24, size - 10), bold=True)
        before_width = text_width(draw, before, value_font)
        arrow_width = text_width(draw, "→", arrow_font)
        after_width = text_width(draw, after, value_font)
        gap = max(14, round(size * 0.42))
        total = before_width + gap + arrow_width + gap + after_width
        if total <= available:
            start = left + (available - total) // 2
            arrow_x = start + before_width + gap
            after_x = arrow_x + arrow_width + gap
            if start < left or after_x + after_width > right:
                raise AssertionError("Centered metric row escaped its measured bounds")
            left_padding = start - left
            right_padding = right - (after_x + after_width)
            if abs(left_padding - right_padding) > 1:
                raise AssertionError("Centered metric row has asymmetric padding")
            return value_font, arrow_font, start, arrow_x, after_x
    raise ValueError(
        f"Metric row cannot fit within {available}px: {before} → {after}"
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rounded(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    fill: tuple[int, int, int],
    outline: tuple[int, int, int] | None = None,
    width: int = 2,
    radius: int = 22,
) -> None:
    draw.rounded_rectangle(
        box,
        radius=radius,
        fill=fill,
        outline=outline,
        width=width,
    )


def label(draw: ImageDraw.ImageDraw, text: str, x: int, y: int, *, color=CYAN) -> None:
    draw.text((x, y), text, font=font(22, bold=True, mono=True), fill=color)


def base_frame(chapter: str) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, WIDTH, 8), fill=CYAN)
    label(draw, "AEGIS MOTION  /  GUARDIANSIM", 64, 38)
    draw.text(
        (WIDTH - 64, 42),
        chapter,
        anchor="ra",
        font=font(20, bold=True, mono=True),
        fill=MUTED,
    )
    draw.text(
        (64, HEIGHT - 42),
        "Genesis simulation · preserved evidence · no physical-robot claim",
        font=font(18),
        fill=(75, 96, 107),
    )
    return image


def draw_world_grid(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    visible: int,
    total: int = 256,
) -> None:
    x0, y0, x1, y1 = box
    columns = 16
    rows = 16
    gap = 8
    cell_w = (x1 - x0 - gap * (columns - 1)) / columns
    cell_h = (y1 - y0 - gap * (rows - 1)) / rows
    for index in range(total):
        row, column = divmod(index, columns)
        left = int(x0 + column * (cell_w + gap))
        top = int(y0 + row * (cell_h + gap))
        right = int(left + cell_w)
        bottom = int(top + cell_h)
        active = index < visible
        color = GREEN if active and index % 19 == 0 else CYAN
        fill = (13, 58, 52) if active and index % 19 == 0 else (5, 34, 45)
        if not active:
            color = (24, 46, 55)
            fill = (7, 19, 25)
        draw.rectangle((left, top, right, bottom), fill=fill, outline=color, width=2)
        if active:
            draw.line(
                (left + 5, bottom - 5, right - 5, top + 5),
                fill=color,
                width=2,
            )


def render_title(t: float) -> Image.Image:
    image = base_frame("01 / THE COMPUTE HOOK")
    draw = ImageDraw.Draw(image)
    draw.text((72, 192), "256 WORLDS ON ONE RADEON GPU.", font=font(78, bold=True), fill=WHITE)
    draw.text((72, 310), "THEN TEST 54 WAYS TO MOVE.", font=font(78), fill=ACID)
    draw.text(
        (76, 455),
        "We measured the GPU work first. Then we used the same",
        font=font(32),
        fill=MUTED,
    )
    draw.text(
        (76, 500),
        "parallel setup to reject unsafe actions before execution.",
        font=font(32),
        fill=MUTED,
    )
    rounded(draw, (76, 620, 610, 890), fill=ACID)
    label(draw, "MEASURED ON RADEON CLOUD", 112, 660, color=BG)
    draw.text((110, 710), "35,166", font=font(88, bold=True), fill=BG)
    draw.text((112, 805), "env-steps/s · 256 worlds", font=font(25), fill=BG)
    rounded(draw, (650, 620, 1210, 890), fill=PANEL_2, outline=CYAN)
    label(draw, "THROUGHPUT SCALE-UP", 690, 660)
    draw.text((688, 710), "228.16×", font=font(82, bold=True), fill=WHITE)
    draw.text((690, 805), "89.1% parallel efficiency", font=font(25), fill=MUTED)
    rounded(draw, (1250, 620, 1844, 890), fill=PANEL_2, outline=GREEN)
    label(draw, "GPU USE", 1290, 660, color=GREEN)
    draw.text((1288, 710), "96%", font=font(82, bold=True), fill=WHITE)
    draw.text((1290, 805), "peak GPU · 85.5% mean", font=font(25), fill=MUTED)
    return image


def render_scale(t: float) -> Image.Image:
    image = base_frame("02 / RADEON SCALE")
    draw = ImageDraw.Draw(image)
    draw.text((64, 100), "MEASURED GENESIS THROUGHPUT", font=font(58, bold=True), fill=WHITE)
    steps = [
        (1, 154, "1.00×"),
        (16, 2384, "15.47×"),
        (64, 9354, "60.69×"),
        (256, 35166, "228.16×"),
    ]
    stage = min(3, int(t / 4.5))
    stage_progress = min(1.0, (t - stage * 4.5) / 2.2)
    visible_worlds = int(steps[stage][0] * max(0.08, stage_progress))
    draw_world_grid(draw, (64, 220, 1120, 935), visible=max(1, visible_worlds))
    for index, (worlds, throughput, speedup) in enumerate(steps):
        left = 1180 + (index % 2) * 330
        top = 235 + (index // 2) * 350
        active = index <= stage
        outline = GREEN if index == stage else ((43, 90, 103) if active else (24, 45, 53))
        fill = (8, 35, 34) if index == stage else PANEL
        rounded(draw, (left, top, left + 290, top + 310), fill=fill, outline=outline, width=3)
        label(draw, f"BATCH {index + 1:02d}", left + 24, top + 22, color=outline)
        draw.text(
            (left + 22, top + 68),
            f"{worlds}",
            font=font(72, bold=True),
            fill=WHITE if active else (64, 82, 90),
        )
        draw.text((left + 24, top + 152), "parallel worlds", font=font(20), fill=MUTED)
        draw.text(
            (left + 24, top + 205),
            f"{throughput:,}",
            font=font(30, bold=True, mono=True),
            fill=GREEN if active else (64, 82, 90),
        )
        draw.text((left + 24, top + 247), f"{speedup} speedup", font=font(20), fill=MUTED)
    draw.text(
        (64, 960),
        f"{steps[stage][0]:>3} WORLDS  ·  {steps[stage][1]:,} ENV-STEPS/S",
        font=font(25, bold=True, mono=True),
        fill=GREEN,
    )
    return image


def render_futures(t: float) -> Image.Image:
    image = base_frame("03 / PARALLEL FUTURES")
    draw = ImageDraw.Draw(image)
    draw.text((64, 100), "54 WAYS TO MAKE THE NEXT MOVE", font=font(58, bold=True), fill=WHITE)
    draw.text(
        (66, 170),
        "18 bounded actions × 3 physical repeats · one batched Genesis scene",
        font=font(27),
        fill=MUTED,
    )
    x0, y0 = 80, 300
    columns = 9
    cell = 92
    gap = 14
    reveal = min(54, max(1, int(t * 6)))
    classified = t >= 4.8
    for index in range(54):
        row, column = divmod(index, columns)
        left = x0 + column * (cell + gap)
        top = y0 + row * (cell + gap)
        if index >= reveal:
            fill, outline = (7, 18, 25), (24, 46, 55)
        elif not classified:
            fill, outline = (5, 40, 53), CYAN
        elif index < 32:
            fill, outline = (18, 77, 58), GREEN
        else:
            fill, outline = (53, 28, 28), RED
        rounded(draw, (left, top, left + cell, top + cell), fill=fill, outline=outline, radius=8)
        draw.text(
            (left + cell // 2, top + cell // 2),
            f"{index + 1:02d}",
            anchor="mm",
            font=font(20, bold=True, mono=True),
            fill=outline,
        )
        if classified and index >= 32:
            draw.line((left + 20, top + 20, left + cell - 20, top + cell - 20), fill=RED, width=5)
    draw.text((1135, 330), "HARD GATE FUNNEL", font=font(24, bold=True, mono=True), fill=CYAN)
    rounded(draw, (1135, 405, 1815, 620), fill=(8, 34, 31), outline=GREEN, width=3)
    draw.text((1180, 445), "32", font=font(96, bold=True), fill=GREEN)
    draw.text((1400, 478), "hard-safe futures", font=font(30, bold=True), fill=WHITE)
    rounded(draw, (1135, 650, 1815, 865), fill=(38, 23, 25), outline=RED, width=3)
    draw.text((1180, 690), "22", font=font(96, bold=True), fill=RED)
    draw.text((1400, 723), "rejected before execution", font=font(30, bold=True), fill=WHITE)
    draw.text((1138, 900), "12.839 s WALL TIME", font=font(38, bold=True, mono=True), fill=CYAN)
    draw.text((1138, 950), "71.8% mean GPU · 95% peak", font=font(23), fill=MUTED)
    return image


def load_video_frames(path: Path) -> list[Image.Image]:
    capture = cv2.VideoCapture(str(path))
    frames: list[Image.Image] = []
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        frames.append(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
    capture.release()
    if not frames:
        raise RuntimeError(f"No frames decoded from {path}")
    return frames


def render_replay(t: float, frames: list[Image.Image]) -> Image.Image:
    progress = min(0.999, max(0.0, t / 18.0))
    index = min(int(progress * len(frames)), len(frames) - 1)
    image = frames[index].resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, WIDTH, 82), fill=BG)
    label(draw, "FORMAL SEED 411  ·  SAME TASK  ·  SAME INITIAL STATE", 50, 28)
    draw.rectangle((0, HEIGHT - 95, WIDTH, HEIGHT), fill=BG)
    draw.text((70, HEIGHT - 67), "NOMINAL", font=font(23, bold=True), fill=RED)
    draw.text((215, HEIGHT - 67), "1.42 mm overlap", font=font(23), fill=WHITE)
    draw.text((760, HEIGHT - 67), "→", font=font(28, bold=True), fill=CYAN)
    draw.text((860, HEIGHT - 67), "GUARDIANSIM", font=font(23, bold=True), fill=GREEN)
    draw.text((1070, HEIGHT - 67), "17.1 mm clearance · 3/3 safe", font=font(23), fill=WHITE)
    return image


def render_proof(t: float) -> Image.Image:
    image = base_frame("05 / FROZEN TEST SET")
    draw = ImageDraw.Draw(image)
    draw.text(
        (64, 100),
        "RESULTS FROM THE FROZEN 30-SCENARIO RUN",
        font=font(50, bold=True),
        fill=WHITE,
    )
    cards = [
        ("REPEATABLE SAFE SCENARIOS", "18/30", "30/30", "Every GuardianSim scenario passed 3/3."),
        ("INDEPENDENT SAFE EXECUTIONS", "58/90", "90/90", "Three physical executions per scenario."),
        ("CLUTTER CONTACT EXECUTIONS", "30", "0", "Measured sampled clutter contacts."),
        ("MEAN SAMPLED CLEARANCE", "23.191", "46.003 mm", "+98.36% versus nominal."),
    ]
    visible = min(4, max(1, int(t / 2.3) + 1))
    for index, (title, before, after, detail) in enumerate(cards):
        left = 70 + index * 455
        active = index < visible
        rounded(
            draw,
            (left, 290, left + 410, 780),
            fill=PANEL_2 if active else PANEL,
            outline=GREEN if active else (28, 48, 57),
            width=3,
        )
        title_font = fit_font(
            draw,
            title,
            max_width=354,
            max_size=22,
            min_size=16,
            bold=True,
            mono=True,
        )
        title_width = text_width(draw, title, title_font)
        draw.text(
            (left + (410 - title_width) // 2, 325),
            title,
            font=title_font,
            fill=GREEN if active else (55, 77, 87),
        )
        value_font, arrow_font, before_x, arrow_x, after_x = centered_metric_row(
            draw,
            before,
            after,
            left=left + 28,
            right=left + 382,
        )
        draw.text(
            (before_x, 435),
            before,
            font=value_font,
            fill=RED if active else (55, 77, 87),
        )
        draw.text((arrow_x, 445), "→", font=arrow_font, fill=CYAN)
        draw.text(
            (after_x, 435),
            after,
            font=value_font,
            fill=GREEN if active else (55, 77, 87),
        )
        detail_font = fit_font(
            draw,
            detail,
            max_width=354,
            max_size=18,
            min_size=14,
        )
        detail_width = text_width(draw, detail, detail_font)
        draw.text(
            (left + (410 - detail_width) // 2, 650),
            detail,
            font=detail_font,
            fill=MUTED if active else (55, 77, 87),
        )
    draw.text(
        (70, 870),
        "FROZEN SCHEMA-5 · 30 SCENARIOS · 3 EXECUTIONS PER STRATEGY",
        font=font(28, bold=True, mono=True),
        fill=CYAN,
    )
    return image


def render_close(t: float) -> Image.Image:
    image = base_frame("06 / WHAT THE DEMO SHOWS")
    draw = ImageDraw.Draw(image)
    draw.text((90, 225), "GUARDIANSIM", font=font(116, bold=True), fill=WHITE)
    draw.text((96, 355), "PARALLEL FUTURES ON AMD RADEON", font=font(48, bold=True), fill=ACID)
    rounded(draw, (96, 500, 1820, 750), fill=PANEL_2, outline=CYAN)
    draw.text(
        (140, 548),
        "The GPU tests the options. The robot moves only if one passes every gate.",
        font=fit_font(
            draw,
            "The GPU tests the options. The robot moves only if one passes every gate.",
            max_width=1636,
            max_size=42,
            min_size=30,
            bold=True,
        ),
        fill=WHITE,
    )
    draw.text(
        (140, 630),
        "If none pass, it stays put. Genesis simulation; code and evidence are public.",
        font=font(30),
        fill=MUTED,
    )
    draw.text(
        (98, 835),
        "github.com/nvm-star-max/GuardianSim",
        font=font(32, bold=True, mono=True),
        fill=GREEN,
    )
    return image


def validate_sources() -> tuple[dict, dict, dict]:
    scale = json.loads(SCALE_REPORT.read_text())
    scale_validation = json.loads(SCALE_VALIDATION.read_text())
    futures = json.loads(FUTURES_REPORT.read_text())
    futures_validation = json.loads(FUTURES_VALIDATION.read_text())
    formal = json.loads(FORMAL_REPORT.read_text())

    assert scale_validation["status"] == "passed"
    assert futures_validation["status"] == "passed"
    assert scale["summary"]["largest_batch_size"] == 256
    assert round(scale["summary"]["peak_environment_steps_per_second"]) == 35166
    assert round(scale["summary"]["largest_batch_speedup_vs_single_env"], 2) == 228.16
    assert scale["summary"]["total_measured_environment_steps"] == 337000
    assert futures["protocol"]["parallel_environment_count"] == 54
    assert sum(result["hard_safe"] for result in futures["results"]) == 32
    assert len(futures["results"]) - sum(result["hard_safe"] for result in futures["results"]) == 22
    assert formal["schema_version"] == 5
    assert formal["completed_episode_count"] == 30
    assert formal["summary"]["guardiansim"]["repeatable_safe_completion_count"] == 30
    return scale, futures, formal


def main() -> None:
    scale, futures, formal = validate_sources()
    hero_frames = load_video_frames(HERO_VIDEO)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    command = [
        ffmpeg,
        "-y",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{WIDTH}x{HEIGHT}",
        "-r",
        str(FPS),
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "19",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(OUTPUT),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    assert process.stdin is not None

    preview_frame: Image.Image | None = None
    for frame_index in range(DURATION_SECONDS * FPS):
        timestamp = frame_index / FPS
        if timestamp < 6:
            image = render_title(timestamp)
        elif timestamp < 24:
            image = render_scale(timestamp - 6)
        elif timestamp < 40:
            image = render_futures(timestamp - 24)
        elif timestamp < 58:
            image = render_replay(timestamp - 40, hero_frames)
        elif timestamp < 72:
            image = render_proof(timestamp - 58)
        else:
            image = render_close(timestamp - 72)
        if frame_index == 18 * FPS:
            preview_frame = image.copy()
        process.stdin.write(image.tobytes())

    process.stdin.close()
    return_code = process.wait()
    if return_code:
        raise RuntimeError(f"ffmpeg exited with {return_code}")
    if preview_frame is None:
        raise RuntimeError("Preview frame was not captured")
    preview_frame.save(PREVIEW)

    hard_safe = sum(result["hard_safe"] for result in futures["results"])
    payload = {
        "kind": "guardiansim_radeon_parallel_futures_visual_review_v3",
        "team": "Aegis Motion",
        "project": "GuardianSim",
        "review_status": "revised silent visual source; typography and copy review passed",
        "layout_policy": {
            "metric_rows": "measured as one group and centered inside each card",
            "titles_and_details": "measured and centered inside each card",
            "overflow_asserted_during_render": True,
        },
        "claim_boundary": (
            "Preserved Genesis simulation evidence only; no physics re-execution; "
            "throughput worlds are not independent safety scenes; no physical-robot claim."
        ),
        "output": {
            "path": str(OUTPUT.relative_to(ROOT)),
            "sha256": sha256(OUTPUT),
            "duration_seconds": DURATION_SECONDS,
            "fps": FPS,
            "width": WIDTH,
            "height": HEIGHT,
            "audio": False,
        },
        "sources": {
            "radeon_scale_report": {
                "path": str(SCALE_REPORT.relative_to(ROOT)),
                "sha256": sha256(SCALE_REPORT),
                "strict_validation": True,
            },
            "parallel_futures_report": {
                "path": str(FUTURES_REPORT.relative_to(ROOT)),
                "sha256": sha256(FUTURES_REPORT),
                "strict_validation": True,
            },
            "gate32_formal_report": {
                "path": str(FORMAL_REPORT.relative_to(ROOT)),
                "sha256": sha256(FORMAL_REPORT),
                "schema_version": formal["schema_version"],
                "completed_episode_count": formal["completed_episode_count"],
            },
            "seed411_replay": {
                "path": str(HERO_VIDEO.relative_to(ROOT)),
                "sha256": sha256(HERO_VIDEO),
            },
        },
        "verified_metrics": {
            "largest_parallel_batch": scale["summary"]["largest_batch_size"],
            "environment_steps_per_second": round(
                scale["summary"]["peak_environment_steps_per_second"]
            ),
            "speedup_vs_single_world": round(
                scale["summary"]["largest_batch_speedup_vs_single_env"], 2
            ),
            "total_measured_environment_steps": scale["summary"][
                "total_measured_environment_steps"
            ],
            "parallel_future_worlds": len(futures["results"]),
            "parallel_future_hard_safe": hard_safe,
            "parallel_future_rejected": len(futures["results"]) - hard_safe,
            "parallel_future_wall_seconds": futures["summary"][
                "batched_execution_wall_seconds"
            ],
            "formal_repeatable_safe_scenarios": {
                "baseline": formal["summary"]["baseline"][
                    "repeatable_safe_completion_count"
                ],
                "guardiansim": formal["summary"]["guardiansim"][
                    "repeatable_safe_completion_count"
                ],
                "total": formal["completed_episode_count"],
            },
        },
        "chapters": [
            {"start": 0, "end": 6, "name": "compute hook"},
            {"start": 6, "end": 24, "name": "Radeon scale"},
            {"start": 24, "end": 40, "name": "parallel futures funnel"},
            {"start": 40, "end": 58, "name": "formal Seed 411 replay"},
            {"start": 58, "end": 72, "name": "frozen 30-scenario result"},
            {"start": 72, "end": 80, "name": "what the demo shows"},
        ],
    }
    SIDECAR.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload["output"], indent=2))


if __name__ == "__main__":
    main()
