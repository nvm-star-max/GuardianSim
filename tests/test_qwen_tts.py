from pathlib import Path

from scripts.qwen_tts import concatenate_wavs, split_text


def test_split_text_preserves_narration_and_limits_chunks() -> None:
    text = (
        "GuardianSim checks an action before execution. "
        "It restores the same scene snapshot for every candidate. "
        "If no action is safe, it stops."
    )
    chunks = split_text(text, limit=70)
    assert all(len(chunk) <= 70 for chunk in chunks)
    assert " ".join(chunks) == text


def test_split_text_handles_single_long_sentence() -> None:
    text = " ".join(["counterfactual"] * 30) + "."
    chunks = split_text(text, limit=80)
    assert len(chunks) > 1
    assert all(len(chunk) <= 80 for chunk in chunks)
    assert " ".join(chunks) == text


def test_concatenate_wavs_adds_short_silence(tmp_path: Path) -> None:
    import wave

    inputs = []
    for index in range(2):
        path = tmp_path / f"{index}.wav"
        with wave.open(str(path), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(24_000)
            handle.writeframes(b"\x01\x00" * 2_400)
        inputs.append(path)

    output = tmp_path / "combined.wav"
    concatenate_wavs(inputs, output, silence_seconds=0.1)

    with wave.open(str(output), "rb") as handle:
        assert handle.getnchannels() == 1
        assert handle.getframerate() == 24_000
        assert handle.getnframes() == 2_400 + 2_400 + 2_400
