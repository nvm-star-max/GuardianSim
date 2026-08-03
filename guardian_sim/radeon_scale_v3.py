"""Frozen high-scale endurance protocol for Radeon Scale V3."""

from __future__ import annotations

import math
import statistics
from collections.abc import Mapping, Sequence

from guardian_sim.radeon_scale_v2 import (
    build_scale_v2_protocol,
    canonical_sha256,
    validate_scale_v2_protocol,
    validate_scale_v2_trial,
)

RADEON_SCALE_V3_SCHEMA_VERSION = 3
RADEON_SCALE_V3_BENCHMARK_NAME = "radeon-full-scene-high-scale-endurance-v3"
RADEON_SCALE_V3_BATCH_SIZES = (4096, 8192, 16384)
RADEON_SCALE_V3_REPEATS_PER_BATCH = 5
RADEON_SCALE_V3_WARMUP_STEPS = 200
RADEON_SCALE_V3_MEASUREMENT_STEPS = 2048
RADEON_SCALE_V3_TOTAL_MEASUREMENTS = (
    len(RADEON_SCALE_V3_BATCH_SIZES) * RADEON_SCALE_V3_REPEATS_PER_BATCH
)
RADEON_SCALE_V3_TOTAL_ENVIRONMENT_STEPS = (
    sum(RADEON_SCALE_V3_BATCH_SIZES)
    * RADEON_SCALE_V3_REPEATS_PER_BATCH
    * RADEON_SCALE_V3_MEASUREMENT_STEPS
)
RADEON_SCALE_V3_SCOPE = (
    "Independent-process Genesis physics endurance measurements at 4,096, 8,192, "
    "and 16,384 complete robot worlds on one AMD Radeon GPU. Environment steps are "
    "not training samples, inference tokens, independent safety trials, or "
    "physical-robot evidence. Capacity preflight results are excluded."
)


def _require_digest(value: str, label: str) -> None:
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")


def build_scale_v3_protocol(
    *,
    scene_source_sha256: str,
    scene_config_sha256: str,
    trial_runner_sha256: str,
    suite_runner_sha256: str,
    batch_sizes: Sequence[int] = RADEON_SCALE_V3_BATCH_SIZES,
    repeats_per_batch: int = RADEON_SCALE_V3_REPEATS_PER_BATCH,
    warmup_steps: int = RADEON_SCALE_V3_WARMUP_STEPS,
    measurement_steps: int = RADEON_SCALE_V3_MEASUREMENT_STEPS,
) -> dict[str, object]:
    """Build the outcome-independent V3 protocol and its V2 trial contract."""

    normalized_sizes = tuple(int(value) for value in batch_sizes)
    if not normalized_sizes or normalized_sizes != tuple(sorted(set(normalized_sizes))):
        raise ValueError("batch sizes must be unique and strictly increasing")
    if repeats_per_batch < 2:
        raise ValueError("repeats_per_batch must be at least two")
    if warmup_steps < 1 or measurement_steps < 1:
        raise ValueError("warmup and measurement steps must be positive")
    for label, digest in (
        ("scene_source_sha256", scene_source_sha256),
        ("scene_config_sha256", scene_config_sha256),
        ("trial_runner_sha256", trial_runner_sha256),
        ("suite_runner_sha256", suite_runner_sha256),
    ):
        _require_digest(digest, label)

    # The reusable V2 validator requires a single-world baseline to be declared.
    # V3 never measures that compatibility entry: its measured batch list remains
    # the high-scale ``normalized_sizes`` sequence below.
    trial_batch_sizes = (
        normalized_sizes
        if normalized_sizes[0] == 1
        else (1, *normalized_sizes)
    )
    trial_protocol = build_scale_v2_protocol(
        scene_source_sha256=scene_source_sha256,
        scene_config_sha256=scene_config_sha256,
        trial_runner_sha256=trial_runner_sha256,
        batch_sizes=trial_batch_sizes,
        warmup_steps=warmup_steps,
        measurement_steps=measurement_steps,
    )
    protocol: dict[str, object] = {
        "schema_version": RADEON_SCALE_V3_SCHEMA_VERSION,
        "benchmark_name": RADEON_SCALE_V3_BENCHMARK_NAME,
        "batch_sizes": list(normalized_sizes),
        "repeats_per_batch": int(repeats_per_batch),
        "warmup_steps": int(warmup_steps),
        "measurement_steps_per_repeat": int(measurement_steps),
        "repeat_scope": "independent process and independently rebuilt scene",
        "percentile_method": "linear interpolation at rank (n - 1) * q",
        "primary_metric": "P50 environment steps per wall-clock second",
        "claim_boundary": RADEON_SCALE_V3_SCOPE,
        "suite_runner_sha256": suite_runner_sha256,
        "trial_protocol": trial_protocol,
    }
    protocol["protocol_sha256"] = canonical_sha256(protocol)
    return protocol


def validate_scale_v3_protocol(
    protocol: Mapping[str, object],
    *,
    require_frozen_formal: bool,
) -> dict[str, object]:
    """Validate the V3 identity and optionally require the exact frozen workload."""

    if protocol.get("schema_version") != RADEON_SCALE_V3_SCHEMA_VERSION:
        raise ValueError("unsupported Radeon Scale V3 protocol schema")
    if protocol.get("benchmark_name") != RADEON_SCALE_V3_BENCHMARK_NAME:
        raise ValueError("unexpected Radeon Scale V3 benchmark name")
    without_hash = {
        key: value for key, value in protocol.items() if key != "protocol_sha256"
    }
    if protocol.get("protocol_sha256") != canonical_sha256(without_hash):
        raise ValueError("Radeon Scale V3 protocol hash mismatch")
    batch_sizes = protocol.get("batch_sizes")
    if not isinstance(batch_sizes, list):
        raise TypeError("protocol.batch_sizes must be a list")
    normalized_sizes = tuple(int(value) for value in batch_sizes)
    if not normalized_sizes or normalized_sizes != tuple(sorted(set(normalized_sizes))):
        raise ValueError("protocol batch sizes must be unique and increasing")
    repeats = int(protocol.get("repeats_per_batch", 0))
    warmup = int(protocol.get("warmup_steps", 0))
    measurement = int(protocol.get("measurement_steps_per_repeat", 0))
    if repeats < 2 or warmup < 1 or measurement < 1:
        raise ValueError("invalid V3 repeat, warmup, or measurement count")
    if protocol.get("claim_boundary") != RADEON_SCALE_V3_SCOPE:
        raise ValueError("Radeon Scale V3 claim boundary mismatch")
    _require_digest(str(protocol.get("suite_runner_sha256", "")), "suite_runner_sha256")
    trial_protocol = protocol.get("trial_protocol")
    if not isinstance(trial_protocol, Mapping):
        raise TypeError("protocol.trial_protocol must be an object")
    validate_scale_v2_protocol(trial_protocol, require_frozen_formal=False)
    expected_trial_sizes = (
        list(normalized_sizes)
        if normalized_sizes[0] == 1
        else [1, *normalized_sizes]
    )
    if [int(value) for value in trial_protocol["batch_sizes"]] != expected_trial_sizes:
        raise ValueError("V3 measured batches differ from the trial-protocol contract")
    if int(trial_protocol["warmup_steps"]) != warmup:
        raise ValueError("V3 and trial-protocol warmup counts differ")
    if int(trial_protocol["measurement_steps"]) != measurement:
        raise ValueError("V3 and trial-protocol measurement counts differ")

    if require_frozen_formal:
        if normalized_sizes != RADEON_SCALE_V3_BATCH_SIZES:
            raise ValueError("formal V3 batch sizes do not match the frozen protocol")
        if repeats != RADEON_SCALE_V3_REPEATS_PER_BATCH:
            raise ValueError("formal V3 repeat count does not match the frozen protocol")
        if warmup != RADEON_SCALE_V3_WARMUP_STEPS:
            raise ValueError("formal V3 warmup does not match the frozen protocol")
        if measurement != RADEON_SCALE_V3_MEASUREMENT_STEPS:
            raise ValueError("formal V3 measurement count does not match the frozen protocol")

    return {
        "status": "passed",
        "protocol_sha256": protocol["protocol_sha256"],
        "batch_sizes": list(normalized_sizes),
        "repeats_per_batch": repeats,
        "formal_protocol_required": require_frozen_formal,
    }


def linear_percentile(values: Sequence[float], quantile: float) -> float:
    """Return a deterministic linearly interpolated percentile."""

    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise ValueError("percentile requires at least one value")
    if not 0 <= quantile <= 1:
        raise ValueError("quantile must be in [0, 1]")
    rank = (len(ordered) - 1) * quantile
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    fraction = rank - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _weighted_gpu_mean(measurements: Sequence[Mapping[str, object]]) -> float:
    weighted_total = 0.0
    sample_total = 0
    for measurement in measurements:
        trial = measurement["trial"]
        if not isinstance(trial, Mapping):
            raise TypeError("measurement.trial must be an object")
        telemetry = trial["gpu_telemetry"]
        if not isinstance(telemetry, Mapping):
            raise TypeError("trial.gpu_telemetry must be an object")
        samples = int(telemetry["sample_count"])
        weighted_total += float(telemetry["mean_gpu_utilization_pct"]) * samples
        sample_total += samples
    if sample_total < 1:
        raise ValueError("GPU telemetry has no samples")
    return weighted_total / sample_total


def _batch_summary(
    n_envs: int,
    measurements: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    throughputs = [
        float(measurement["trial"]["environment_steps_per_second"])
        for measurement in measurements
    ]
    mean = statistics.fmean(throughputs)
    coefficient_of_variation = (
        statistics.pstdev(throughputs) / mean if mean > 0 else math.inf
    )
    telemetries = [measurement["trial"]["gpu_telemetry"] for measurement in measurements]
    return {
        "n_envs": n_envs,
        "repeat_count": len(measurements),
        "measured_environment_steps": sum(
            int(measurement["trial"]["environment_steps"])
            for measurement in measurements
        ),
        "throughput_min": min(throughputs),
        "throughput_p50": linear_percentile(throughputs, 0.50),
        "throughput_mean": mean,
        "throughput_p95": linear_percentile(throughputs, 0.95),
        "throughput_max": max(throughputs),
        "throughput_coefficient_of_variation": coefficient_of_variation,
        "mean_gpu_utilization_pct": _weighted_gpu_mean(measurements),
        "max_gpu_utilization_pct": max(
            float(telemetry["max_gpu_utilization_pct"]) for telemetry in telemetries
        ),
        "peak_vram_used_bytes": max(
            float(telemetry["max_vram_used_bytes"]) for telemetry in telemetries
        ),
        "total_vram_bytes": max(
            float(telemetry["total_vram_bytes"]) for telemetry in telemetries
        ),
    }


def assemble_scale_v3_report(
    protocol: Mapping[str, object],
    measurements: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Assemble a fully derived V3 report from immutable V2 raw trials."""

    validate_scale_v3_protocol(protocol, require_frozen_formal=False)
    expected_pairs = [
        (int(n_envs), repeat_index)
        for n_envs in protocol["batch_sizes"]
        for repeat_index in range(1, int(protocol["repeats_per_batch"]) + 1)
    ]
    ordered = sorted(
        (
            {
                "n_envs": int(item["n_envs"]),
                "repeat_index": int(item["repeat_index"]),
                "trial": dict(item["trial"]),
            }
            for item in measurements
        ),
        key=lambda item: (item["n_envs"], item["repeat_index"]),
    )
    actual_pairs = [(item["n_envs"], item["repeat_index"]) for item in ordered]
    if actual_pairs != expected_pairs:
        raise ValueError("measurement set does not match the V3 protocol")
    trial_protocol = protocol["trial_protocol"]
    for item in ordered:
        trial = item["trial"]
        if int(trial.get("n_envs", 0)) != item["n_envs"]:
            raise ValueError("measurement wrapper batch size differs from raw trial")
        validate_scale_v2_trial(trial, trial_protocol, require_telemetry=True)

    batch_summaries = []
    for n_envs in protocol["batch_sizes"]:
        subset = [item for item in ordered if item["n_envs"] == int(n_envs)]
        batch_summaries.append(_batch_summary(int(n_envs), subset))
    largest = batch_summaries[-1]
    smallest = batch_summaries[0]
    report: dict[str, object] = {
        "schema_version": RADEON_SCALE_V3_SCHEMA_VERSION,
        "benchmark_name": RADEON_SCALE_V3_BENCHMARK_NAME,
        "evidence_scope": RADEON_SCALE_V3_SCOPE,
        "protocol": dict(protocol),
        "measurements": ordered,
        "batch_summaries": batch_summaries,
        "summary": {
            "batch_count": len(batch_summaries),
            "measurement_count": len(ordered),
            "largest_parallel_batch": int(largest["n_envs"]),
            "total_measured_environment_steps": sum(
                int(batch["measured_environment_steps"]) for batch in batch_summaries
            ),
            "largest_batch_throughput_p50": float(largest["throughput_p50"]),
            "largest_batch_throughput_p95": float(largest["throughput_p95"]),
            "largest_batch_throughput_min": float(largest["throughput_min"]),
            "largest_batch_throughput_max": float(largest["throughput_max"]),
            "largest_vs_smallest_batch_p50_ratio": float(largest["throughput_p50"])
            / float(smallest["throughput_p50"]),
            "peak_batch_p50_throughput": max(
                float(batch["throughput_p50"]) for batch in batch_summaries
            ),
            "mean_gpu_utilization_pct": _weighted_gpu_mean(ordered),
            "peak_gpu_utilization_pct": max(
                float(batch["max_gpu_utilization_pct"]) for batch in batch_summaries
            ),
            "peak_vram_used_bytes": max(
                float(batch["peak_vram_used_bytes"]) for batch in batch_summaries
            ),
        },
    }
    report["report_sha256"] = canonical_sha256(report)
    return report


def validate_scale_v3_report(
    report: Mapping[str, object],
    *,
    require_frozen_formal: bool = True,
) -> dict[str, object]:
    """Strictly recompute every V3 report field and validate its hash."""

    if report.get("schema_version") != RADEON_SCALE_V3_SCHEMA_VERSION:
        raise ValueError("unsupported Radeon Scale V3 report schema")
    if report.get("benchmark_name") != RADEON_SCALE_V3_BENCHMARK_NAME:
        raise ValueError("unexpected Radeon Scale V3 report name")
    if report.get("evidence_scope") != RADEON_SCALE_V3_SCOPE:
        raise ValueError("Radeon Scale V3 evidence scope mismatch")
    protocol = report.get("protocol")
    if not isinstance(protocol, Mapping):
        raise TypeError("report.protocol must be an object")
    validate_scale_v3_protocol(
        protocol,
        require_frozen_formal=require_frozen_formal,
    )
    measurements = report.get("measurements")
    if not isinstance(measurements, list):
        raise TypeError("report.measurements must be a list")
    derived = assemble_scale_v3_report(protocol, measurements)
    if dict(report) != derived:
        without_hash = {
            key: value for key, value in report.items() if key != "report_sha256"
        }
        if report.get("report_sha256") != canonical_sha256(without_hash):
            raise ValueError("Radeon Scale V3 report hash mismatch")
        raise ValueError("Radeon Scale V3 report derived fields mismatch")
    summary = report["summary"]
    if require_frozen_formal:
        if int(summary["measurement_count"]) != RADEON_SCALE_V3_TOTAL_MEASUREMENTS:
            raise ValueError("formal V3 measurement count mismatch")
        if int(summary["total_measured_environment_steps"]) != (
            RADEON_SCALE_V3_TOTAL_ENVIRONMENT_STEPS
        ):
            raise ValueError("formal V3 environment-step count mismatch")
    return {
        "status": "passed",
        "schema_version": RADEON_SCALE_V3_SCHEMA_VERSION,
        "protocol_sha256": protocol["protocol_sha256"],
        "report_sha256": report["report_sha256"],
        "measurement_count": summary["measurement_count"],
        "largest_parallel_batch": summary["largest_parallel_batch"],
        "total_measured_environment_steps": summary[
            "total_measured_environment_steps"
        ],
        "frozen_formal_required": require_frozen_formal,
    }
