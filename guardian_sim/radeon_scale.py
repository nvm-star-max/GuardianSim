"""Protocol and validation helpers for the Radeon physics scaling benchmark."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path

RADEON_SCALE_SCHEMA_VERSION = 1
RADEON_SCALE_BENCHMARK_NAME = "radeon-parallel-physics-scaling"
RADEON_SCALE_DEFAULT_BATCH_SIZES = (1, 16, 64, 256)
RADEON_SCALE_DEFAULT_WARMUP_STEPS = 100
RADEON_SCALE_DEFAULT_MEASUREMENT_STEPS = 1000
RADEON_SCALE_SIMULATION_DT_S = 0.01


def sha256_file(path: Path) -> str:
    """Return a streaming SHA-256 digest for an evidence source file."""

    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_scale_protocol(
    *,
    batch_sizes: Sequence[int] = RADEON_SCALE_DEFAULT_BATCH_SIZES,
    warmup_steps: int = RADEON_SCALE_DEFAULT_WARMUP_STEPS,
    measurement_steps: int = RADEON_SCALE_DEFAULT_MEASUREMENT_STEPS,
    scene_source_sha256: str,
    scene_config_sha256: str,
) -> dict[str, object]:
    """Build the outcome-independent benchmark protocol and its canonical hash."""

    normalized_sizes = tuple(int(value) for value in batch_sizes)
    if not normalized_sizes or normalized_sizes[0] != 1:
        raise ValueError("batch sizes must start with the single-environment baseline")
    if any(value < 1 for value in normalized_sizes):
        raise ValueError("batch sizes must be positive")
    if len(set(normalized_sizes)) != len(normalized_sizes):
        raise ValueError("batch sizes must be unique")
    if tuple(sorted(normalized_sizes)) != normalized_sizes:
        raise ValueError("batch sizes must be strictly increasing")
    if warmup_steps < 1 or measurement_steps < 1:
        raise ValueError("warmup and measurement steps must be positive")
    for label, digest in (
        ("scene_source_sha256", scene_source_sha256),
        ("scene_config_sha256", scene_config_sha256),
    ):
        if len(digest) != 64:
            raise ValueError(f"{label} must be a SHA-256 digest")

    protocol: dict[str, object] = {
        "benchmark_name": RADEON_SCALE_BENCHMARK_NAME,
        "batch_sizes": list(normalized_sizes),
        "warmup_steps": warmup_steps,
        "measurement_steps": measurement_steps,
        "simulation_dt_s": RADEON_SCALE_SIMULATION_DT_S,
        "scene": "Franka + table + four active YCB entities; headless; cameras disabled",
        "scene_source_sha256": scene_source_sha256,
        "scene_config_sha256": scene_config_sha256,
        "timing_scope": (
            "steady-state control command plus Genesis scene.step after a separate warmup; "
            "scene build and JIT warmup are excluded"
        ),
        "primary_metric": "environment_steps_per_second",
    }
    canonical = json.dumps(protocol, sort_keys=True, separators=(",", ":"))
    protocol["protocol_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return protocol


def derive_trial_metrics(
    *,
    n_envs: int,
    measurement_steps: int,
    measurement_seconds: float,
    simulation_dt_s: float = RADEON_SCALE_SIMULATION_DT_S,
) -> dict[str, float | int]:
    """Calculate throughput metrics from one steady-state trial."""

    if n_envs < 1 or measurement_steps < 1 or measurement_seconds <= 0:
        raise ValueError("trial dimensions and measurement time must be positive")
    environment_steps = n_envs * measurement_steps
    environment_steps_per_second = environment_steps / measurement_seconds
    return {
        "environment_steps": environment_steps,
        "environment_steps_per_second": environment_steps_per_second,
        "simulated_seconds_per_wall_second": (
            environment_steps_per_second * simulation_dt_s
        ),
    }


def assemble_scale_report(
    protocol: Mapping[str, object],
    trials: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Add baseline-relative metrics and a concise summary to raw trials."""

    if not trials:
        raise ValueError("at least one trial is required")
    ordered = sorted((dict(trial) for trial in trials), key=lambda trial: int(trial["n_envs"]))
    baseline_throughput = float(ordered[0]["environment_steps_per_second"])
    if int(ordered[0]["n_envs"]) != 1 or baseline_throughput <= 0:
        raise ValueError("the first trial must be a positive single-environment baseline")

    for trial in ordered:
        n_envs = int(trial["n_envs"])
        speedup = float(trial["environment_steps_per_second"]) / baseline_throughput
        trial["speedup_vs_single_env"] = speedup
        trial["parallel_efficiency"] = speedup / n_envs

    largest = ordered[-1]
    peak_throughput = max(float(trial["environment_steps_per_second"]) for trial in ordered)
    payload: dict[str, object] = {
        "schema_version": RADEON_SCALE_SCHEMA_VERSION,
        "benchmark_name": RADEON_SCALE_BENCHMARK_NAME,
        "evidence_scope": (
            "Physics throughput only. This report does not increase the independent "
            "GuardianSim safety-evaluation sample count."
        ),
        "protocol": dict(protocol),
        "trials": ordered,
        "summary": {
            "largest_batch_size": int(largest["n_envs"]),
            "largest_batch_environment_steps_per_second": float(
                largest["environment_steps_per_second"]
            ),
            "largest_batch_speedup_vs_single_env": float(
                largest["speedup_vs_single_env"]
            ),
            "peak_environment_steps_per_second": peak_throughput,
            "total_measured_environment_steps": sum(
                int(trial["environment_steps"]) for trial in ordered
            ),
        },
    }
    validate_scale_report(payload, require_telemetry=False)
    return payload


def _require_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return value


def _require_close(actual: object, expected: float, label: str) -> None:
    if not isinstance(actual, (int, float)) or not math.isfinite(float(actual)):
        raise ValueError(f"{label} must be finite")
    if not math.isclose(float(actual), expected, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError(f"{label} does not match its source measurements")


def validate_scale_report(
    payload: Mapping[str, object],
    *,
    require_telemetry: bool = True,
) -> dict[str, object]:
    """Strictly validate protocol identity, AMD execution, and derived metrics."""

    if payload.get("schema_version") != RADEON_SCALE_SCHEMA_VERSION:
        raise ValueError("unsupported Radeon scaling schema")
    if payload.get("benchmark_name") != RADEON_SCALE_BENCHMARK_NAME:
        raise ValueError("unexpected benchmark name")

    protocol = _require_mapping(payload.get("protocol"), "protocol")
    protocol_without_hash = {
        key: value for key, value in protocol.items() if key != "protocol_sha256"
    }
    canonical = json.dumps(protocol_without_hash, sort_keys=True, separators=(",", ":"))
    expected_protocol_hash = hashlib.sha256(canonical.encode()).hexdigest()
    if protocol.get("protocol_sha256") != expected_protocol_hash:
        raise ValueError("protocol hash mismatch")

    raw_batch_sizes = protocol.get("batch_sizes")
    if not isinstance(raw_batch_sizes, list):
        raise TypeError("protocol.batch_sizes must be a list")
    expected_batch_sizes = [int(value) for value in raw_batch_sizes]
    trials = payload.get("trials")
    if not isinstance(trials, list):
        raise TypeError("trials must be a list")
    actual_batch_sizes = [int(_require_mapping(trial, "trial")["n_envs"]) for trial in trials]
    if actual_batch_sizes != expected_batch_sizes:
        raise ValueError("trial batch sizes do not match the frozen protocol order")

    measurement_steps = int(protocol["measurement_steps"])
    simulation_dt_s = float(protocol["simulation_dt_s"])
    baseline_throughput: float | None = None
    for index, raw_trial in enumerate(trials):
        trial = _require_mapping(raw_trial, f"trial {index}")
        n_envs = int(trial["n_envs"])
        if trial.get("status") != "passed":
            raise ValueError(f"trial {n_envs} did not pass")
        if trial.get("backend") != "genesis_gpu":
            raise ValueError(f"trial {n_envs} did not use the Genesis GPU backend")
        device = _require_mapping(trial.get("device"), f"trial {n_envs} device")
        if "amd" not in str(device.get("name", "")).lower():
            raise ValueError(f"trial {n_envs} does not identify an AMD GPU")
        if not str(device.get("hip_version", "")).strip():
            raise ValueError(f"trial {n_envs} is missing a HIP version")
        if trial.get("protocol_sha256") != protocol.get("protocol_sha256"):
            raise ValueError(f"trial {n_envs} protocol hash mismatch")

        derived = derive_trial_metrics(
            n_envs=n_envs,
            measurement_steps=measurement_steps,
            measurement_seconds=float(trial["measurement_seconds"]),
            simulation_dt_s=simulation_dt_s,
        )
        if int(trial["environment_steps"]) != int(derived["environment_steps"]):
            raise ValueError(f"trial {n_envs} environment-step count mismatch")
        throughput = float(derived["environment_steps_per_second"])
        _require_close(
            trial.get("environment_steps_per_second"),
            throughput,
            f"trial {n_envs} throughput",
        )
        _require_close(
            trial.get("simulated_seconds_per_wall_second"),
            float(derived["simulated_seconds_per_wall_second"]),
            f"trial {n_envs} real-time factor",
        )
        if baseline_throughput is None:
            baseline_throughput = throughput
        _require_close(
            trial.get("speedup_vs_single_env"),
            throughput / baseline_throughput,
            f"trial {n_envs} speedup",
        )
        _require_close(
            trial.get("parallel_efficiency"),
            throughput / baseline_throughput / n_envs,
            f"trial {n_envs} parallel efficiency",
        )

        telemetry = _require_mapping(
            trial.get("gpu_telemetry"),
            f"trial {n_envs} GPU telemetry",
        )
        sample_count = int(telemetry.get("sample_count", 0))
        if require_telemetry and sample_count < 1:
            raise ValueError(f"trial {n_envs} has no ROCm telemetry samples")
        for metric in (
            "mean_gpu_utilization_pct",
            "max_gpu_utilization_pct",
            "max_vram_used_bytes",
            "total_vram_bytes",
        ):
            value = telemetry.get(metric)
            if require_telemetry and value is None:
                raise ValueError(
                    f"trial {n_envs} telemetry {metric} is missing"
                )
            if value is not None and (
                not isinstance(value, (int, float)) or float(value) < 0
            ):
                raise ValueError(f"trial {n_envs} telemetry {metric} is invalid")

    summary = _require_mapping(payload.get("summary"), "summary")
    if trials:
        last = _require_mapping(trials[-1], "last trial")
        if int(summary.get("largest_batch_size", -1)) != int(last["n_envs"]):
            raise ValueError("summary largest batch mismatch")
    return {
        "status": "passed",
        "schema_version": RADEON_SCALE_SCHEMA_VERSION,
        "protocol_sha256": protocol["protocol_sha256"],
        "trial_count": len(trials),
        "largest_batch_size": summary["largest_batch_size"],
        "telemetry_required": require_telemetry,
    }
