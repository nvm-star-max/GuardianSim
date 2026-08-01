from __future__ import annotations

import copy
import unittest

from guardian_sim.candidates import generate_obstacle_aware_candidates
from guardian_sim.parallel_futures import (
    PARALLEL_FUTURES_REPORT_NAME,
    PARALLEL_FUTURES_SCHEMA_VERSION,
    assign_parallel_futures,
    build_parallel_future_poses,
    build_parallel_futures_protocol,
    validate_parallel_futures_report,
)


class ParallelFuturesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.candidates = tuple(
            generate_obstacle_aware_candidates(
                (0.31, 0.22, 0.78),
                (0.31, 0.12, 0.78),
            )
        )

    def _report(self) -> dict[str, object]:
        protocol = build_parallel_futures_protocol(self.candidates)
        assignments = assign_parallel_futures(self.candidates)
        results = [
            {
                "env_index": item.env_index,
                "candidate_id": item.candidate_id,
                "repeat_index": item.repeat_index,
                "minimum_clearance_m": 0.02,
                "reachable": True,
                "predicted_stability": 0.9,
                "path_length_m": 0.3,
                "hard_safe": True,
            }
            for item in assignments
        ]
        wall_seconds = 4.5
        return {
            "schema_version": PARALLEL_FUTURES_SCHEMA_VERSION,
            "report_name": PARALLEL_FUTURES_REPORT_NAME,
            "backend": "genesis_gpu_batched",
            "protocol": protocol,
            "device": {
                "name": "AMD Radeon PRO W7900",
                "hip_version": "7.2",
            },
            "gpu_telemetry": {"sample_count": 3},
            "results": results,
            "summary": {
                "batched_execution_wall_seconds": wall_seconds,
                "candidate_futures_per_second": len(results) / wall_seconds,
                "hard_safe_future_count": len(results),
            },
        }

    def test_assigns_eighteen_candidates_across_fifty_four_envs(self) -> None:
        assignments = assign_parallel_futures(self.candidates)
        self.assertEqual(len(assignments), 54)
        self.assertEqual(
            {item.env_index for item in assignments},
            set(range(54)),
        )
        self.assertEqual(
            len({(item.candidate_id, item.repeat_index) for item in assignments}),
            54,
        )

    def test_builds_candidate_specific_batched_poses(self) -> None:
        poses = build_parallel_future_poses(
            self.candidates,
            object_yaw_degrees=35.0,
            object_start_height_m=0.78,
            grasp_hand_z_m=0.855,
        )
        self.assertEqual(len(poses), 54)
        self.assertEqual(poses[0].grasp_position, poses[1].grasp_position)
        self.assertNotEqual(
            poses[0].grasp_quaternion_wxyz,
            poses[6].grasp_quaternion_wxyz,
        )

    def test_validates_complete_amd_report(self) -> None:
        validated = validate_parallel_futures_report(self._report())
        self.assertEqual(validated["parallel_environment_count"], 54)
        self.assertEqual(validated["hard_safe_future_count"], 54)

    def test_rejects_coverage_or_label_tampering(self) -> None:
        missing = self._report()
        missing["results"].pop()
        with self.assertRaisesRegex(ValueError, "result count"):
            validate_parallel_futures_report(missing)

        mislabeled = copy.deepcopy(self._report())
        mislabeled["results"][0]["minimum_clearance_m"] = 0.0
        with self.assertRaisesRegex(ValueError, "hard-safe label"):
            validate_parallel_futures_report(mislabeled)


if __name__ == "__main__":
    unittest.main()
