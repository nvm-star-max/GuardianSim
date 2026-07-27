from __future__ import annotations

import unittest

from guardian_sim.demo_validation import replay_retains_contact_to_safe_contrast


class Gate33DemoTests(unittest.TestCase):
    def test_accepts_only_contact_to_safe_replay(self) -> None:
        contact = {
            "clutter_contact": True,
            "safe_completion": False,
        }
        safe = {
            "clutter_contact": False,
            "safe_completion": True,
        }
        self.assertTrue(
            replay_retains_contact_to_safe_contrast(
                formal_baseline=contact,
                formal_guardian=safe,
                replay_baseline=contact,
                replay_guardian=safe,
            )
        )
        self.assertFalse(
            replay_retains_contact_to_safe_contrast(
                formal_baseline=contact,
                formal_guardian=safe,
                replay_baseline=safe,
                replay_guardian=safe,
            )
        )
        self.assertFalse(
            replay_retains_contact_to_safe_contrast(
                formal_baseline=contact,
                formal_guardian=safe,
                replay_baseline=contact,
                replay_guardian=contact,
            )
        )


if __name__ == "__main__":
    unittest.main()
