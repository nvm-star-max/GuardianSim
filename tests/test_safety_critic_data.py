from __future__ import annotations

import json
import unittest
from pathlib import Path

from guardian_sim.safety_critic_data import (
    CRITIC_FEATURE_NAMES,
    extract_safety_critic_rows,
    split_rows_by_scene,
)

ROOT = Path(__file__).resolve().parents[1]
GATE32 = ROOT / "docs" / "evidence" / "gate-3-2" / "formal-report.json"
GATE33 = (
    ROOT
    / "docs"
    / "evidence"
    / "gate-3-3-two-strata"
    / "raw"
    / "two-strata-report.json"
)


class SafetyCriticDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = extract_safety_critic_rows(
            json.loads(GATE32.read_text(encoding="utf-8")),
            json.loads(GATE33.read_text(encoding="utf-8")),
        )

    def test_extracts_every_unique_preserved_rollout(self) -> None:
        self.assertEqual(len(self.rows), 1185)
        self.assertTrue(all(len(row.features) == len(CRITIC_FEATURE_NAMES) for row in self.rows))
        identities = {
            (
                row.source_gate,
                row.seed,
                row.candidate_id,
                row.observation_index,
            )
            for row in self.rows
        }
        self.assertEqual(len(identities), len(self.rows))

    def test_split_is_scene_held_out(self) -> None:
        train, test = split_rows_by_scene(self.rows)
        self.assertEqual(len(train) + len(test), len(self.rows))
        train_scenes = {(row.source_gate, row.seed) for row in train}
        test_scenes = {(row.source_gate, row.seed) for row in test}
        self.assertFalse(train_scenes & test_scenes)
        self.assertEqual(len(train_scenes) + len(test_scenes), 42)

    def test_hard_safe_labels_have_both_classes(self) -> None:
        labels = {row.hard_safe for row in self.rows}
        self.assertEqual(labels, {0, 1})


if __name__ == "__main__":
    unittest.main()
