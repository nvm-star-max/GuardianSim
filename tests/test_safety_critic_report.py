from __future__ import annotations

import copy
import unittest

from guardian_sim.safety_critic_report import (
    SAFETY_CRITIC_MODEL_NAME,
    SAFETY_CRITIC_REQUIRED_BATCH_SIZES,
    validate_safety_critic_report,
)


def _report() -> dict[str, object]:
    benchmark = []
    for batch_size in SAFETY_CRITIC_REQUIRED_BATCH_SIZES:
        iterations = 100
        seconds = 2.0
        benchmark.append(
            {
                "batch_size": batch_size,
                "latency_p50_ms": 0.2,
                "latency_p95_ms": 0.3,
                "throughput_iterations": iterations,
                "throughput_measurement_seconds": seconds,
                "candidates_per_second": batch_size * iterations / seconds,
                "gpu_telemetry": {"sample_count": 3},
            }
        )
    train_scenes = [["gate32_formal", seed] for seed in range(401, 431)]
    test_scenes = [["gate33_engineering", seed] for seed in range(501, 513)]
    return {
        "schema_version": 1,
        "model_name": SAFETY_CRITIC_MODEL_NAME,
        "role": "advisory_prefilter_hard_physics_verifier_remains_authoritative",
        "backend": "pytorch_rocm",
        "device": {
            "name": "AMD Radeon PRO W7900",
            "hip_version": "7.2",
        },
        "dataset": {
            "row_count": 1185,
            "scene_count": 42,
            "train_scenes": train_scenes,
            "test_scenes": test_scenes,
        },
        "evaluation": {
            "hard_safe_accuracy": 0.91,
            "hard_safe_precision": 0.90,
            "hard_safe_recall": 0.89,
            "unsafe_precision": 0.92,
            "unsafe_recall": 0.93,
            "hard_safe_f1": 0.895,
        },
        "showcase_ready": True,
        "inference_benchmark": benchmark,
    }


class SafetyCriticReportTests(unittest.TestCase):
    def test_accepts_scene_held_out_rocm_report(self) -> None:
        result = validate_safety_critic_report(_report())
        self.assertTrue(result["showcase_ready"])
        self.assertEqual(result["largest_batch_size"], 4096)

    def test_rejects_scene_leakage(self) -> None:
        report = _report()
        report["dataset"]["test_scenes"].append(["gate32_formal", 401])
        with self.assertRaisesRegex(ValueError, "overlap"):
            validate_safety_critic_report(report)

    def test_rejects_tampered_throughput(self) -> None:
        report = _report()
        report["inference_benchmark"][3]["candidates_per_second"] += 1
        with self.assertRaisesRegex(ValueError, "throughput mismatch"):
            validate_safety_critic_report(report)

    def test_can_preserve_a_valid_report_that_misses_quality_gate(self) -> None:
        report = copy.deepcopy(_report())
        report["evaluation"]["hard_safe_f1"] = 0.70
        report["showcase_ready"] = False
        result = validate_safety_critic_report(report, require_ready=False)
        self.assertFalse(result["showcase_ready"])
        with self.assertRaisesRegex(ValueError, "quality gate"):
            validate_safety_critic_report(report)


if __name__ == "__main__":
    unittest.main()
