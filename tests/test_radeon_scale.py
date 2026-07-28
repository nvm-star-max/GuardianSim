from __future__ import annotations

import copy
import unittest

from guardian_sim.radeon_scale import (
    assemble_scale_report,
    build_scale_protocol,
    derive_trial_metrics,
    validate_scale_report,
)
from guardian_sim.rocm_telemetry import parse_rocm_smi_sample


class RadeonScaleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.protocol = build_scale_protocol(
            batch_sizes=(1, 16, 64),
            warmup_steps=10,
            measurement_steps=100,
            scene_source_sha256="a" * 64,
            scene_config_sha256="b" * 64,
        )

    def _trial(self, n_envs: int, seconds: float) -> dict[str, object]:
        return {
            "status": "passed",
            "protocol_sha256": self.protocol["protocol_sha256"],
            "backend": "genesis_gpu",
            "n_envs": n_envs,
            "build_seconds": 2.0,
            "warmup_seconds": 1.0,
            "measurement_seconds": seconds,
            **derive_trial_metrics(
                n_envs=n_envs,
                measurement_steps=100,
                measurement_seconds=seconds,
            ),
            "device": {
                "name": "AMD Radeon PRO W7900",
                "torch_version": "2.9.1",
                "hip_version": "7.2",
                "genesis_version": "1.1.2",
            },
            "gpu_telemetry": {
                "sample_count": 3,
                "mean_gpu_utilization_pct": 81.0,
                "max_gpu_utilization_pct": 96.0,
                "max_vram_used_bytes": 8_000_000_000,
                "total_vram_bytes": 48_000_000_000,
            },
        }

    def test_assemble_and_validate_report(self) -> None:
        report = assemble_scale_report(
            self.protocol,
            [
                self._trial(1, 1.0),
                self._trial(16, 1.6),
                self._trial(64, 3.2),
            ],
        )
        result = validate_scale_report(report)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(report["summary"]["largest_batch_size"], 64)
        self.assertAlmostEqual(report["trials"][1]["speedup_vs_single_env"], 10.0)
        self.assertEqual(report["summary"]["total_measured_environment_steps"], 8100)

    def test_rejects_tampered_throughput(self) -> None:
        report = assemble_scale_report(
            self.protocol,
            [
                self._trial(1, 1.0),
                self._trial(16, 1.6),
                self._trial(64, 3.2),
            ],
        )
        report["trials"][2]["environment_steps_per_second"] += 1
        with self.assertRaisesRegex(ValueError, "throughput"):
            validate_scale_report(report)

    def test_rejects_non_amd_or_missing_telemetry(self) -> None:
        report = assemble_scale_report(
            self.protocol,
            [
                self._trial(1, 1.0),
                self._trial(16, 1.6),
                self._trial(64, 3.2),
            ],
        )
        non_amd = copy.deepcopy(report)
        non_amd["trials"][0]["device"]["name"] = "Generic GPU"
        with self.assertRaisesRegex(ValueError, "AMD GPU"):
            validate_scale_report(non_amd)

        report["trials"][0]["gpu_telemetry"]["sample_count"] = 0
        with self.assertRaisesRegex(ValueError, "no ROCm telemetry"):
            validate_scale_report(report)

    def test_protocol_is_ordered_and_hashed(self) -> None:
        self.assertEqual(len(self.protocol["protocol_sha256"]), 64)
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            build_scale_protocol(
                batch_sizes=(1, 64, 16),
                warmup_steps=10,
                measurement_steps=10,
                scene_source_sha256="a" * 64,
                scene_config_sha256="b" * 64,
            )

    def test_parse_rocm_smi_json(self) -> None:
        sample = parse_rocm_smi_sample(
            """
            {
              "card0": {
                "GPU use (%)": "97",
                "VRAM Total Memory (B)": "51527024640",
                "VRAM Total Used Memory (B)": "9126805504"
              }
            }
            """
        )
        self.assertEqual(sample["gpu_utilization_pct"], 97.0)
        self.assertEqual(sample["vram_total_bytes"], 51527024640.0)
        self.assertEqual(sample["vram_used_bytes"], 9126805504.0)


if __name__ == "__main__":
    unittest.main()
