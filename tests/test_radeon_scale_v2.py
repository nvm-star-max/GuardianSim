from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from guardian_sim.radeon_scale import derive_trial_metrics
from guardian_sim.radeon_scale_v2 import (
    RADEON_SCALE_V2_BATCH_SIZES,
    RADEON_SCALE_V2_LARGEST_BATCH_ENVIRONMENT_STEPS,
    RADEON_SCALE_V2_MEASUREMENT_STEPS,
    RADEON_SCALE_V2_TOTAL_ENVIRONMENT_STEPS,
    assemble_scale_v2_report,
    build_scale_v2_protocol,
    validate_scale_v2_protocol,
    validate_scale_v2_report,
)
from scripts.run_radeon_scale_v2_suite import (
    verify_checksums,
    write_checksums,
)
from scripts.run_radeon_scale_v2_trial import write_json_exclusive


class RadeonScaleV2Test(unittest.TestCase):
    def setUp(self) -> None:
        self.protocol = build_scale_v2_protocol(
            batch_sizes=(1, 4, 8),
            warmup_steps=2,
            measurement_steps=10,
            scene_source_sha256="a" * 64,
            scene_config_sha256="b" * 64,
            trial_runner_sha256="c" * 64,
        )

    def _trial(self, n_envs: int, seconds: float) -> dict[str, object]:
        return {
            "status": "passed",
            "protocol_sha256": self.protocol["protocol_sha256"],
            "backend": "genesis_gpu",
            "n_envs": n_envs,
            "process_id": 123,
            "started_at_utc": "2026-07-31T00:00:00+00:00",
            "finished_at_utc": "2026-07-31T00:00:01+00:00",
            "build_seconds": 2.0,
            "warmup_seconds": 1.0,
            "measurement_seconds": seconds,
            **derive_trial_metrics(
                n_envs=n_envs,
                measurement_steps=10,
                measurement_seconds=seconds,
            ),
            "device": {
                "name": "AMD Radeon PRO W7900",
                "torch_version": "2.9.1",
                "hip_version": "7.2",
                "genesis_version": "1.2.3",
            },
            "gpu_telemetry": {
                "sample_count": 3,
                "mean_gpu_utilization_pct": 75.0 + n_envs,
                "max_gpu_utilization_pct": 90.0 + n_envs,
                "max_vram_used_bytes": 1_000_000_000 * n_envs,
                "total_vram_bytes": 48_000_000_000,
            },
        }

    def test_exact_formal_workload_counts(self) -> None:
        largest = RADEON_SCALE_V2_BATCH_SIZES[-1] * (
            RADEON_SCALE_V2_MEASUREMENT_STEPS
        )
        total = sum(RADEON_SCALE_V2_BATCH_SIZES) * (
            RADEON_SCALE_V2_MEASUREMENT_STEPS
        )
        self.assertEqual(
            largest,
            RADEON_SCALE_V2_LARGEST_BATCH_ENVIRONMENT_STEPS,
        )
        self.assertEqual(total, RADEON_SCALE_V2_TOTAL_ENVIRONMENT_STEPS)

    def test_assemble_and_validate_nonformal_fixture(self) -> None:
        report = assemble_scale_v2_report(
            self.protocol,
            [
                self._trial(1, 1.0),
                self._trial(4, 2.0),
                self._trial(8, 2.5),
            ],
        )
        validation = validate_scale_v2_report(
            report,
            require_frozen_formal=False,
        )
        self.assertEqual(validation["status"], "passed")
        self.assertEqual(report["summary"]["largest_batch_size"], 8)
        self.assertEqual(report["summary"]["total_measured_environment_steps"], 130)
        self.assertAlmostEqual(
            report["trials"][1]["speedup_vs_single_world"],
            2.0,
        )

    def test_report_hash_and_derived_values_reject_tampering(self) -> None:
        report = assemble_scale_v2_report(
            self.protocol,
            [
                self._trial(1, 1.0),
                self._trial(4, 2.0),
                self._trial(8, 2.5),
            ],
        )
        tampered = copy.deepcopy(report)
        tampered["summary"]["peak_environment_steps_per_second"] += 1
        with self.assertRaisesRegex(ValueError, "summary"):
            validate_scale_v2_report(
                tampered,
                require_frozen_formal=False,
            )

        tampered = copy.deepcopy(report)
        tampered["report_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "report hash"):
            validate_scale_v2_report(
                tampered,
                require_frozen_formal=False,
            )

    def test_frozen_formal_validator_rejects_fixture_protocol(self) -> None:
        with self.assertRaisesRegex(ValueError, "formal batch sizes"):
            validate_scale_v2_protocol(
                self.protocol,
                require_frozen_formal=True,
            )

    def test_rejects_non_amd_and_missing_telemetry(self) -> None:
        report = assemble_scale_v2_report(
            self.protocol,
            [
                self._trial(1, 1.0),
                self._trial(4, 2.0),
                self._trial(8, 2.5),
            ],
        )
        non_amd = copy.deepcopy(report)
        non_amd["trials"][0]["device"]["name"] = "Generic GPU"
        with self.assertRaisesRegex(ValueError, "AMD GPU"):
            validate_scale_v2_report(
                non_amd,
                require_frozen_formal=False,
            )

        no_telemetry = copy.deepcopy(report)
        no_telemetry["trials"][0]["gpu_telemetry"]["sample_count"] = 0
        with self.assertRaisesRegex(ValueError, "no ROCm telemetry"):
            validate_scale_v2_report(
                no_telemetry,
                require_frozen_formal=False,
            )

    def test_exclusive_trial_writer_never_overwrites_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trial.json"
            write_json_exclusive(path, {"attempt": 1})
            with self.assertRaisesRegex(FileExistsError, "refusing to overwrite"):
                write_json_exclusive(path, {"attempt": 2})
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                {"attempt": 1},
            )

    def test_checksum_manifest_covers_exact_evidence_set(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            (output_dir / "a.txt").write_text("alpha\n", encoding="utf-8")
            (output_dir / "b.txt").write_text("beta\n", encoding="utf-8")
            write_checksums(output_dir)
            verify_checksums(output_dir)
            (output_dir / "b.txt").write_text("tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                verify_checksums(output_dir)


if __name__ == "__main__":
    unittest.main()
