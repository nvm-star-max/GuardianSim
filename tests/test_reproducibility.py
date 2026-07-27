from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from guardian_sim.environment_manifest import _os_release, capture_environment, write_manifest
from scripts.validate_candidate_report import validate_candidate_report
from scripts.write_checksums import build_manifest


class EnvironmentManifestTests(unittest.TestCase):
    def test_os_release_parser_handles_quotes_and_comments(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "os-release"
            path.write_text('# comment\nNAME="Test OS"\nVERSION_ID=24.04\n', encoding="utf-8")

            self.assertEqual(
                _os_release(path),
                {"NAME": "Test OS", "VERSION_ID": "24.04"},
            )

    def test_capture_is_portable_without_requiring_a_gpu(self) -> None:
        payload = capture_environment(Path(__file__).resolve().parents[1])

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["project"], "GuardianSim")
        self.assertIn("gpu_ready", payload)
        self.assertIn("torch_runtime", payload)
        self.assertIn("genesis-world", payload["packages"])

    def test_manifest_writer_emits_same_json_to_file_and_stdout(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "environment.json"
            rendered = write_manifest({"schema_version": 1}, output)

            self.assertEqual(json.loads(rendered), {"schema_version": 1})
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), {"schema_version": 1})


class CandidateSmokeValidationTests(unittest.TestCase):
    @staticmethod
    def _payload() -> dict[str, object]:
        ranking = []
        for index, candidate_id in enumerate(("left", "right"), start=1):
            ranking.append(
                {
                    "rank": index,
                    "candidate": {"candidate_id": candidate_id},
                    "metrics": {
                        "collision_margin_m": 0.02,
                        "reachability": 1.0,
                        "grasp_alignment": 0.9,
                        "predicted_stability": 0.8,
                        "path_length_m": 0.5,
                        "perception_uncertainty": 0.05,
                    },
                    "utility": 0.8,
                    "risk": 0.1,
                    "success_probability": 0.9,
                }
            )
        return {
            "schema_version": 3,
            "data_source": "genesis_counterfactual_rollout",
            "snapshot_fingerprint": "abc123",
            "candidate_count": 2,
            "ranking": ranking,
        }

    def test_accepts_valid_report(self) -> None:
        result = validate_candidate_report(self._payload())

        self.assertTrue(result["validated"])
        self.assertEqual(result["top_candidate_id"], "left")

    def test_rejects_duplicate_candidates(self) -> None:
        payload = self._payload()
        payload["ranking"][1]["candidate"]["candidate_id"] = "left"

        with self.assertRaisesRegex(ValueError, "unique"):
            validate_candidate_report(payload)


class ChecksumManifestTests(unittest.TestCase):
    def test_manifest_is_recursive_sorted_and_excludes_itself(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "nested").mkdir()
            (root / "z.txt").write_text("z", encoding="utf-8")
            (root / "nested" / "a.txt").write_text("a", encoding="utf-8")
            output = root / "SHA256SUMS"
            output.write_text("old", encoding="utf-8")

            manifest = build_manifest(root, output)

            self.assertEqual(
                [line.split("  ", 1)[1] for line in manifest.splitlines()],
                ["nested/a.txt", "z.txt"],
            )


class EvaluatorShellTests(unittest.TestCase):
    def test_cloud_preflight_detects_blank_opencode_environment(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        for relative_path in (
            "scripts/evaluator_preflight.sh",
            "scripts/run_evaluator_smoke.sh",
        ):
            source = (repo_root / relative_path).read_text(encoding="utf-8")
            self.assertIn("-x /opt/venv/bin/python", source)
            self.assertIn("export UV_PROJECT_ENVIRONMENT=/opt/venv", source)


if __name__ == "__main__":
    unittest.main()
