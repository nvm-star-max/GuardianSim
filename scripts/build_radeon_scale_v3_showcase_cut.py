#!/usr/bin/env python3
"""Build the 90-second Radeon Scale V3 GuardianSim visual review cut.

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
DURATION_SECONDS = 90

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
    / "docs/evidence/radeon-scale-v3-formal-2026-08-03/report.json"
)
SCALE_VALIDATION = (
    ROOT
    / "docs/evidence/radeon-scale-v3-formal-2026-08-03/validation.json"
)
FUTURES_REPORT = (
    ROOT
    / "docs/evidence/safety-swarm-v2-formal-2026-07-30/formal-report.json"
)
FUTURES_VALIDATION = (
    ROOT
    / "docs/evidence/safety-swarm-v2-formal-2026-07-30/formal-validation.json"
)
FORMAL_REPORT = ROOT / "docs/evidence/gate-3-2/formal-report.json"
HERO_VIDEO = ROOT / "docs/demo/gate-3-2-seed-411-aegis-showcase-v3.mp4"

OUTPUT = (
    ROOT
    / "docs/submission/GuardianSim-Radeon-Scale-V3-review-v2.mp4"
)
SIDECAR = (
    ROOT
    / "docs/submission/GuardianSim-Radeon-Scale-V3-review-v2.json"
)
PREVIEW = (
    ROOT
    / "docs/submission/GuardianSim-Radeon-Scale-V3-review-v2-preview.png"
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
    draw.text((72, 168), "THINK 16,384 WORLDS.", font=font(84, bold=True), fill=WHITE)
    draw.text((72, 288), "EXECUTE ONE.", font=font(92), fill=ACID)
    draw.text(
        (76, 425),
        "One full Franka manipulation scene in every parallel world.",
        font=font(32),
        fill=MUTED,
    )
    draw.text(
        (76, 470),
        "AMD Radeon runs the worlds; GuardianSim reduces them to one auditable move.",
        font=font(32),
        fill=MUTED,
    )
    rounded(draw, (76, 620, 610, 890), fill=ACID)
    label(draw, "P50 PHYSICS RATE", 112, 660, color=BG)
    draw.text((110, 710), "278,051", font=font(78, bold=True), fill=BG)
    draw.text((112, 805), "environment-steps/s", font=font(25), fill=BG)
    rounded(draw, (650, 620, 1210, 890), fill=PANEL_2, outline=CYAN)
    label(draw, "FORMAL WORKLOAD", 690, 660)
    draw.text((688, 710), "293.6M", font=font(82, bold=True), fill=WHITE)
    draw.text((690, 805), "measured environment steps", font=font(25), fill=MUTED)
    rounded(draw, (1250, 620, 1844, 890), fill=PANEL_2, outline=GREEN)
    label(draw, "SUITE GPU USE", 1290, 660, color=GREEN)
    draw.text((1288, 710), "98.33%", font=font(78, bold=True), fill=WHITE)
    draw.text((1290, 805), "weighted mean · 100% peak", font=font(25), fill=MUTED)
    return image


def render_scale(t: float) -> Image.Image:
    image = base_frame("02 / RADEON SCALE")
    draw = ImageDraw.Draw(image)
    draw.text((64, 100), "THROUGHPUT RISES TO 16,384 FULL WORLDS", font=font(52, bold=True), fill=WHITE)
    draw.text(
        (66, 172),
        "Three frozen batch sizes · five independent processes each · 15 formal measurements",
        font=font(25),
        fill=MUTED,
    )
    steps = [
        (4096, 152697, 1.00, 97.77, 6.25),
        (8192, 214944, 1.41, 97.98, 11.52),
        (16384, 278051, 1.82, 98.82, 22.05),
    ]
    stage = min(2, int(t / 6.0))
    chart = (90, 290, 1260, 850)
    x0, y0, x1, y1 = chart
    draw.line((x0, y1, x1, y1), fill=(48, 77, 88), width=3)
    draw.line((x0, y0, x0, y1), fill=(48, 77, 88), width=3)
    max_rate = 300000
    for tick in (0, 100000, 200000, 300000):
        y = y1 - int((tick / max_rate) * (y1 - y0))
        draw.line((x0, y, x1, y), fill=(20, 44, 54), width=2)
        draw.text((x0 - 16, y), f"{tick // 1000}k", anchor="rm", font=font(18, mono=True), fill=MUTED)
    slot = (x1 - x0) / len(steps)
    points: list[tuple[int, int]] = []
    for index, (worlds, throughput, ratio, gpu_use, vram_gib) in enumerate(steps):
        center = int(x0 + slot * (index + 0.5))
        top = y1 - int((throughput / max_rate) * (y1 - y0))
        active = index <= stage
        color = GREEN if index == stage else (CYAN if active else (29, 57, 66))
        fill = (19, 99, 76) if index == stage else ((8, 49, 63) if active else (8, 24, 31))
        draw.rounded_rectangle((center - 110, top, center + 110, y1), radius=14, fill=fill, outline=color, width=3)
        draw.text((center, y1 + 28), f"{worlds:,}", anchor="ma", font=font(18, bold=True, mono=True), fill=color)
        if active:
            draw.text((center, top - 18), f"{throughput:,}", anchor="ms", font=font(18, bold=True, mono=True), fill=color)
            points.append((center, top))
    if len(points) > 1:
        draw.line(points, fill=ACID, width=5, joint="curve")
    for point in points:
        draw.ellipse((point[0] - 6, point[1] - 6, point[0] + 6, point[1] + 6), fill=ACID)

    worlds, throughput, ratio, gpu_use, vram_gib = steps[stage]
    rounded(draw, (1330, 285, 1835, 525), fill=PANEL_2, outline=GREEN, width=3)
    label(draw, "CURRENT BATCH", 1370, 320, color=GREEN)
    draw.text((1370, 370), f"{worlds:,}", font=font(70, bold=True), fill=WHITE)
    draw.text((1372, 455), "parallel full scenes", font=font(24), fill=MUTED)
    rounded(draw, (1330, 555, 1835, 795), fill=PANEL_2, outline=CYAN, width=3)
    label(draw, "MEASURED RATE", 1370, 590)
    draw.text((1370, 640), f"{throughput:,}", font=font(58, bold=True), fill=WHITE)
    draw.text((1372, 712), "environment-steps/s", font=font(24), fill=MUTED)
    draw.text((1330, 835), f"{ratio:.2f}× P50 vs 4,096 · {gpu_use:.2f}% GPU", font=font(22, bold=True, mono=True), fill=ACID if stage == 2 else CYAN)
    draw.text((1330, 875), f"{vram_gib:.2f} GiB peak VRAM", font=font(22, bold=True, mono=True), fill=MUTED)
    draw.text(
        (90, 925),
        "LARGEST BATCH: P95 278,660 · RANGE 274,990–278,672 · 100% PEAK GPU",
        font=font(25, bold=True, mono=True),
        fill=GREEN if stage == 2 else MUTED,
    )
    return image


def render_futures(t: float) -> Image.Image:
    image = base_frame("03 / SAFETY SWARM")
    draw = ImageDraw.Draw(image)
    draw.text((64, 100), "4,608 FUTURES BECOME ONE AUDITABLE MOVE", font=font(52, bold=True), fill=WHITE)
    draw.text(
        (66, 170),
        "18 bounded actions × 256 frozen uncertainty worlds · hard gates before ranking",
        font=font(27),
        fill=MUTED,
    )
    x0, y0 = 80, 310
    columns = 6
    cell_w = 150
    cell_h = 150
    gap = 18
    reveal = min(18, max(1, int(t * 2.5)))
    classified = t >= 4.0
    qualifying = {4, 6, 8, 10, 12}
    for index in range(18):
        row, column = divmod(index, columns)
        left = x0 + column * (cell_w + gap)
        top = y0 + row * (cell_h + gap)
        if index >= reveal:
            fill, outline = (7, 18, 25), (24, 46, 55)
        elif not classified:
            fill, outline = (5, 40, 53), CYAN
        elif index in qualifying:
            fill, outline = (18, 77, 58), GREEN
        else:
            fill, outline = (53, 28, 28), RED
        rounded(draw, (left, top, left + cell_w, top + cell_h), fill=fill, outline=outline, radius=10)
        draw.text(
            (left + cell_w // 2, top + 50),
            f"A{index + 1:02d}",
            anchor="ma",
            font=font(25, bold=True, mono=True),
            fill=outline,
        )
        status = "256/256" if index in qualifying else "REJECT"
        draw.text(
            (left + cell_w // 2, top + 100),
            status if classified and index < reveal else "256 worlds",
            anchor="ma",
            font=font(18, bold=True, mono=True),
            fill=outline,
        )
    draw.text((1125, 305), "FROZEN FUNNEL", font=font(24, bold=True, mono=True), fill=CYAN)
    funnel = [
        ("4,608", "candidate-world pairs", CYAN, 1125, 380, 1815),
        ("5", "actions passed all 256 worlds", GREEN, 1210, 555, 1730),
        ("1", "selected by frozen ranking", ACID, 1295, 730, 1645),
    ]
    for value, detail, color, left, top, right in funnel:
        rounded(draw, (left, top, right, top + 135), fill=PANEL_2, outline=color, width=3, radius=14)
        draw.text((left + 28, top + 20), value, font=font(55, bold=True), fill=color)
        draw.text((left + 155, top + 53), detail, font=font(24, bold=True), fill=WHITE)
    draw.text((1128, 910), "2.30M physics steps · 73.4% mean / 97% peak GPU", font=font(25, bold=True, mono=True), fill=CYAN)
    draw.text((1128, 952), "Candidate-world pairs are engineering outcomes, not robot trials.", font=font(21), fill=MUTED)
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
        ("INDEPENDENT SAFE EXECUTIONS", "58/90", "90/90", "Three Genesis simulations per scenario."),
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
    draw.text((90, 210), "THINK THOUSANDS.", font=font(104, bold=True), fill=WHITE)
    draw.text((96, 345), "EXECUTE ONE.", font=font(104, bold=True), fill=ACID)
    rounded(draw, (96, 500, 1820, 750), fill=PANEL_2, outline=CYAN)
    draw.text(
        (140, 548),
        "RADEON RUNS THE WORLDS  →  GUARDIANSIM REDUCES THEM  →  ROBOT MOVES OR STOPS",
        font=fit_font(
            draw,
            "RADEON RUNS THE WORLDS  →  GUARDIANSIM REDUCES THEM  →  ROBOT MOVES OR STOPS",
            max_width=1636,
            max_size=42,
            min_size=30,
            bold=True,
        ),
        fill=WHITE,
    )
    draw.text(
        (140, 630),
        "16,384 worlds · 278,051 env-steps/s P50 · 293.6M-step frozen workload · 100% peak GPU",
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


def render_simulation_finale(t: float, frames: list[Image.Image]) -> Image.Image:
    """End on the preserved Seed 411 motion instead of a static title card."""
    # The preserved replay is 17.55 seconds long. Its actual side-by-side robot
    # motion occupies 05.00--12.30; the surrounding frames are explanatory
    # cards. Stretch only that motion window across the ten-second finale.
    progress = min(0.999, max(0.0, t / 10.0))
    motion_start = min(round(5.0 * FPS), len(frames) - 1)
    motion_end = min(round(12.3 * FPS), len(frames) - 1)
    index = min(
        motion_start + int(progress * (motion_end - motion_start)),
        motion_end,
    )
    image = frames[index].resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(image)

    # Cover the replay's own title block completely; leaving only part of it
    # visible reads as accidental clipping beneath our finale label.
    draw.rectangle((0, 0, WIDTH, 168), fill=BG)
    label(draw, "FINAL SIMULATION RESULT  ·  FORMAL SEED 411", 50, 28)

    draw.rectangle((0, HEIGHT - 112, WIDTH, HEIGHT), fill=BG)
    draw.text((70, HEIGHT - 78), "LEFT  ·  NOMINAL CONTACT", font=font(24, bold=True), fill=RED)
    draw.text((520, HEIGHT - 78), "1.42 mm overlap", font=font(24), fill=WHITE)
    draw.text((875, HEIGHT - 78), "→", font=font(30, bold=True), fill=CYAN)
    draw.text((975, HEIGHT - 78), "RIGHT  ·  GUARDIANSIM", font=font(24, bold=True), fill=GREEN)
    draw.text((1370, HEIGHT - 78), "17.1 mm clearance · 3/3 safe", font=font(24), fill=WHITE)
    draw.text(
        (70, HEIGHT - 35),
        "Same task · same initial state · preserved Genesis replay · no physical-robot claim",
        font=font(18, mono=True),
        fill=MUTED,
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
    assert scale["schema_version"] == 3
    assert scale["summary"]["measurement_count"] == 15
    assert scale["summary"]["largest_parallel_batch"] == 16384
    assert round(scale["summary"]["largest_batch_throughput_p50"]) == 278051
    assert round(scale["summary"]["largest_batch_throughput_p95"]) == 278660
    assert round(scale["summary"]["largest_vs_smallest_batch_p50_ratio"], 2) == 1.82
    assert scale["summary"]["total_measured_environment_steps"] == 293601280
    assert round(scale["summary"]["mean_gpu_utilization_pct"], 2) == 98.33
    assert scale["summary"]["peak_gpu_utilization_pct"] == 100.0
    assert len(scale["measurements"]) == 15
    assert futures["summary"]["candidate_count"] == 18
    assert futures["summary"]["world_count_per_candidate"] == 256
    assert futures["summary"]["candidate_world_count"] == 4608
    assert len(futures["summary"]["qualifying_candidate_ids"]) == 5
    assert futures["summary"]["decision"] == "execute"
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
        elif timestamp < 80:
            image = render_close(timestamp - 72)
        else:
            image = render_simulation_finale(timestamp - 80, hero_frames)
        if frame_index == 85 * FPS:
            preview_frame = image.copy()
        process.stdin.write(image.tobytes())

    process.stdin.close()
    return_code = process.wait()
    if return_code:
        raise RuntimeError(f"ffmpeg exited with {return_code}")
    if preview_frame is None:
        raise RuntimeError("Preview frame was not captured")
    preview_frame.save(PREVIEW)

    payload = {
        "kind": "guardiansim_radeon_scale_v3_visual_review_v2",
        "team": "Aegis Motion",
        "project": "GuardianSim",
        "review_status": "Scale V3 silent visual candidate with Seed 411 simulation finale",
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
            "safety_swarm_v2_report": {
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
                "finale_motion_window_seconds": [5.0, 12.3],
            },
        },
        "verified_metrics": {
            "measurement_count": scale["summary"]["measurement_count"],
            "largest_parallel_batch": scale["summary"]["largest_parallel_batch"],
            "largest_batch_throughput_p50": round(scale["summary"]["largest_batch_throughput_p50"]),
            "largest_batch_throughput_p95": round(scale["summary"]["largest_batch_throughput_p95"]),
            "largest_batch_throughput_min": round(scale["summary"]["largest_batch_throughput_min"]),
            "largest_batch_throughput_max": round(scale["summary"]["largest_batch_throughput_max"]),
            "largest_vs_smallest_batch_p50_ratio": round(scale["summary"]["largest_vs_smallest_batch_p50_ratio"], 2),
            "total_measured_environment_steps": scale["summary"][
                "total_measured_environment_steps"
            ],
            "mean_gpu_utilization_pct": round(scale["summary"]["mean_gpu_utilization_pct"], 2),
            "peak_gpu_utilization_pct": scale["summary"]["peak_gpu_utilization_pct"],
            "peak_vram_used_bytes": scale["summary"]["peak_vram_used_bytes"],
            "safety_swarm_candidate_world_pairs": futures["summary"][
                "candidate_world_count"
            ],
            "safety_swarm_qualifying_actions": len(
                futures["summary"]["qualifying_candidate_ids"]
            ),
            "safety_swarm_selected_actions": 1,
            "safety_swarm_environment_steps": futures["summary"][
                "total_environment_steps"
            ],
            "safety_swarm_wall_seconds": futures["summary"][
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
            {"start": 24, "end": 40, "name": "Safety Swarm funnel"},
            {"start": 40, "end": 58, "name": "formal Seed 411 replay"},
            {"start": 58, "end": 72, "name": "frozen 30-scenario result"},
            {"start": 72, "end": 80, "name": "what the demo shows"},
            {"start": 80, "end": 90, "name": "final Seed 411 simulation replay"},
        ],
    }
    SIDECAR.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload["output"], indent=2))


if __name__ == "__main__":
    main()
