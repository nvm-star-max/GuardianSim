#!/usr/bin/env python3
"""Small, dependency-free Qwen3-TTS client for GuardianSim narration.

Secrets are read from ``DASHSCOPE_API_KEY`` or the ignored ``.env.local``
file.  The key is never written to logs or output metadata.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
import wave
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
DEFAULT_MODEL = "qwen3-tts-instruct-flash-2026-01-26"
DEFAULT_VOICE = "Ethan"
DEFAULT_INSTRUCTIONS = (
    "Speak like a calm, confident robotics engineer explaining a breakthrough "
    "to judges. Warm and human, with conversational pacing, short natural "
    "pauses, and subtle emphasis. Avoid announcer voice and exaggerated drama."
)


@dataclass(frozen=True)
class SynthesisResult:
    output: Path
    chunks: int
    characters: int
    model: str
    voice: str


def load_api_key(env_path: Path = ROOT / ".env.local") -> str:
    """Return the API key without logging it."""

    if value := os.environ.get("DASHSCOPE_API_KEY"):
        return value.strip()
    if env_path.exists():
        for raw_line in env_path.read_text().splitlines():
            line = raw_line.strip()
            if line.startswith("DASHSCOPE_API_KEY="):
                value = line.split("=", 1)[1].strip()
                if value:
                    return value
    raise RuntimeError("DASHSCOPE_API_KEY is not configured. Export it or add it to the Git-ignored .env.local file.")


def split_text(text: str, *, limit: int = 520) -> list[str]:
    """Split narration at sentence boundaries below the API character limit."""

    text = " ".join(text.split())
    if not text:
        return []
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > limit:
            words = sentence.split()
            piece = ""
            for word in words:
                candidate = f"{piece} {word}".strip()
                if piece and len(candidate) > limit:
                    chunks.append(piece)
                    piece = word
                else:
                    piece = candidate
            if current:
                chunks.append(current)
                current = ""
            if piece:
                chunks.append(piece)
            continue
        candidate = f"{current} {sentence}".strip()
        if current and len(candidate) > limit:
            chunks.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        chunks.append(current)
    if any(len(chunk) > limit for chunk in chunks):
        raise ValueError("Could not split narration below the Qwen TTS limit")
    return chunks


def _post_json(url: str, payload: dict, *, api_key: str) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        try:
            parsed = json.loads(detail)
            message = parsed.get("message") or parsed.get("code") or detail
        except json.JSONDecodeError:
            message = detail
        raise RuntimeError(f"Qwen TTS request failed ({exc.code}): {message}") from exc


def synthesize_chunk(
    text: str,
    output: Path,
    *,
    api_key: str,
    model: str = DEFAULT_MODEL,
    voice: str = DEFAULT_VOICE,
    instructions: str = DEFAULT_INSTRUCTIONS,
    endpoint: str = DEFAULT_ENDPOINT,
) -> None:
    payload = {
        "model": model,
        "input": {
            "text": text,
            "voice": voice,
            "language_type": "English",
            "instructions": instructions,
            "optimize_instructions": True,
        },
    }
    response = _post_json(endpoint, payload, api_key=api_key)
    audio_url = response.get("output", {}).get("audio", {}).get("url")
    if not audio_url:
        message = response.get("message") or response.get("code") or "missing audio URL"
        raise RuntimeError(f"Qwen TTS returned no audio: {message}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(audio_url, timeout=120) as audio_response:
        output.write_bytes(audio_response.read())


def concatenate_wavs(
    inputs: list[Path],
    output: Path,
    *,
    silence_seconds: float = 0.12,
) -> None:
    if not inputs:
        raise ValueError("No WAV inputs to concatenate")
    output.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(inputs[0]), "rb") as first:
        params = first.getparams()
        frames = [first.readframes(first.getnframes())]
    silence_frames = round(params.framerate * silence_seconds)
    silence = b"\x00" * silence_frames * params.nchannels * params.sampwidth
    for path in inputs[1:]:
        with wave.open(str(path), "rb") as handle:
            current = handle.getparams()
            current_format = (
                current.nchannels,
                current.sampwidth,
                current.framerate,
                current.comptype,
            )
            expected_format = (
                params.nchannels,
                params.sampwidth,
                params.framerate,
                params.comptype,
            )
            if current_format != expected_format:
                raise ValueError(f"Incompatible WAV format in {path}")
            frames.extend([silence, handle.readframes(handle.getnframes())])
    with wave.open(str(output), "wb") as combined:
        combined.setparams(params)
        for frame_block in frames:
            combined.writeframes(frame_block)


def synthesize_text(
    text: str,
    output: Path,
    *,
    cache_dir: Path,
    model: str = DEFAULT_MODEL,
    voice: str = DEFAULT_VOICE,
    instructions: str = DEFAULT_INSTRUCTIONS,
) -> SynthesisResult:
    api_key = load_api_key()
    chunks = split_text(text)
    if not chunks:
        raise ValueError("Narration is empty")
    chunk_paths: list[Path] = []
    for index, chunk in enumerate(chunks):
        identity = hashlib.sha256(
            json.dumps(
                {
                    "text": chunk,
                    "model": model,
                    "voice": voice,
                    "instructions": instructions,
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()[:16]
        chunk_path = cache_dir / f"{output.stem}-chunk-{index:02d}-{identity}.wav"
        if not chunk_path.exists():
            synthesize_chunk(
                chunk,
                chunk_path,
                api_key=api_key,
                model=model,
                voice=voice,
                instructions=instructions,
            )
        chunk_paths.append(chunk_path)
    if len(chunk_paths) == 1:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(chunk_paths[0].read_bytes())
    else:
        concatenate_wavs(chunk_paths, output)
    return SynthesisResult(
        output=output,
        chunks=len(chunks),
        characters=len(text),
        model=model,
        voice=voice,
    )
