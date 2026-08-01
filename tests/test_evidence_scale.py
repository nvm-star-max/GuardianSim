import json
import unittest
from pathlib import Path

from guardian_sim.evidence_scale import summarize_preserved_evidence

ROOT = Path(__file__).resolve().parents[1]


class EvidenceScaleTests(unittest.TestCase):
    def test_preserved_reports_have_non_inflated_scale_counts(self):
        gate32 = json.loads(
            (ROOT / "docs/evidence/gate-3-2/formal-report.json").read_text()
        )
        gate33 = json.loads(
            (
                ROOT
                / "docs/evidence/gate-3-3-two-strata/raw"
                / "two-strata-report.json"
            ).read_text()
        )

        scale = summarize_preserved_evidence(gate32, gate33)

        self.assertEqual(scale.formal_scene_count, 30)
        self.assertEqual(scale.breadth_scene_count, 12)
        self.assertEqual(scale.paired_scene_count, 42)
        self.assertEqual(scale.counterfactual_rollout_count, 1185)
        self.assertEqual(scale.final_execution_count, 202)
        self.assertEqual(scale.simulated_action_trace_count, 1387)

    def test_rejects_the_wrong_report_schema(self):
        with self.assertRaisesRegex(ValueError, "schema version 5"):
            summarize_preserved_evidence(
                {"schema_version": 4, "episodes": []},
                {"schema_version": 6, "episodes": []},
            )
