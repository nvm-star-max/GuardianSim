"""Strict validation for the Radeon Safety Critic training/inference report."""

from __future__ import annotations

import math
from collections.abc import Mapping

SAFETY_CRITIC_SCHEMA_VERSION = 1
SAFETY_CRITIC_MODEL_NAME = "GuardianSim Safety Critic"
SAFETY_CRITIC_REQUIRED_BATCH_SIZES = (1, 18, 54, 108, 256, 1024, 4096)
SAFETY_CRITIC_MINIMUM_F1 = 0.80
SAFETY_CRITIC_MINIMUM_UNSAFE_PRECISION = 0.90


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return value


def _finite(value: object, label: str) -> float:
    if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{label} must be finite")
    return float(value)


def validate_safety_critic_report(
    payload: Mapping[str, object],
    *,
    require_ready: bool = True,
) -> dict[str, object]:
    """Validate data separation, held-out quality, and ROCm inference evidence."""

    if payload.get("schema_version") != SAFETY_CRITIC_SCHEMA_VERSION:
        raise ValueError("unsupported Safety Critic schema")
    if payload.get("model_name") != SAFETY_CRITIC_MODEL_NAME:
        raise ValueError("unexpected Safety Critic model name")
    if payload.get("role") != "advisory_prefilter_hard_physics_verifier_remains_authoritative":
        raise ValueError("Safety Critic claim boundary is missing")

    dataset = _mapping(payload.get("dataset"), "dataset")
    if int(dataset.get("row_count", 0)) != 1185:
        raise ValueError("Safety Critic must bind to all 1,185 preserved rollouts")
    if int(dataset.get("scene_count", 0)) != 42:
        raise ValueError("Safety Critic scene count mismatch")
    train_seeds = {
        (str(item[0]), int(item[1]))
        for item in dataset.get("train_scenes", [])
    }
    test_seeds = {
        (str(item[0]), int(item[1]))
        for item in dataset.get("test_scenes", [])
    }
    if not train_seeds or not test_seeds or train_seeds & test_seeds:
        raise ValueError("Safety Critic train/test scenes overlap or are empty")
    if len(train_seeds | test_seeds) != 42:
        raise ValueError("Safety Critic split does not cover all scenes")

    device = _mapping(payload.get("device"), "device")
    if payload.get("backend") != "pytorch_rocm":
        raise ValueError("Safety Critic inference did not use PyTorch ROCm")
    if "amd" not in str(device.get("name", "")).lower():
        raise ValueError("Safety Critic report does not identify an AMD GPU")
    if not str(device.get("hip_version", "")).strip():
        raise ValueError("Safety Critic report is missing HIP")

    evaluation = _mapping(payload.get("evaluation"), "evaluation")
    f1 = _finite(evaluation.get("hard_safe_f1"), "hard-safe F1")
    unsafe_precision = _finite(
        evaluation.get("unsafe_precision"),
        "unsafe precision",
    )
    for name in (
        "hard_safe_accuracy",
        "hard_safe_precision",
        "hard_safe_recall",
        "unsafe_precision",
        "unsafe_recall",
        "hard_safe_f1",
    ):
        metric = _finite(evaluation.get(name), name)
        if not 0.0 <= metric <= 1.0:
            raise ValueError(f"{name} must be in [0, 1]")

    benchmark = payload.get("inference_benchmark")
    if not isinstance(benchmark, list):
        raise TypeError("inference_benchmark must be a list")
    actual_batches = [
        int(_mapping(item, "inference item")["batch_size"])
        for item in benchmark
    ]
    if actual_batches != list(SAFETY_CRITIC_REQUIRED_BATCH_SIZES):
        raise ValueError("Safety Critic inference batch matrix drift")
    for raw_item in benchmark:
        item = _mapping(raw_item, "inference item")
        batch_size = int(item["batch_size"])
        iterations = int(item["throughput_iterations"])
        seconds = _finite(
            item.get("throughput_measurement_seconds"),
            f"batch {batch_size} measurement seconds",
        )
        measured_throughput = _finite(
            item.get("candidates_per_second"),
            f"batch {batch_size} candidates/s",
        )
        expected_throughput = batch_size * iterations / seconds
        if not math.isclose(
            measured_throughput,
            expected_throughput,
            rel_tol=1e-9,
            abs_tol=1e-9,
        ):
            raise ValueError(f"batch {batch_size} throughput mismatch")
        p50 = _finite(item.get("latency_p50_ms"), f"batch {batch_size} p50")
        p95 = _finite(item.get("latency_p95_ms"), f"batch {batch_size} p95")
        if p50 <= 0.0 or p95 < p50:
            raise ValueError(f"batch {batch_size} latency quantiles are invalid")
        telemetry = _mapping(
            item.get("gpu_telemetry"),
            f"batch {batch_size} telemetry",
        )
        if int(telemetry.get("sample_count", 0)) < 1:
            raise ValueError(f"batch {batch_size} has no ROCm telemetry")

    ready = (
        f1 >= SAFETY_CRITIC_MINIMUM_F1
        and unsafe_precision >= SAFETY_CRITIC_MINIMUM_UNSAFE_PRECISION
    )
    if bool(payload.get("showcase_ready")) != ready:
        raise ValueError("Safety Critic showcase gate mismatch")
    if require_ready and not ready:
        raise ValueError("Safety Critic did not pass the showcase quality gate")
    return {
        "status": "passed",
        "schema_version": SAFETY_CRITIC_SCHEMA_VERSION,
        "showcase_ready": ready,
        "hard_safe_f1": f1,
        "unsafe_precision": unsafe_precision,
        "largest_batch_size": actual_batches[-1],
    }
