from __future__ import annotations

import copy
import unittest

from guardian_sim.radeon_scale import derive_trial_metrics
from guardian_sim.radeon_scale_v3 import (
    RADEON_SCALE_V3_BATCH_SIZES,
    RADEON_SCALE_V3_MEASUREMENT_STEPS,
    RADEON_SCALE_V3_REPEATS_PER_BATCH,
    RADEON_SCALE_V3_TOTAL_ENVIRONMENT_STEPS,
    assemble_scale_v3_report,
    build_scale_v3_protocol,
    linear_percentile,
    validate_scale_v3_protocol,
    validate_scale_v3_report,
)


class RadeonScaleV3Test(unittest.TestCase):
    def setUp(self) -> None:
        self.protocol = build_scale_v3_protocol(
            batch_sizes=(4, 8),
            repeats_per_batch=3,
            warmup_steps=2,
            measurement_steps=10,
            scene_source_sha256="a" * 64,
            scene_config_sha256="b" * 64,
            trial_runner_sha256="c" * 64,
            suite_runner_sha256="d" * 64,
        )

    def _trial(self, n_envs: int, seconds: float) -> dict[str, object]:
        metrics = derive_trial_metrics(
            n_envs=n_envs,
            measurement_steps=10,
            measurement_seconds=seconds,
        )
        return {
            "status": "passed",
            "protocol_sha256": self.protocol["trial_protocol"]["protocol_sha256"],
            "backend": "genesis_gpu",
            "n_envs": n_envs,
            "process_id": 123,
            "started_at_utc": "2026-08-03T00:00:00+00:00",
            "finished_at_utc": "2026-08-03T00:00:01+00:00",
            "build_seconds": 2.0,
            "warmup_seconds": 1.0,
            "measurement_seconds": seconds,
            **metrics,
            "device": {
                "name": "AMD Radeon PRO W7900",
                "torch_version": "2.9.1",
                "hip_version": "7.2",
                "genesis_version": "1.2.3",
            },
            "gpu_telemetry": {
                "sample_count": 4,
                "mean_gpu_utilization_pct": 95.0,
                "max_gpu_utilization_pct": 99.0,
                "max_vram_used_bytes": float(n_envs * 1_000_000),
                "total_vram_bytes": 48_000_000_000.0,
                "sampling_errors": [],
            },
        }

    def _measurements(self) -> list[dict[str, object]]:
        measurements = []
        for n_envs in (4, 8):
            for repeat_index, seconds in enumerate((1.0, 0.8, 1.2), start=1):
                measurements.append(
                    {
                        "n_envs": n_envs,
                        "repeat_index": repeat_index,
                        "trial": self._trial(n_envs, seconds),
                    }
                )
        return measurements

    def test_frozen_environment_step_count(self) -> None:
        expected = (
            sum(RADEON_SCALE_V3_BATCH_SIZES)
            * RADEON_SCALE_V3_REPEATS_PER_BATCH
            * RADEON_SCALE_V3_MEASUREMENT_STEPS
        )
        self.assertEqual(expected, RADEON_SCALE_V3_TOTAL_ENVIRONMENT_STEPS)
        self.assertEqual(expected, 293_601_280)

    def test_linear_percentile(self) -> None:
        self.assertEqual(linear_percentile([1, 2, 3, 4, 5], 0.5), 3.0)
        self.assertAlmostEqual(linear_percentile([1, 2, 3, 4, 5], 0.95), 4.8)

    def test_assemble_and_validate_fixture(self) -> None:
        report = assemble_scale_v3_report(self.protocol, self._measurements())
        receipt = validate_scale_v3_report(report, require_frozen_formal=False)
        self.assertEqual(receipt["status"], "passed")
        self.assertEqual(report["summary"]["measurement_count"], 6)
        self.assertEqual(report["summary"]["largest_parallel_batch"], 8)
        self.assertEqual(report["summary"]["total_measured_environment_steps"], 360)
        self.assertEqual(len(report["batch_summaries"]), 2)

    def test_rejects_tampering_and_missing_repeat(self) -> None:
        report = assemble_scale_v3_report(self.protocol, self._measurements())
        tampered = copy.deepcopy(report)
        tampered["summary"]["largest_batch_throughput_p50"] += 1
        with self.assertRaisesRegex(ValueError, "hash mismatch|derived fields"):
            validate_scale_v3_report(tampered, require_frozen_formal=False)

        with self.assertRaisesRegex(ValueError, "measurement set"):
            assemble_scale_v3_report(self.protocol, self._measurements()[:-1])

    def test_formal_validator_rejects_fixture_protocol(self) -> None:
        with self.assertRaisesRegex(ValueError, "formal V3 batch sizes"):
            validate_scale_v3_protocol(self.protocol, require_frozen_formal=True)


if __name__ == "__main__":
    unittest.main()
