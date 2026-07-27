from __future__ import annotations

import copy
import unittest

from guardian_sim.demo_validation import validate_gate32_replay_bundle


def _fixture() -> tuple[dict[str, object], dict[str, object]]:
    baseline_classification = {
        "clutter_contact": True,
        "safe_completion": False,
    }
    guardian_classification = {
        "clutter_contact": False,
        "safe_completion": True,
    }
    formal = {
        "protocol": {"protocol_sha256": "frozen"},
        "episodes": [{
            "seed": 411,
            "scenario_id": "scenario-411",
            "pick_object": "014_lemon",
            "layout": "lateral_clutter",
            "primary_obstacle": "018_plum",
            "baseline": {
                "candidate": {"candidate_id": "nominal"},
                "aggregate": {
                    "execution_count": 3,
                    "clutter_contact_count": 3,
                    "repeatable_safe_completion": False,
                },
            },
            "guardiansim": {
                "candidate": {"candidate_id": "guardian"},
                "aggregate": {
                    "execution_count": 3,
                    "clutter_contact_count": 0,
                    "safe_completion_count": 3,
                    "repeatable_safe_completion": True,
                },
            },
        }],
    }
    replay = {
        "kind": "gate32_visual_replay_not_formal_evidence",
        "formal_protocol_sha256": "frozen",
        "seed": 411,
        "scenario_id": "scenario-411",
        "pick_object": "014_lemon",
        "layout": "lateral_clutter",
        "primary_obstacle": "018_plum",
        "visual_replay": {
            "baseline": {
                "candidate": {"candidate_id": "nominal"},
                "classification": baseline_classification,
                "metrics": {
                    "collision_margin_m": 0.0,
                    "clearance_diagnostic": {
                        "obstacle_name": "018_plum",
                        "overlaps": True,
                        "overlap_depth_m": 0.0014,
                    },
                },
            },
            "guardiansim": {
                "candidate": {"candidate_id": "guardian"},
                "classification": guardian_classification,
                "metrics": {
                    "collision_margin_m": 0.017,
                    "clearance_diagnostic": {
                        "obstacle_name": "018_plum",
                        "overlaps": False,
                        "overlap_depth_m": 0.0,
                    },
                },
            },
        },
    }
    return formal, replay


class Gate32DemoValidationTests(unittest.TestCase):
    def test_accepts_formal_three_contact_to_three_safe_replay(self) -> None:
        formal, replay = _fixture()
        result = validate_gate32_replay_bundle(
            formal_report=formal,
            replay=replay,
        )
        self.assertTrue(result["validated"])
        self.assertAlmostEqual(result["replay_baseline_overlap_mm"], 1.4)
        self.assertAlmostEqual(result["replay_guardian_clearance_mm"], 17.0)

    def test_rejects_candidate_drift(self) -> None:
        formal, replay = _fixture()
        replay["visual_replay"]["guardiansim"]["candidate"][
            "candidate_id"
        ] = "different"
        with self.assertRaisesRegex(ValueError, "candidate differs"):
            validate_gate32_replay_bundle(
                formal_report=formal,
                replay=replay,
            )

    def test_rejects_replay_without_contact_to_safe_contrast(self) -> None:
        formal, replay = _fixture()
        replay = copy.deepcopy(replay)
        replay["visual_replay"]["baseline"]["classification"] = {
            "clutter_contact": False,
            "safe_completion": True,
        }
        with self.assertRaisesRegex(ValueError, "contact-to-safe"):
            validate_gate32_replay_bundle(
                formal_report=formal,
                replay=replay,
            )


if __name__ == "__main__":
    unittest.main()
