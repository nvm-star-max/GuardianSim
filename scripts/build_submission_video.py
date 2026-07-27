#!/usr/bin/env python3
"""Build the narrated GuardianSim hackathon submission review video.

The video is a presentation artifact assembled from preserved, validated
evidence. It does not re-run Genesis and it does not add a benchmark trial.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
WIDTH = 1920
HEIGHT = 1080
FPS = 20

BG = (9, 14, 24)
PANEL = (19, 28, 43)
PANEL_2 = (26, 37, 55)
WHITE = (241, 246, 252)
MUTED = (156, 171, 190)
BLUE = (68, 161, 255)
CYAN = (61, 218, 220)
GREEN = (98, 220, 143)
ORANGE = (255, 153, 75)
RED = (255, 92, 92)
YELLOW = (250, 208, 90)

FONT_REGULAR = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
FONT_BOLD = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")
FONT_MONO = Path("/System/Library/Fonts/Supplemental/Courier New.ttf")

HERO_PATH = ROOT / "docs/demo/gate-3-2-seed-411-aegis-showcase-v3.mp4"
HERO_SIDECAR = ROOT / "docs/demo/gate-3-2-seed-411-aegis-showcase-v3.json"
HERO_VALIDATION = (
    ROOT / "docs/demo/gate-3-2-seed-411-aegis-showcase-v3-validation.json"
)
FORMAL_REPORT = ROOT / "docs/evidence/gate-3-2/formal-report.json"
FORMAL_ENVIRONMENT = ROOT / "docs/evidence/gate-3-2/formal-environment.txt"
SMOKE_WORLD = (
    ROOT / "docs/evidence/evaluator-smoke-58a76d4/raw/genesis-probe/world.png"
)
SMOKE_WRIST = (
    ROOT / "docs/evidence/evaluator-smoke-58a76d4/raw/genesis-probe/wrist.png"
)
SMOKE_CANDIDATES = (
    ROOT / "docs/evidence/evaluator-smoke-58a76d4/raw/candidates.json"
)
GATE33_REPORT = (
    ROOT / "docs/evidence/gate-3-3-two-strata/raw/two-strata-report.json"
)

OUTPUT = ROOT / "docs/submission/GuardianSim-Aegis-Motion-demo-review-v1.mp4"
SIDECAR = ROOT / "docs/submission/GuardianSim-Aegis-Motion-demo-review-v1.json"
PREVIEW = ROOT / "docs/submission/GuardianSim-Aegis-Motion-demo-review-v1-preview.png"


@dataclass(frozen=True)
class Segment:
    slug: str
    title: str
    kicker: str
    narration: str
    renderer: Callable[[float, float], Image.Image]


def font(size: int, *, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_MONO if mono else (FONT_BOLD if bold else FONT_REGULAR)
    return ImageFont.truetype(str(path), size=size)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rgb(color: tuple[int, int, int]) -> tuple[int, int, int]:
    return color


def rounded(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    fill: tuple[int, int, int],
    outline: tuple[int, int, int] | None = None,
    width: int = 2,
    radius: int = 24,
) -> None:
    draw.rounded_rectangle(
        box,
        radius=radius,
        fill=rgb(fill),
        outline=rgb(outline) if outline else None,
        width=width,
    )


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=fnt)[2] <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    *,
    fnt: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    width: int,
    spacing: int = 10,
    max_lines: int | None = None,
) -> int:
    lines = wrap(draw, text, fnt, width)
    if max_lines:
        lines = lines[:max_lines]
    y = xy[1]
    line_height = fnt.size + spacing
    for line in lines:
        draw.text((xy[0], y), line, font=fnt, fill=rgb(fill))
        y += line_height
    return y


def base_frame(title: str, kicker: str, *, accent: tuple[int, int, int] = BLUE) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), rgb(BG))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, WIDTH, 10), fill=rgb(accent))
    draw.text((72, 48), "AEGIS MOTION  /  GUARDIANSIM", font=font(24, bold=True), fill=rgb(accent))
    draw.text((72, 96), title, font=font(54, bold=True), fill=rgb(WHITE))
    draw.text((74, 164), kicker, font=font(25), fill=rgb(MUTED))
    draw.text(
        (72, HEIGHT - 52),
        "Genesis simulation · Preserved evidence · No physical-robot claim",
        font=font(20),
        fill=rgb(MUTED),
    )
    return image


def current_sentence(text: str, t: float, duration: float) -> str:
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text.strip())
        if sentence.strip()
    ]
    if not sentences:
        return ""
    weights = [max(1, len(sentence.split())) for sentence in sentences]
    target = min(max(t / max(duration, 0.001), 0.0), 0.9999) * sum(weights)
    cursor = 0
    for sentence, weight in zip(sentences, weights, strict=True):
        cursor += weight
        if target < cursor:
            return sentence
    return sentences[-1]


def subtitle(image: Image.Image, text: str, *, position: str = "bottom") -> None:
    draw = ImageDraw.Draw(image)
    if position == "top":
        box = (180, 92, 1740, 234)
        y = 118
    else:
        box = (180, 888, 1740, 1030)
        y = 914
    rounded(draw, box, fill=(5, 9, 16), outline=(54, 68, 87), radius=22)
    lines = wrap(draw, text, font(29, bold=True), 1450)
    if len(lines) > 2:
        y -= 17
    for line in lines[:3]:
        bbox = draw.textbbox((0, 0), line, font=font(29, bold=True))
        x = (WIDTH - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, font=font(29, bold=True), fill=rgb(WHITE))
        y += 40


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


def contain(source: Image.Image, box: tuple[int, int, int, int], *, fill: tuple[int, int, int] = PANEL) -> Image.Image:
    x0, y0, x1, y1 = box
    canvas = Image.new("RGB", (x1 - x0, y1 - y0), rgb(fill))
    copy = source.copy()
    copy.thumbnail(canvas.size, Image.Resampling.LANCZOS)
    x = (canvas.width - copy.width) // 2
    y = (canvas.height - copy.height) // 2
    canvas.paste(copy, (x, y))
    return canvas


FORMAL = json.loads(FORMAL_REPORT.read_text())
GATE33 = json.loads(GATE33_REPORT.read_text())
SMOKE = json.loads(SMOKE_CANDIDATES.read_text())
HERO_META = json.loads(HERO_SIDECAR.read_text())
HERO_CHECK = json.loads(HERO_VALIDATION.read_text())

assert FORMAL["schema_version"] == 5
assert FORMAL["completed_episode_count"] == 30
assert FORMAL["summary"]["baseline"]["repeatable_safe_completion_count"] == 18
assert FORMAL["summary"]["guardiansim"]["repeatable_safe_completion_count"] == 30
assert FORMAL["summary"]["baseline"]["execution_safe_completion_count"] == 58
assert FORMAL["summary"]["guardiansim"]["execution_safe_completion_count"] == 90
assert FORMAL["summary"]["baseline"]["clutter_contact_count"] == 30
assert FORMAL["summary"]["guardiansim"]["clutter_contact_count"] == 0
assert GATE33["schema_version"] == 6
assert GATE33["completed_episode_count"] == 12
assert GATE33["summary"]["guardiansim"]["safe_stop_count"] == 2
assert SMOKE["candidate_count"] == 3
assert HERO_CHECK["validated"] is True

HERO_FRAMES = load_video_frames(HERO_PATH)
WORLD_IMAGE = Image.open(SMOKE_WORLD).convert("RGB")
WRIST_IMAGE = Image.open(SMOKE_WRIST).convert("RGB")


def hero_frame(t: float, duration: float, *, label: str) -> Image.Image:
    progress = min(max(t / max(duration, 0.001), 0.0), 0.9999)
    index = min(int(progress * len(HERO_FRAMES)), len(HERO_FRAMES) - 1)
    image = HERO_FRAMES[index].resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, WIDTH, 80), fill=(5, 9, 16))
    draw.text((52, 22), label, font=font(29, bold=True), fill=rgb(WHITE))
    draw.text((1480, 25), "FORMAL SEED 411", font=font(22, bold=True), fill=rgb(CYAN))
    return image


def render_hook(t: float, duration: float) -> Image.Image:
    image = hero_frame(t, duration, label="SAME TASK · SAME INITIAL STATE")
    draw = ImageDraw.Draw(image)
    if t < duration * 0.25:
        rounded(draw, (250, 160, 1670, 360), fill=(7, 12, 21), outline=BLUE, width=3)
        draw.text((322, 194), "A ROBOT CAN SUCCEED", font=font(56, bold=True), fill=rgb(WHITE))
        draw.text((410, 270), "AND STILL BE UNSAFE.", font=font(56, bold=True), fill=rgb(ORANGE))
    return image


def render_environment(t: float, duration: float) -> Image.Image:
    image = base_frame(
        "Real AMD Radeon execution path",
        "Archived evaluator evidence from Radeon Cloud · commit 58a76d4",
        accent=CYAN,
    )
    draw = ImageDraw.Draw(image)
    rounded(draw, (72, 224, 1050, 830), fill=(7, 12, 19), outline=(46, 75, 92))
    draw.text((110, 258), "$ rocm-smi && python scripts/evaluator_preflight.py", font=font(24, mono=True), fill=rgb(CYAN))
    lines = [
        "GPU[0]  AMD Radeon Graphics  ·  gfx1100",
        "ROCm/HIP  7.2.53211-e1a6bc5663",
        "PyTorch   2.9.1+gitff65f5b",
        "Genesis   1.2.3  ·  backend: gs.amdgpu",
        "Python    3.12.3",
        "gpu_count: 1",
        "gpu_ready: true",
    ]
    visible = max(1, min(len(lines), int((t / duration) * (len(lines) + 2))))
    for i, line in enumerate(lines[:visible]):
        color = GREEN if "true" in line else WHITE
        draw.text((116, 330 + i * 58), line, font=font(28, mono=True), fill=rgb(color))
    rounded(draw, (1100, 224, 1848, 830), fill=PANEL, outline=(46, 75, 92))
    probe = WORLD_IMAGE if t < duration * 0.55 else WRIST_IMAGE
    label = "WORLD PROBE · real Genesis scene" if t < duration * 0.55 else "WRIST PROBE · real Genesis camera"
    panel = contain(probe, (1125, 272, 1823, 748), fill=(8, 13, 21))
    image.paste(panel, (1125, 272))
    draw.text((1136, 770), label, font=font(22, bold=True), fill=rgb(CYAN))
    return image


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: tuple[int, int, int]) -> None:
    draw.line((start, end), fill=rgb(color), width=6)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    size = 16
    for delta in (2.55, -2.55):
        point = (
            int(end[0] + size * math.cos(angle + delta)),
            int(end[1] + size * math.sin(angle + delta)),
        )
        draw.line((end, point), fill=rgb(color), width=6)


def render_architecture(t: float, duration: float) -> Image.Image:
    image = base_frame(
        "Counterfactual safety before execution",
        "Hard eligibility first · utility ranking second · explicit stop when no action is safe",
        accent=BLUE,
    )
    draw = ImageDraw.Draw(image)
    boxes = [
        ((70, 340, 340, 520), "1", "Nominal action", "Policy proposes"),
        ((390, 340, 660, 520), "2", "Candidates", "Yaw · retreat · approach"),
        ((710, 340, 980, 520), "3", "Same snapshot", "Fingerprint restored"),
        ((1030, 340, 1300, 520), "4", "Radeon rollouts", "Genesis · gs.amdgpu"),
        ((1350, 340, 1620, 520), "5", "Hard gates", "Reach · stability · clearance"),
        ((1650, 340, 1880, 520), "6", "Execute", "Safest eligible"),
    ]
    active = max(1, min(len(boxes), int((t / duration) * (len(boxes) + 2))))
    for i, (box, number, title, detail) in enumerate(boxes):
        color = BLUE if i < active else (57, 70, 88)
        rounded(draw, box, fill=PANEL if i < active else (16, 23, 35), outline=color, width=3)
        draw.text((box[0] + 20, box[1] + 18), number, font=font(22, bold=True), fill=rgb(color))
        draw.text((box[0] + 20, box[1] + 62), title, font=font(25, bold=True), fill=rgb(WHITE if i < active else MUTED))
        draw_wrapped(
            draw,
            detail,
            (box[0] + 20, box[1] + 106),
            fnt=font(19),
            fill=MUTED,
            width=box[2] - box[0] - 40,
            spacing=4,
        )
        if i and i < active:
            arrow(draw, (boxes[i - 1][0][2] + 8, 430), (box[0] - 8, 430), CYAN)
    rounded(draw, (1030, 625, 1455, 790), fill=(24, 38, 42), outline=GREEN, width=3)
    draw.text((1060, 658), "ELIGIBLE", font=font(24, bold=True), fill=rgb(GREEN))
    draw.text((1060, 705), "Repeatability confirmation", font=font(23, bold=True), fill=rgb(WHITE))
    arrow(draw, (1480, 705), (1710, 705), GREEN)
    rounded(draw, (1535, 625, 1880, 790), fill=(46, 25, 29), outline=RED, width=3)
    draw.text((1565, 658), "NO ELIGIBLE ACTION", font=font(22, bold=True), fill=rgb(RED))
    draw.text((1565, 708), "SAFE STOP", font=font(34, bold=True), fill=rgb(WHITE))
    arrow(draw, (1480, 475), (1480, 610), RED)
    return image


def render_smoke(t: float, duration: float) -> Image.Image:
    image = base_frame(
        "One-command evaluator smoke",
        "Execution-path proof only · not the source of performance metrics",
        accent=YELLOW,
    )
    draw = ImageDraw.Draw(image)
    rounded(draw, (72, 225, 1195, 835), fill=(5, 10, 17), outline=(79, 77, 51))
    transcript = [
        "$ ./scripts/run_evaluator_smoke.sh",
        "[source] commit 58a76d4 · dirty: false",
        "[preflight] gpu_ready: true",
        "[tests] 54/54 passed",
        "[report] Gate 3.2 schema-5: 30/30 valid",
        "[genesis] world probe: passed",
        "[genesis] wrist probe: passed",
        "[rollout] candidate_count: 3",
        "[snapshot] 8a3692e8...2ee2",
        "[validator] validated: true",
    ]
    visible = max(1, min(len(transcript), int((t / duration) * (len(transcript) + 3))))
    for i, line in enumerate(transcript[:visible]):
        if "true" in line or "passed" in line or "validated" in line:
            color = GREEN
        elif line.startswith("$"):
            color = CYAN
        else:
            color = WHITE
        draw.text((108, 268 + i * 50), line, font=font(24, mono=True), fill=rgb(color))
    rounded(draw, (1235, 225, 1848, 835), fill=PANEL, outline=(79, 77, 51))
    top = contain(WORLD_IMAGE, (1260, 265, 1823, 518), fill=(8, 13, 21))
    bottom = contain(WRIST_IMAGE, (1260, 550, 1823, 803), fill=(8, 13, 21))
    image.paste(top, (1260, 265))
    image.paste(bottom, (1260, 550))
    draw.text((1280, 486), "WORLD PROBE", font=font(18, bold=True), fill=rgb(YELLOW))
    draw.text((1280, 771), "WRIST PROBE", font=font(18, bold=True), fill=rgb(YELLOW))
    return image


def render_physical(t: float, duration: float) -> Image.Image:
    image = hero_frame(t, duration, label="FORMAL PHYSICAL REPLAY · VALIDATED PRESENTATION")
    draw = ImageDraw.Draw(image)
    if t > duration * 0.76:
        rounded(draw, (520, 150, 1400, 315), fill=(5, 10, 17), outline=GREEN, width=3)
        draw.text((575, 180), "SAME FROZEN SCENARIO · 3 INDEPENDENT EXECUTIONS", font=font(24, bold=True), fill=rgb(CYAN))
        draw.text((595, 232), "BASELINE 0/3 SAFE   →   GUARDIANSIM 3/3 SAFE", font=font(35, bold=True), fill=rgb(WHITE))
    return image


def bar(
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    label: str,
    baseline: float,
    guardian: float,
    scale: float,
    baseline_text: str,
    guardian_text: str,
) -> None:
    draw.text((120, y), label, font=font(27, bold=True), fill=rgb(WHITE))
    x0 = 570
    max_width = 970
    draw.rounded_rectangle((x0, y + 3, x0 + max_width, y + 42), radius=18, fill=(38, 45, 58))
    draw.rounded_rectangle(
        (x0, y + 3, x0 + int(max_width * baseline / scale), y + 42),
        radius=18,
        fill=rgb(ORANGE),
    )
    draw.text((1570, y), baseline_text, font=font(26, bold=True), fill=rgb(ORANGE))
    draw.rounded_rectangle((x0, y + 56, x0 + max_width, y + 95), radius=18, fill=(38, 45, 58))
    draw.rounded_rectangle(
        (x0, y + 56, x0 + int(max_width * guardian / scale), y + 95),
        radius=18,
        fill=rgb(GREEN),
    )
    draw.text((1570, y + 53), guardian_text, font=font(26, bold=True), fill=rgb(GREEN))


def render_results(t: float, duration: float) -> Image.Image:
    image = base_frame(
        "Frozen Gate 3.2 formal result",
        "30 scenarios · 3 independent executions per strategy and scenario · strict schema-5",
        accent=GREEN,
    )
    draw = ImageDraw.Draw(image)
    bar(
        draw,
        y=260,
        label="Repeatable safe scenarios",
        baseline=18,
        guardian=30,
        scale=30,
        baseline_text="18 / 30",
        guardian_text="30 / 30",
    )
    bar(
        draw,
        y=405,
        label="Independent safe executions",
        baseline=58,
        guardian=90,
        scale=90,
        baseline_text="58 / 90",
        guardian_text="90 / 90",
    )
    bar(
        draw,
        y=550,
        label="Mean sampled clearance",
        baseline=23.191,
        guardian=46.003,
        scale=50,
        baseline_text="23.191 mm",
        guardian_text="46.003 mm",
    )
    rounded(draw, (115, 720, 870, 825), fill=(47, 25, 27), outline=RED)
    draw.text((155, 746), "CLUTTER CONTACT EXECUTIONS", font=font(22, bold=True), fill=rgb(MUTED))
    draw.text((650, 738), "30 → 0", font=font(40, bold=True), fill=rgb(WHITE))
    rounded(draw, (920, 720, 1800, 825), fill=(22, 43, 37), outline=GREEN)
    draw.text((960, 746), "MEAN CLEARANCE INCREASE", font=font(22, bold=True), fill=rgb(MUTED))
    draw.text((1570, 738), "+98.36%", font=font(40, bold=True), fill=rgb(GREEN))
    return image


def render_safe_stop(t: float, duration: float) -> Image.Image:
    image = base_frame(
        "Honest boundary: stop when coverage is insufficient",
        "Gate 3.3 engineering breadth evidence · not the formal performance benchmark",
        accent=RED,
    )
    draw = ImageDraw.Draw(image)
    rounded(draw, (80, 235, 1080, 835), fill=PANEL, outline=(78, 50, 57))
    center = (575, 530)
    draw.ellipse((center[0] - 58, center[1] - 58, center[0] + 58, center[1] + 58), fill=rgb(YELLOW))
    draw.text((520, 602), "TARGET", font=font(22, bold=True), fill=rgb(YELLOW))
    obstacles = [(355, 430), (785, 430), (355, 650), (785, 650)]
    for x, y in obstacles:
        draw.rounded_rectangle((x - 58, y - 58, x + 58, y + 58), radius=24, fill=rgb(RED))
    angles = [-70, -35, 0, 35, 70]
    reveal = max(1, min(len(angles), int((t / duration) * (len(angles) + 2))))
    for angle in angles[:reveal]:
        rad = math.radians(angle - 90)
        end = (int(center[0] + 245 * math.cos(rad)), int(center[1] + 245 * math.sin(rad)))
        draw.line((center, end), fill=rgb(ORANGE), width=8)
        cross_x, cross_y = end
        draw.line((cross_x - 16, cross_y - 16, cross_x + 16, cross_y + 16), fill=rgb(RED), width=8)
        draw.line((cross_x - 16, cross_y + 16, cross_x + 16, cross_y - 16), fill=rgb(RED), width=8)
    draw.text((260, 755), "Illustration of bounded candidate coverage", font=font(22), fill=rgb(MUTED))
    rounded(draw, (1140, 235, 1840, 835), fill=(43, 24, 29), outline=RED, width=3)
    draw.text((1200, 285), "NO HARD-SAFE ACTION", font=font(30, bold=True), fill=rgb(RED))
    draw.text((1260, 370), "SAFE STOP", font=font(62, bold=True), fill=rgb(WHITE))
    draw.text((1205, 490), "Gap / bearing stratum", font=font(27, bold=True), fill=rgb(MUTED))
    draw.text((1205, 545), "4 safe executions", font=font(31, bold=True), fill=rgb(GREEN))
    draw.text((1205, 595), "2 explicit safe stops", font=font(31, bold=True), fill=rgb(RED))
    draw.text((1205, 645), "0 unsafe executions", font=font(31, bold=True), fill=rgb(GREEN))
    draw_wrapped(
        draw,
        "Current limitation: the bounded action family cannot resolve every geometry.",
        (1205, 710),
        fnt=font(23),
        fill=MUTED,
        width=560,
        spacing=6,
    )
    return image


def render_close(t: float, duration: float) -> Image.Image:
    image = base_frame(
        "GuardianSim",
        "Counterfactual action safety on AMD Radeon GPUs",
        accent=CYAN,
    )
    draw = ImageDraw.Draw(image)
    repo = "https://github.com/nvm-star-max/GuardianSim"
    qr = cv2.QRCodeEncoder_create().encode(repo)
    qr_image = Image.fromarray(qr).convert("RGB").resize((340, 340), Image.Resampling.NEAREST)
    image.paste(qr_image, (1290, 300))
    rounded(draw, (115, 280, 1175, 690), fill=PANEL, outline=CYAN, width=3)
    draw.text((170, 335), "OPEN SOURCE · REPRODUCIBLE EVIDENCE", font=font(31, bold=True), fill=rgb(CYAN))
    draw.text((170, 420), repo, font=font(30, mono=True), fill=rgb(WHITE))
    draw.text((170, 510), "$ ./scripts/run_evaluator_smoke.sh", font=font(27, mono=True), fill=rgb(GREEN))
    draw.text((170, 565), "$ python scripts/validate_gate32_report.py ...", font=font(25, mono=True), fill=rgb(GREEN))
    draw.text((170, 635), "Source · frozen reports · validators · checksums", font=font(25, bold=True), fill=rgb(MUTED))
    draw.text((1305, 670), "SCAN FOR REPOSITORY", font=font(22, bold=True), fill=rgb(CYAN))
    rounded(draw, (375, 760, 1545, 850), fill=(18, 39, 36), outline=GREEN)
    draw.text((520, 785), "EXECUTE SAFELY · OR STOP EXPLICITLY", font=font(36, bold=True), fill=rgb(GREEN))
    return image


SEGMENTS: list[Segment] = [
    Segment(
        slug="hook",
        title="Success is not the same as safety",
        kicker="Formal Gate 3.2 replay",
        narration=(
            "A robot can complete a grasp and still take an unsafe path through clutter. "
            "In the same frozen Genesis scene, the nominal action contacts a neighboring "
            "object. GuardianSim evaluates counterfactual actions before execution, "
            "selects a safer eligible action, or refuses to move."
        ),
        renderer=render_hook,
    ),
    Segment(
        slug="amd-proof",
        title="AMD Radeon execution proof",
        kicker="Archived evaluator evidence",
        narration=(
            "GuardianSim is a Physical AI safety layer for Franka fruit picking in Genesis. "
            "The preserved evaluator run used one AMD Radeon GPU with the gfx eleven hundred "
            "architecture, ROCm and HIP seven point two, PyTorch two point nine, and Genesis "
            "one point two point three. The physical counterfactual rollouts executed through "
            "the Genesis A M D GPU backend. These terminal values and camera probes are "
            "archived with checksums in the repository."
        ),
        renderer=render_environment,
    ),
    Segment(
        slug="architecture",
        title="How GuardianSim works",
        kicker="Counterfactual certification",
        narration=(
            "The robot policy first proposes a nominal grasp. GuardianSim generates a bounded "
            "set of yaw, obstacle-retreat, and approach alternatives. Every candidate begins "
            "from the same fingerprinted scene snapshot. Radeon GPU rollouts then measure "
            "reachability, retained-lift stability, sampled path length, uncertainty, and "
            "clearance from non-target clutter. Hard safety gates determine eligibility before "
            "utility ranking. The selected candidate is confirmed across repeated rollouts and "
            "then executed independently. If no candidate passes every frozen gate, GuardianSim "
            "does not silently return to an unsafe nominal action. It produces an explicit safe stop."
        ),
        renderer=render_architecture,
    ),
    Segment(
        slug="smoke",
        title="Reproducibility workflow",
        kicker="Bounded real-Genesis smoke",
        narration=(
            "A new evaluator can run one documented smoke command from a clean checkout. "
            "The command verifies source identity and Radeon readiness, runs the unit tests, "
            "strictly validates the preserved thirty-scenario report, builds the real Franka "
            "scene, records world and wrist probes, restores one fingerprinted snapshot, and "
            "evaluates three bounded counterfactual candidates. The resulting candidate report "
            "also passes strict validation. This smoke proves that the documented execution path "
            "works. It is deliberately small and is not used as the source of the performance claim."
        ),
        renderer=render_smoke,
    ),
    Segment(
        slug="physical-proof",
        title="The physical difference",
        kicker="Validated Seed 411 replay",
        narration=(
            "Now consider formal Seed four hundred and eleven. The baseline uses a zero-degree "
            "fixed approach and overlaps the neighboring clutter object by one point four two "
            "millimeters in the accepted visual replay. GuardianSim rejects that nominal geometry "
            "and selects a plus sixty-seven point five degree orientation with a raised approach. "
            "The accepted replay measures seventeen point one millimeters of clearance. In the "
            "formal report, the baseline is unsafe in all three independent executions for this "
            "scenario, while GuardianSim is safe in all three. The candidate identity, decision "
            "reason, report hash, and video hash are bound by a strict presentation validator."
        ),
        renderer=render_physical,
    ),
    Segment(
        slug="formal-results",
        title="Formal Gate 3.2 evidence",
        kicker="Frozen schema-5 benchmark",
        narration=(
            "The primary benchmark contains thirty frozen scenarios and three independent physical "
            "executions per strategy and scenario. Repeatable safe completion improves from eighteen "
            "of thirty for the baseline to thirty of thirty for GuardianSim. Independent safe "
            "executions improve from fifty-eight of ninety to ninety of ninety. Sampled clutter "
            "contacts decrease from thirty to zero. Mean sampled clearance increases from twenty-three "
            "point one nine one millimeters to forty-six point zero zero three millimeters, an increase "
            "of ninety-eight point three six percent. These are Genesis simulation measurements, not "
            "claims about a physical robot."
        ),
        renderer=render_results,
    ),
    Segment(
        slug="safe-stop",
        title="Limitation and safe stop",
        kicker="Separate Gate 3.3 engineering evidence",
        narration=(
            "GuardianSim does not guarantee completion for arbitrary geometry. A separate twelve-case "
            "engineering breadth run tested pose shifts and harder obstacle gaps and bearings. In the "
            "six gap-and-bearing cases, four GuardianSim actions executed safely. In two lateral lemon "
            "and plum scenes, no candidate in the frozen action family passed every hard gate, so the "
            "system stopped before physical execution. There were zero unsafe GuardianSim executions "
            "in that stratum. The two safe stops are intended fail-safe behavior, but they also expose "
            "a real limitation: the current bounded action space needs broader geometric coverage. "
            "This engineering result is shown separately and is not mixed into the formal benchmark."
        ),
        renderer=render_safe_stop,
    ),
    Segment(
        slug="close",
        title="Open evidence, inspectable decisions",
        kicker="Aegis Motion · GuardianSim",
        narration=(
            "GuardianSim turns a policy-proposed manipulation action into an explainable, "
            "uncertainty-aware execute-or-stop decision on an AMD Radeon GPU. The source code, "
            "reproduction command, frozen reports, validators, and checksums are available in the "
            "public repository. GuardianSim is evaluated in Genesis simulation and has not yet been "
            "validated on a physical robot."
        ),
        renderer=render_close,
    ),
]


def audio_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        return handle.getnframes() / handle.getframerate()


def make_narration(directory: Path) -> tuple[list[Path], list[float]]:
    paths: list[Path] = []
    durations: list[float] = []
    for index, segment in enumerate(SEGMENTS):
        path = directory / f"{index:02d}-{segment.slug}.wav"
        subprocess.run(
            [
                "/usr/bin/say",
                "-v",
                "Samantha",
                "-r",
                "165",
                "-o",
                str(path),
                "--file-format=WAVE",
                "--data-format=LEI16@22050",
                segment.narration,
            ],
            check=True,
        )
        paths.append(path)
        durations.append(audio_duration(path))
    return paths, durations


def render_silent_video(path: Path, durations: list[float]) -> list[int]:
    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        FPS,
        (WIDTH, HEIGHT),
    )
    if not writer.isOpened():
        raise RuntimeError("Could not open the MP4 writer")
    frame_counts: list[int] = []
    for segment, duration in zip(SEGMENTS, durations, strict=True):
        count = max(1, round(duration * FPS))
        frame_counts.append(count)
        for frame_index in range(count):
            t = frame_index / FPS
            image = segment.renderer(t, duration)
            subtitle_position = "bottom"
            if segment.slug == "physical-proof":
                subtitle_position = "top"
            elif segment.slug == "hook" and t >= duration * 0.25:
                subtitle_position = "top"
            subtitle(
                image,
                current_sentence(segment.narration, t, duration),
                position=subtitle_position,
            )
            writer.write(cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR))
    writer.release()
    return frame_counts


def mux(silent_video: Path, audio_paths: list[Path], output: Path) -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    command = [ffmpeg, "-y", "-i", str(silent_video)]
    for path in audio_paths:
        command.extend(["-i", str(path)])
    audio_inputs = "".join(f"[{index}:a]" for index in range(1, len(audio_paths) + 1))
    filter_complex = f"{audio_inputs}concat=n={len(audio_paths)}:v=0:a=1[a]"
    command.extend(
        [
            "-filter_complex",
            filter_complex,
            "-map",
            "0:v:0",
            "-map",
            "[a]",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-movflags",
            "+faststart",
            "-shortest",
            str(output),
        ]
    )
    subprocess.run(command, check=True)


def write_preview(video: Path, output: Path) -> None:
    capture = cv2.VideoCapture(str(video))
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    samples = []
    for fraction in (0.03, 0.18, 0.34, 0.50, 0.67, 0.83, 0.97):
        capture.set(cv2.CAP_PROP_POS_FRAMES, int(frame_count * fraction))
        ok, frame = capture.read()
        if not ok:
            raise RuntimeError(f"Could not decode preview frame at {fraction}")
        thumb = cv2.resize(frame, (480, 270), interpolation=cv2.INTER_AREA)
        samples.append(thumb)
    capture.release()
    rows = [
        np.concatenate(samples[:4], axis=1),
        np.concatenate(samples[4:] + [np.zeros_like(samples[0])], axis=1),
    ]
    sheet = np.concatenate(rows, axis=0)
    cv2.imwrite(str(output), sheet)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="guardiansim-submission-video-") as temp:
        temp_dir = Path(temp)
        audio_paths, durations = make_narration(temp_dir)
        silent_video = temp_dir / "silent.mp4"
        frame_counts = render_silent_video(silent_video, durations)
        mux(silent_video, audio_paths, OUTPUT)

    write_preview(OUTPUT, PREVIEW)
    capture = cv2.VideoCapture(str(OUTPUT))
    output_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    output_fps = float(capture.get(cv2.CAP_PROP_FPS))
    output_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    output_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    capture.release()

    payload = {
        "kind": "guardiansim_submission_video_review_v1",
        "team": "Aegis Motion",
        "project": "GuardianSim",
        "claim_boundary": (
            "Presentation assembled from preserved evidence; no Genesis physics "
            "re-execution and no added benchmark trial. Simulation only."
        ),
        "language": "English",
        "narration": {
            "voice": "macOS Samantha",
            "rate_words_per_minute": 165,
            "human_narration_recommended_for_final": True,
            "segments": [
                {
                    "slug": segment.slug,
                    "title": segment.title,
                    "text": segment.narration,
                    "duration_seconds": duration,
                    "frame_count": frame_count,
                }
                for segment, duration, frame_count in zip(
                    SEGMENTS, durations, frame_counts, strict=True
                )
            ],
        },
        "output": {
            "path": str(OUTPUT.relative_to(ROOT)),
            "sha256": sha256(OUTPUT),
            "duration_seconds": output_frames / output_fps,
            "fps": output_fps,
            "frame_count": output_frames,
            "width": output_width,
            "height": output_height,
        },
        "sources": {
            "hero_video": {
                "path": str(HERO_PATH.relative_to(ROOT)),
                "sha256": sha256(HERO_PATH),
                "validated": HERO_CHECK["validated"],
            },
            "hero_sidecar_sha256": sha256(HERO_SIDECAR),
            "gate32_formal_report": {
                "path": str(FORMAL_REPORT.relative_to(ROOT)),
                "sha256": sha256(FORMAL_REPORT),
                "completed_episode_count": FORMAL["completed_episode_count"],
                "schema_version": FORMAL["schema_version"],
            },
            "gate33_engineering_report": {
                "path": str(GATE33_REPORT.relative_to(ROOT)),
                "sha256": sha256(GATE33_REPORT),
                "completed_episode_count": GATE33["completed_episode_count"],
                "schema_version": GATE33["schema_version"],
            },
            "smoke_candidates": {
                "path": str(SMOKE_CANDIDATES.relative_to(ROOT)),
                "sha256": sha256(SMOKE_CANDIDATES),
                "candidate_count": SMOKE["candidate_count"],
            },
            "environment_sha256": sha256(FORMAL_ENVIRONMENT),
            "world_probe_sha256": sha256(SMOKE_WORLD),
            "wrist_probe_sha256": sha256(SMOKE_WRIST),
        },
        "verified_metrics": {
            "gate32_repeatable_safe_completion": {"baseline": 18, "guardiansim": 30, "total": 30},
            "gate32_independent_safe_executions": {"baseline": 58, "guardiansim": 90, "total": 90},
            "gate32_clutter_contact_executions": {"baseline": 30, "guardiansim": 0},
            "gate32_mean_clearance_mm": {"baseline": 23.191, "guardiansim": 46.003},
            "gate32_clearance_increase_percent": 98.36,
            "seed411_replay": {
                "baseline_overlap_mm": 1.419067,
                "guardiansim_clearance_mm": 17.094284,
                "formal_baseline_safe": 0,
                "formal_guardiansim_safe": 3,
                "formal_execution_total": 3,
            },
            "gate33_gap_bearing": {
                "safe_executions": 4,
                "safe_stops": 2,
                "unsafe_executions": 0,
                "scenario_total": 6,
                "label": "engineering breadth evidence",
            },
        },
    }
    SIDECAR.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload["output"], indent=2))


if __name__ == "__main__":
    main()
