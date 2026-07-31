"""Frozen protocol and strict validation for the Radeon Scale V2 benchmark."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence

from guardian_sim.radeon_scale import derive_trial_metrics

RADEON_SCALE_V2_SCHEMA_VERSION = 2
RADEON_SCALE_V2_BENCHMARK_NAME = "radeon-full-scene-concurrency-v2"
RADEON_SCALE_V2_BATCH_SIZES = (1, 16, 64, 256, 512, 1024, 2048, 4096)
RADEON_SCALE_V2_WARMUP_STEPS = 200
RADEON_SCALE_V2_MEASUREMENT_STEPS = 12_288
RADEON_SCALE_V2_LARGEST_BATCH_ENVIRONMENT_STEPS = 50_331_648
RADEON_SCALE_V2_TOTAL_ENVIRONMENT_STEPS = 98_512_896
RADEON_SCALE_V2_SIMULATION_DT_S = 0.01
RADEON_SCALE_V2_SCENE = (
    "Franka + table + four active YCB entities per world; headless; cameras disabled"
)
RADEON_SCALE_V2_SCOPE = (
    "Sustained Genesis physics-throughput benchmark. Environment steps are not "
    "training examples, independent safety trials, or physical-robot evidence."
)


def canonical_sha256(payload: Mapping[str, object]) -> str:
    """Hash a JSON object with deterministic serialization."""

    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _require_digest(value: str, label: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")


def build_scale_v2_protocol(
    *,
    scene_source_sha256: str,
    scene_config_sha256: str,
    trial_runner_sha256: str,
    batch_sizes: Sequence[int] = RADEON_SCALE_V2_BATCH_SIZES,
    warmup_steps: int = RADEON_SCALE_V2_WARMUP_STEPS,
    measurement_steps: int = RADEON_SCALE_V2_MEASUREMENT_STEPS,
) -> dict[str, object]:
    """Build the outcome-independent V2 protocol and canonical identity."""

    normalized_sizes = tuple(int(value) for value in batch_sizes)
    if not normalized_sizes or normalized_sizes[0] != 1:
        raise ValueError("batch sizes must start with the single-world baseline")
    if normalized_sizes != tuple(sorted(set(normalized_sizes))):
        raise ValueError("batch sizes must be unique and strictly increasing")
    if warmup_steps < 1 or measurement_steps < 1:
        raise ValueError("warmup and measurement steps must be positive")
    for label, digest in (
        ("scene_source_sha256", scene_source_sha256),
        ("scene_config_sha256", scene_config_sha256),
        ("trial_runner_sha256", trial_runner_sha256),
    ):
        _require_digest(digest, label)

    protocol: dict[str, object] = {
        "schema_version": RADEON_SCALE_V2_SCHEMA_VERSION,
        "benchmark_name": RADEON_SCALE_V2_BENCHMARK_NAME,
        "batch_sizes": list(normalized_sizes),
        "warmup_steps": int(warmup_steps),
        "measurement_steps": int(measurement_steps),
        "simulation_dt_s": RADEON_SCALE_V2_SIMULATION_DT_S,
        "scene": RADEON_SCALE_V2_SCENE,
        "scene_source_sha256": scene_source_sha256,
        "scene_config_sha256": scene_config_sha256,
        "trial_runner_sha256": trial_runner_sha256,
        "timing_scope": (
            "steady-state Franka position hold plus Genesis scene.step after a "
            "separate warmup; scene build, shader setup, and JIT warmup are excluded"
        ),
        "primary_metric": "environment_steps_per_second",
        "claim_boundary": RADEON_SCALE_V2_SCOPE,
    }
    protocol["protocol_sha256"] = canonical_sha256(protocol)
    return protocol


def validate_scale_v2_protocol(
    protocol: Mapping[str, object],
    *,
    require_frozen_formal: bool,
) -> dict[str, object]:
    """Validate canonical identity and, optionally, the exact formal workload."""

    if protocol.get("schema_version") != RADEON_SCALE_V2_SCHEMA_VERSION:
        raise ValueError("unsupported Radeon Scale V2 protocol schema")
    if protocol.get("benchmark_name") != RADEON_SCALE_V2_BENCHMARK_NAME:
        raise ValueError("unexpected Radeon Scale V2 benchmark name")
    without_hash = {
        key: value for key, value in protocol.items() if key != "protocol_sha256"
    }
    if protocol.get("protocol_sha256") != canonical_sha256(without_hash):
        raise ValueError("Radeon Scale V2 protocol hash mismatch")
    batch_sizes = protocol.get("batch_sizes")
    if not isinstance(batch_sizes, list):
        raise TypeError("protocol.batch_sizes must be a list")
    normalized_sizes = tuple(int(value) for value in batch_sizes)
    if not normalized_sizes or normalized_sizes[0] != 1:
        raise ValueError("protocol must start with the single-world baseline")
    if normalized_sizes != tuple(sorted(set(normalized_sizes))):
        raise ValueError("protocol batch sizes must be unique and increasing")
    if int(protocol.get("warmup_steps", 0)) < 1:
        raise ValueError("protocol warmup steps must be positive")
    if int(protocol.get("measurement_steps", 0)) < 1:
        raise ValueError("protocol measurement steps must be positive")
    if protocol.get("scene") != RADEON_SCALE_V2_SCENE:
        raise ValueError("protocol scene description mismatch")
    if protocol.get("claim_boundary") != RADEON_SCALE_V2_SCOPE:
        raise ValueError("protocol claim boundary mismatch")
    for label in (
        "scene_source_sha256",
        "scene_config_sha256",
        "trial_runner_sha256",
    ):
        _require_digest(str(protocol.get(label, "")), label)

    if require_frozen_formal:
        if normalized_sizes != RADEON_SCALE_V2_BATCH_SIZES:
            raise ValueError("formal batch sizes do not match the frozen protocol")
        if int(protocol["warmup_steps"]) != RADEON_SCALE_V2_WARMUP_STEPS:
            raise ValueError("formal warmup steps do not match the frozen protocol")
        if int(protocol["measurement_steps"]) != RADEON_SCALE_V2_MEASUREMENT_STEPS:
            raise ValueError("formal measurement steps do not match the frozen protocol")

    return {
        "status": "passed",
        "protocol_sha256": protocol["protocol_sha256"],
        "batch_sizes": list(normalized_sizes),
        "formal_protocol_required": require_frozen_formal,
    }


def _require_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return value


def _require_close(actual: object, expected: float, label: str) -> None:
    if not isinstance(actual, (int, float)) or not math.isfinite(float(actual)):
        raise ValueError(f"{label} must be finite")
    if not math.isclose(float(actual), expected, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError(f"{label} does not match source measurements")


def validate_scale_v2_trial(
    trial: Mapping[str, object],
    protocol: Mapping[str, object],
    *,
    require_telemetry: bool,
) -> dict[str, object]:
    """Validate one immutable raw trial against its protocol."""

    validate_scale_v2_protocol(protocol, require_frozen_formal=False)
    n_envs = int(trial.get("n_envs", 0))
    if n_envs not in [int(value) for value in protocol["batch_sizes"]]:
        raise ValueError("trial batch size is not declared by the protocol")
    if trial.get("status") != "passed":
        raise ValueError(f"trial {n_envs} did not pass")
    if trial.get("backend") != "genesis_gpu":
        raise ValueError(f"trial {n_envs} did not use the Genesis GPU backend")
    if trial.get("protocol_sha256") != protocol.get("protocol_sha256"):
        raise ValueError(f"trial {n_envs} protocol hash mismatch")

    device = _require_mapping(trial.get("device"), f"trial {n_envs} device")
    if "amd" not in str(device.get("name", "")).lower():
        raise ValueError(f"trial {n_envs} does not identify an AMD GPU")
    if not str(device.get("hip_version", "")).strip():
        raise ValueError(f"trial {n_envs} is missing a HIP version")

    derived = derive_trial_metrics(
        n_envs=n_envs,
        measurement_steps=int(protocol["measurement_steps"]),
        measurement_seconds=float(trial["measurement_seconds"]),
        simulation_dt_s=float(protocol["simulation_dt_s"]),
    )
    if int(trial.get("environment_steps", -1)) != int(derived["environment_steps"]):
        raise ValueError(f"trial {n_envs} environment-step count mismatch")
    _require_close(
        trial.get("environment_steps_per_second"),
        float(derived["environment_steps_per_second"]),
        f"trial {n_envs} throughput",
    )
    _require_close(
        trial.get("simulated_seconds_per_wall_second"),
        float(derived["simulated_seconds_per_wall_second"]),
        f"trial {n_envs} simulated-time rate",
    )

    telemetry = _require_mapping(
        trial.get("gpu_telemetry"),
        f"trial {n_envs} GPU telemetry",
    )
    if require_telemetry and int(telemetry.get("sample_count", 0)) < 1:
        raise ValueError(f"trial {n_envs} has no ROCm telemetry samples")
    for metric in (
        "mean_gpu_utilization_pct",
        "max_gpu_utilization_pct",
        "max_vram_used_bytes",
        "total_vram_bytes",
    ):
        value = telemetry.get(metric)
        if require_telemetry and value is None:
            raise ValueError(f"trial {n_envs} telemetry {metric} is missing")
        if value is not None and (
            not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) < 0
        ):
            raise ValueError(f"trial {n_envs} telemetry {metric} is invalid")

    return {
        "status": "passed",
        "n_envs": n_envs,
        "environment_steps": int(derived["environment_steps"]),
        "telemetry_required": require_telemetry,
    }


def assemble_scale_v2_report(
    protocol: Mapping[str, object],
    trials: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Assemble immutable raw trials and fully derived summary fields."""

    validate_scale_v2_protocol(protocol, require_frozen_formal=False)
    ordered = sorted(
        (dict(trial) for trial in trials),
        key=lambda trial: int(trial["n_envs"]),
    )
    expected_sizes = [int(value) for value in protocol["batch_sizes"]]
    if [int(trial["n_envs"]) for trial in ordered] != expected_sizes:
        raise ValueError("trial set does not match the protocol batch sizes")
    baseline = float(ordered[0]["environment_steps_per_second"])
    if baseline <= 0:
        raise ValueError("single-world baseline throughput must be positive")

    for trial in ordered:
        validate_scale_v2_trial(trial, protocol, require_telemetry=False)
        n_envs = int(trial["n_envs"])
        throughput = float(trial["environment_steps_per_second"])
        trial["speedup_vs_single_world"] = throughput / baseline
        trial["parallel_efficiency"] = throughput / baseline / n_envs

    largest = ordered[-1]
    report: dict[str, object] = {
        "schema_version": RADEON_SCALE_V2_SCHEMA_VERSION,
        "benchmark_name": RADEON_SCALE_V2_BENCHMARK_NAME,
        "evidence_scope": RADEON_SCALE_V2_SCOPE,
        "protocol": dict(protocol),
        "trials": ordered,
        "summary": {
            "trial_count": len(ordered),
            "largest_batch_size": int(largest["n_envs"]),
            "largest_batch_environment_steps": int(largest["environment_steps"]),
            "largest_batch_environment_steps_per_second": float(
                largest["environment_steps_per_second"]
            ),
            "largest_batch_speedup_vs_single_world": float(
                largest["speedup_vs_single_world"]
            ),
            "largest_batch_parallel_efficiency": float(
                largest["parallel_efficiency"]
            ),
            "peak_environment_steps_per_second": max(
                float(trial["environment_steps_per_second"]) for trial in ordered
            ),
            "total_measured_environment_steps": sum(
                int(trial["environment_steps"]) for trial in ordered
            ),
            "peak_gpu_utilization_pct": max(
                float(_require_mapping(trial["gpu_telemetry"], "telemetry").get(
                    "max_gpu_utilization_pct", 0
                ))
                for trial in ordered
            ),
            "peak_vram_used_bytes": max(
                float(_require_mapping(trial["gpu_telemetry"], "telemetry").get(
                    "max_vram_used_bytes", 0
                ))
                for trial in ordered
            ),
        },
    }
    report["report_sha256"] = canonical_sha256(report)
    return report


def validate_scale_v2_report(
    report: Mapping[str, object],
    *,
    require_telemetry: bool = True,
    require_frozen_formal: bool = True,
) -> dict[str, object]:
    """Strictly validate a complete report and every public derived metric."""

    if report.get("schema_version") != RADEON_SCALE_V2_SCHEMA_VERSION:
        raise ValueError("unsupported Radeon Scale V2 report schema")
    if report.get("benchmark_name") != RADEON_SCALE_V2_BENCHMARK_NAME:
        raise ValueError("unexpected Radeon Scale V2 report name")
    if report.get("evidence_scope") != RADEON_SCALE_V2_SCOPE:
        raise ValueError("Radeon Scale V2 evidence scope mismatch")
    protocol = _require_mapping(report.get("protocol"), "protocol")
    validate_scale_v2_protocol(
        protocol,
        require_frozen_formal=require_frozen_formal,
    )
    trials = report.get("trials")
    if not isinstance(trials, list):
        raise TypeError("trials must be a list")
    expected_sizes = [int(value) for value in protocol["batch_sizes"]]
    actual_sizes = [
        int(_require_mapping(trial, f"trial {index}")["n_envs"])
        for index, trial in enumerate(trials)
    ]
    if actual_sizes != expected_sizes:
        raise ValueError("trial order does not match the frozen protocol")

    baseline: float | None = None
    for index, raw_trial in enumerate(trials):
        trial = _require_mapping(raw_trial, f"trial {index}")
        validate_scale_v2_trial(
            trial,
            protocol,
            require_telemetry=require_telemetry,
        )
        throughput = float(trial["environment_steps_per_second"])
        if baseline is None:
            baseline = throughput
        n_envs = int(trial["n_envs"])
        _require_close(
            trial.get("speedup_vs_single_world"),
            throughput / baseline,
            f"trial {n_envs} speedup",
        )
        _require_close(
            trial.get("parallel_efficiency"),
            throughput / baseline / n_envs,
            f"trial {n_envs} parallel efficiency",
        )

    summary = _require_mapping(report.get("summary"), "summary")
    derived = assemble_scale_v2_report(protocol, trials)
    derived_summary = _require_mapping(derived["summary"], "derived summary")
    for key, expected in derived_summary.items():
        actual = summary.get(key)
        if isinstance(expected, float):
            _require_close(actual, expected, f"summary {key}")
        elif actual != expected:
            raise ValueError(f"summary {key} mismatch")

    without_hash = {
        key: value for key, value in report.items() if key != "report_sha256"
    }
    if report.get("report_sha256") != canonical_sha256(without_hash):
        raise ValueError("Radeon Scale V2 report hash mismatch")

    if require_frozen_formal:
        if int(summary["largest_batch_environment_steps"]) != (
            RADEON_SCALE_V2_LARGEST_BATCH_ENVIRONMENT_STEPS
        ):
            raise ValueError("formal largest-batch environment-step count mismatch")
        if int(summary["total_measured_environment_steps"]) != (
            RADEON_SCALE_V2_TOTAL_ENVIRONMENT_STEPS
        ):
            raise ValueError("formal total environment-step count mismatch")

    return {
        "status": "passed",
        "schema_version": RADEON_SCALE_V2_SCHEMA_VERSION,
        "protocol_sha256": protocol["protocol_sha256"],
        "report_sha256": report["report_sha256"],
        "trial_count": len(trials),
        "largest_batch_size": summary["largest_batch_size"],
        "largest_batch_environment_steps": summary[
            "largest_batch_environment_steps"
        ],
        "total_measured_environment_steps": summary[
            "total_measured_environment_steps"
        ],
        "telemetry_required": require_telemetry,
        "frozen_formal_required": require_frozen_formal,
    }
