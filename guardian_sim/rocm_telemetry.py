"""Small, dependency-free ROCm SMI sampler shared by Radeon benchmarks."""

from __future__ import annotations

import json
import re
import subprocess
import threading
from collections.abc import Mapping


def _number(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"-?\d+(?:\.\d+)?", value)
        if match:
            return float(match.group())
    return None


def _flatten_mapping(value: object) -> list[tuple[str, object]]:
    flattened: list[tuple[str, object]] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            flattened.append((str(key), item))
            flattened.extend(_flatten_mapping(item))
    elif isinstance(value, list):
        for item in value:
            flattened.extend(_flatten_mapping(item))
    return flattened


def parse_rocm_smi_sample(stdout: str) -> dict[str, float] | None:
    """Parse the fields used across current and older rocm-smi JSON formats."""

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    fields = _flatten_mapping(payload)

    def find(*needles: str) -> float | None:
        for key, value in fields:
            normalized = key.lower()
            if all(needle in normalized for needle in needles):
                parsed = _number(value)
                if parsed is not None:
                    return parsed
        return None

    utilization = find("gpu", "use")
    used_vram = find("vram", "used")
    total_vram = find("vram", "total")
    if utilization is None and used_vram is None and total_vram is None:
        return None
    return {
        key: value
        for key, value in {
            "gpu_utilization_pct": utilization,
            "vram_used_bytes": used_vram,
            "vram_total_bytes": total_vram,
        }.items()
        if value is not None
    }


class RocmSmiSampler:
    """Poll lightweight ROCm telemetry during a timed GPU workload."""

    def __init__(self, interval_seconds: float = 0.25) -> None:
        self.interval_seconds = interval_seconds
        self.samples: list[dict[str, float]] = []
        self.raw_errors: list[str] = []
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _sample_once(self) -> None:
        try:
            result = subprocess.run(
                [
                    "rocm-smi",
                    "--showuse",
                    "--showmeminfo",
                    "vram",
                    "--json",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as error:
            self.raw_errors.append(repr(error))
            return
        parsed = parse_rocm_smi_sample(result.stdout)
        if parsed:
            self.samples.append(parsed)
        elif result.stderr:
            self.raw_errors.append(result.stderr.strip()[-500:])

    def _run(self) -> None:
        while not self._stop.is_set():
            self._sample_once()
            self._stop.wait(self.interval_seconds)

    def start(self) -> None:
        self._sample_once()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> dict[str, object]:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=10)
        self._sample_once()
        utilizations = [
            sample["gpu_utilization_pct"]
            for sample in self.samples
            if "gpu_utilization_pct" in sample
        ]
        used_vram = [
            sample["vram_used_bytes"]
            for sample in self.samples
            if "vram_used_bytes" in sample
        ]
        total_vram = [
            sample["vram_total_bytes"]
            for sample in self.samples
            if "vram_total_bytes" in sample
        ]
        return {
            "sample_count": len(self.samples),
            "mean_gpu_utilization_pct": (
                sum(utilizations) / len(utilizations) if utilizations else None
            ),
            "max_gpu_utilization_pct": max(utilizations) if utilizations else None,
            "max_vram_used_bytes": max(used_vram) if used_vram else None,
            "total_vram_bytes": max(total_vram) if total_vram else None,
            "sampling_errors": self.raw_errors[:5],
        }
