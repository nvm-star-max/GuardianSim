import unittest

from guardian_sim.gate4_protocol import (
    GATE4_BASE_CANDIDATE_COUNT,
    GATE4_MAX_CANDIDATE_COUNT,
    GATE4_SCENARIO_COUNT,
    GATE4_SCENARIOS_PER_CELL,
    GATE4_SCENARIOS_PER_STRATUM,
    exact_mcnemar_p_value,
    gate4_protocol_payload,
    gate4_workload_budget,
    generate_gate4_candidates,
    paired_outcome_counts,
    validate_gate4_protocol,
)


class Gate4ProtocolTests(unittest.TestCase):
    def test_matrix_has_240_balanced_unseen_scenarios(self):
        scenarios = validate_gate4_protocol()

        self.assertEqual(len(scenarios), GATE4_SCENARIO_COUNT)
        self.assertEqual(GATE4_SCENARIO_COUNT, 240)
        self.assertEqual(GATE4_SCENARIOS_PER_CELL, 10)
        self.assertEqual(GATE4_SCENARIOS_PER_STRATUM, 60)
        self.assertEqual(scenarios[0].seed, 1001)
        self.assertEqual(scenarios[-1].seed, 1240)

    def test_adaptive_candidate_family_is_bounded_and_unique(self):
        target = (0.30, 0.20, 0.75)
        obstacle = (0.34, 0.22, 0.75)

        base = generate_gate4_candidates(
            target,
            obstacle,
            include_expansion=False,
        )
        expanded = generate_gate4_candidates(
            target,
            obstacle,
            include_expansion=True,
        )

        self.assertEqual(len(base), GATE4_BASE_CANDIDATE_COUNT)
        self.assertEqual(len(expanded), GATE4_MAX_CANDIDATE_COUNT)
        self.assertEqual(
            len({candidate.candidate_id for candidate in expanded}),
            len(expanded),
        )
        self.assertTrue(
            {candidate.candidate_id for candidate in base}
            < {candidate.candidate_id for candidate in expanded}
        )

    def test_workload_keeps_scenes_separate_from_nested_traces(self):
        budget = gate4_workload_budget()

        self.assertEqual(budget["independent_paired_scenes"], 240)
        self.assertEqual(budget["planned_final_executions"], 1440)
        self.assertEqual(
            budget["maximum_total_simulated_action_traces"],
            14400,
        )

    def test_protocol_is_hashed_before_outcomes_exist(self):
        protocol = gate4_protocol_payload()

        self.assertEqual(protocol["scenario_count"], 240)
        self.assertEqual(
            protocol["status"],
            "draft_outcome_blind_not_yet_executed",
        )
        self.assertEqual(
            protocol["scenario_matrix_sha256"],
            "4d96a2125a2744df96add7e2633e6011221908f492827e89bae5bee8d25c051c",
        )
        self.assertEqual(
            protocol["protocol_sha256"],
            "b20494f26fad7574d8c59e3a8393563bd44d49432edcae21e76d6dc46375300d",
        )

    def test_exact_mcnemar_matches_the_gate32_twelve_to_zero_case(self):
        counts = paired_outcome_counts(
            [True] * 18 + [False] * 12,
            [True] * 30,
        )

        self.assertEqual(counts.guardian_only_safe, 12)
        self.assertEqual(counts.baseline_only_safe, 0)
        self.assertAlmostEqual(exact_mcnemar_p_value(counts), 0.00048828125)

    def test_rejects_unpaired_outcomes(self):
        with self.assertRaisesRegex(ValueError, "equal lengths"):
            paired_outcome_counts([True], [True, False])
