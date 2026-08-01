#!/usr/bin/env python3
"""Train once, then benchmark GuardianSim's advisory Safety Critic on ROCm."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from guardian_sim.rocm_telemetry import RocmSmiSampler
from guardian_sim.safety_critic_data import (
    CRITIC_FEATURE_NAMES,
    extract_safety_critic_rows,
    split_rows_by_scene,
)
from guardian_sim.safety_critic_report import (
    SAFETY_CRITIC_MINIMUM_F1,
    SAFETY_CRITIC_MINIMUM_UNSAFE_PRECISION,
    SAFETY_CRITIC_MODEL_NAME,
    SAFETY_CRITIC_REQUIRED_BATCH_SIZES,
    SAFETY_CRITIC_SCHEMA_VERSION,
    validate_safety_critic_report,
)

DEFAULT_GATE32 = ROOT / "docs" / "evidence" / "gate-3-2" / "formal-report.json"
DEFAULT_GATE33 = (
    ROOT
    / "docs"
    / "evidence"
    / "gate-3-3-two-strata"
    / "raw"
    / "two-strata-report.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _classification_metrics(labels, predictions) -> dict[str, float | int]:
    import numpy as np

    labels = np.asarray(labels, dtype=np.int64)
    predictions = np.asarray(predictions, dtype=np.int64)
    true_positive = int(np.sum((labels == 1) & (predictions == 1)))
    true_negative = int(np.sum((labels == 0) & (predictions == 0)))
    false_positive = int(np.sum((labels == 0) & (predictions == 1)))
    false_negative = int(np.sum((labels == 1) & (predictions == 0)))

    def ratio(numerator: int, denominator: int) -> float:
        return numerator / denominator if denominator else 0.0

    safe_precision = ratio(true_positive, true_positive + false_positive)
    safe_recall = ratio(true_positive, true_positive + false_negative)
    unsafe_precision = ratio(true_negative, true_negative + false_negative)
    unsafe_recall = ratio(true_negative, true_negative + false_positive)
    return {
        "true_positive": true_positive,
        "true_negative": true_negative,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "hard_safe_accuracy": ratio(
            true_positive + true_negative,
            len(labels),
        ),
        "hard_safe_precision": safe_precision,
        "hard_safe_recall": safe_recall,
        "unsafe_precision": unsafe_precision,
        "unsafe_recall": unsafe_recall,
        "hard_safe_f1": ratio(
            2 * safe_precision * safe_recall,
            safe_precision + safe_recall,
        ),
    }


def _benchmark_model(model, sample, torch, np, *, minimum_seconds: float):
    results = []
    model.eval()
    with torch.inference_mode():
        for batch_size in SAFETY_CRITIC_REQUIRED_BATCH_SIZES:
            batch = sample.repeat(batch_size, 1)
            for _ in range(100):
                model(batch)
            torch.cuda.synchronize()

            latency_samples = []
            for _ in range(100):
                started = time.perf_counter()
                model(batch)
                torch.cuda.synchronize()
                latency_samples.append((time.perf_counter() - started) * 1000.0)

            iterations = 256
            while True:
                sampler = RocmSmiSampler()
                sampler.start()
                torch.cuda.synchronize()
                started = time.perf_counter()
                for _ in range(iterations):
                    model(batch)
                torch.cuda.synchronize()
                seconds = time.perf_counter() - started
                telemetry = sampler.stop()
                if seconds >= minimum_seconds or iterations >= 1_048_576:
                    break
                iterations *= 2

            results.append(
                {
                    "batch_size": batch_size,
                    "latency_p50_ms": float(np.percentile(latency_samples, 50)),
                    "latency_p95_ms": float(np.percentile(latency_samples, 95)),
                    "throughput_iterations": iterations,
                    "throughput_measurement_seconds": seconds,
                    "candidates_per_second": batch_size * iterations / seconds,
                    "gpu_telemetry": telemetry,
                }
            )
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate32", type=Path, default=DEFAULT_GATE32)
    parser.add_argument("--gate33", type=Path, default=DEFAULT_GATE33)
    parser.add_argument("--epochs", type=int, default=600)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--learning-rate", type=float, default=8e-4)
    parser.add_argument("--benchmark-minimum-seconds", type=float, default=1.0)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/safety-critic"),
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    import numpy as np
    import torch
    from torch import nn
    from torch.utils.data import DataLoader, TensorDataset

    if not torch.cuda.is_available() or not torch.version.hip:
        raise RuntimeError("Safety Critic training requires ROCm/HIP PyTorch")
    if args.epochs < 1 or args.batch_size < 1:
        raise ValueError("epochs and batch size must be positive")

    torch.manual_seed(2026)
    np.random.seed(2026)
    device = torch.device("cuda")
    gate32 = json.loads(args.gate32.read_text(encoding="utf-8"))
    gate33 = json.loads(args.gate33.read_text(encoding="utf-8"))
    rows = extract_safety_critic_rows(gate32, gate33)
    train_rows, test_rows = split_rows_by_scene(rows)

    x_train_np = np.asarray([row.features for row in train_rows], dtype=np.float32)
    x_test_np = np.asarray([row.features for row in test_rows], dtype=np.float32)
    y_train_safe_np = np.asarray([row.hard_safe for row in train_rows], dtype=np.float32)
    y_test_safe_np = np.asarray([row.hard_safe for row in test_rows], dtype=np.float32)
    y_train_reg_np = np.asarray(
        [
            (
                row.collision_margin_m,
                row.predicted_stability,
                row.path_length_m,
            )
            for row in train_rows
        ],
        dtype=np.float32,
    )
    y_test_reg_np = np.asarray(
        [
            (
                row.collision_margin_m,
                row.predicted_stability,
                row.path_length_m,
            )
            for row in test_rows
        ],
        dtype=np.float32,
    )
    feature_mean = x_train_np.mean(axis=0)
    feature_std = x_train_np.std(axis=0)
    feature_std[feature_std < 1e-6] = 1.0
    regression_mean = y_train_reg_np.mean(axis=0)
    regression_std = y_train_reg_np.std(axis=0)
    regression_std[regression_std < 1e-6] = 1.0
    x_train_np = (x_train_np - feature_mean) / feature_std
    x_test_np = (x_test_np - feature_mean) / feature_std
    y_train_reg_scaled = (
        y_train_reg_np - regression_mean
    ) / regression_std

    class SafetyCritic(nn.Module):
        def __init__(self, input_features: int) -> None:
            super().__init__()
            self.network = nn.Sequential(
                nn.Linear(input_features, 256),
                nn.GELU(),
                nn.LayerNorm(256),
                nn.Linear(256, 256),
                nn.GELU(),
                nn.Linear(256, 128),
                nn.GELU(),
                nn.Linear(128, 4),
            )

        def forward(self, features):
            return self.network(features)

    model = SafetyCritic(len(CRITIC_FEATURE_NAMES)).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.learning_rate,
        weight_decay=1e-4,
    )
    safe_labels = torch.from_numpy(y_train_safe_np)
    positives = float(safe_labels.sum())
    negatives = float(len(safe_labels) - positives)
    positive_weight = torch.tensor([negatives / positives], device=device)
    classification_loss = nn.BCEWithLogitsLoss(pos_weight=positive_weight)
    regression_loss = nn.SmoothL1Loss()
    training_dataset = TensorDataset(
        torch.from_numpy(x_train_np),
        safe_labels,
        torch.from_numpy(y_train_reg_scaled),
    )
    generator = torch.Generator().manual_seed(2026)
    loader = DataLoader(
        training_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        generator=generator,
    )

    model.train()
    losses = []
    training_started = time.perf_counter()
    for _epoch in range(args.epochs):
        epoch_loss = 0.0
        for features, safe_target, regression_target in loader:
            features = features.to(device)
            safe_target = safe_target.to(device)
            regression_target = regression_target.to(device)
            optimizer.zero_grad(set_to_none=True)
            output = model(features)
            loss = classification_loss(output[:, 0], safe_target)
            loss = loss + 0.35 * regression_loss(
                output[:, 1:],
                regression_target,
            )
            loss.backward()
            optimizer.step()
            epoch_loss += float(loss.detach().cpu())
        losses.append(epoch_loss / len(loader))
    torch.cuda.synchronize()
    training_seconds = time.perf_counter() - training_started

    model.eval()
    with torch.inference_mode():
        test_output = model(torch.from_numpy(x_test_np).to(device))
        probabilities = torch.sigmoid(test_output[:, 0]).cpu().numpy()
        regression_scaled = test_output[:, 1:].cpu().numpy()
    predictions = (probabilities >= 0.5).astype(np.int64)
    evaluation = _classification_metrics(y_test_safe_np, predictions)
    regression_predictions = (
        regression_scaled * regression_std + regression_mean
    )
    regression_mae = np.abs(regression_predictions - y_test_reg_np).mean(axis=0)
    evaluation.update(
        {
            "collision_margin_mae_m": float(regression_mae[0]),
            "predicted_stability_mae": float(regression_mae[1]),
            "path_length_mae_m": float(regression_mae[2]),
            "test_row_count": len(test_rows),
        }
    )

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / "safety-critic.pt"
    torch.save(
        {
            "model_name": SAFETY_CRITIC_MODEL_NAME,
            "state_dict": model.state_dict(),
            "feature_names": list(CRITIC_FEATURE_NAMES),
            "feature_mean": feature_mean.tolist(),
            "feature_std": feature_std.tolist(),
            "regression_mean": regression_mean.tolist(),
            "regression_std": regression_std.tolist(),
            "architecture": [len(CRITIC_FEATURE_NAMES), 256, 256, 128, 4],
        },
        checkpoint_path,
    )

    sample = torch.from_numpy(x_test_np[:1]).to(device)
    inference_benchmark = _benchmark_model(
        model,
        sample,
        torch,
        np,
        minimum_seconds=args.benchmark_minimum_seconds,
    )
    train_scenes = sorted(
        {(row.source_gate, row.seed) for row in train_rows}
    )
    test_scenes = sorted(
        {(row.source_gate, row.seed) for row in test_rows}
    )
    showcase_ready = (
        float(evaluation["hard_safe_f1"]) >= SAFETY_CRITIC_MINIMUM_F1
        and float(evaluation["unsafe_precision"])
        >= SAFETY_CRITIC_MINIMUM_UNSAFE_PRECISION
    )
    report = {
        "schema_version": SAFETY_CRITIC_SCHEMA_VERSION,
        "model_name": SAFETY_CRITIC_MODEL_NAME,
        "role": "advisory_prefilter_hard_physics_verifier_remains_authoritative",
        "backend": "pytorch_rocm",
        "device": {
            "name": torch.cuda.get_device_name(0),
            "torch_version": torch.__version__,
            "hip_version": torch.version.hip,
        },
        "dataset": {
            "row_count": len(rows),
            "scene_count": len(train_scenes) + len(test_scenes),
            "train_row_count": len(train_rows),
            "test_row_count": len(test_rows),
            "train_scenes": [list(item) for item in train_scenes],
            "test_scenes": [list(item) for item in test_scenes],
            "feature_names": list(CRITIC_FEATURE_NAMES),
            "gate32_report_sha256": _sha256(args.gate32),
            "gate33_report_sha256": _sha256(args.gate33),
        },
        "training": {
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "learning_rate": args.learning_rate,
            "training_seconds": training_seconds,
            "initial_loss": losses[0],
            "final_loss": losses[-1],
            "checkpoint_sha256": _sha256(checkpoint_path),
            "parameter_count": sum(
                parameter.numel() for parameter in model.parameters()
            ),
        },
        "evaluation": evaluation,
        "quality_gate": {
            "minimum_hard_safe_f1": SAFETY_CRITIC_MINIMUM_F1,
            "minimum_unsafe_precision": SAFETY_CRITIC_MINIMUM_UNSAFE_PRECISION,
        },
        "showcase_ready": showcase_ready,
        "inference_benchmark": inference_benchmark,
    }
    validation = validate_safety_critic_report(
        report,
        require_ready=False,
    )
    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    validation_path = output_dir / "validation.json"
    validation_path.write_text(
        json.dumps(validation, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"report": str(report_path), **validation}, indent=2))


if __name__ == "__main__":
    main()
