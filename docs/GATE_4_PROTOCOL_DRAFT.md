# Gate 4.0 Large-Sample Robustness Protocol — Outcome-Blind Draft

Status: **implemented and locally preflighted; not launched; not yet a
performance claim**

Drafted: 2026-07-28, before observing any Gate 4 Radeon outcome.

Protocol SHA-256:
`b20494f26fad7574d8c59e3a8393563bd44d49432edcae21e76d6dc46375300d`

Scenario-matrix SHA-256:
`4d96a2125a2744df96add7e2633e6011221908f492827e89bae5bee8d25c051c`

This draft does not alter the frozen Gate 3.2 or Gate 3.3 reports, thresholds,
hashes, or claims. It defines the next independent evaluation before any new
outcome is observed.

## 1. Why this gate exists

Gate 3.2 is a strong focused mechanism proof, but its primary statistical
sample contains only 30 paired scene units. The preserved Gate 3.2 and Gate
3.3 evidence is computationally larger than that headline suggests:

- 42 evidence-bound scene units;
- 1,185 counterfactual candidate rollouts;
- 202 final baseline or GuardianSim executions;
- 1,387 total simulated action traces.

Those nested traces are real Genesis executions, but they are not 1,387
independent scenes. Gate 4 increases the independent scene count instead of
renaming nested repeats.

## 2. Frozen matrix shape

Gate 4 contains **240 new paired scene units**:

- 4 perturbation strata:
  - `pose_shift`;
  - `gap_bearing`;
  - `dynamics_extreme`;
  - `perception_bias`;
- 3 target objects;
- 2 clutter-layout families;
- 10 deterministic seeds per cell;
- seeds 1001–1240, disjoint from Gates 3.1–3.3.

The matrix has 24 balanced cells and 10 scenarios per cell. Scenario
generation, ordering, perturbation levels, and seed identities are implemented
in `guardian_sim/gate4_protocol.py`.

## 3. Four-shard execution

The run is split by perturbation stratum:

- four sequential shards;
- 60 contiguous scenarios per shard;
- one independent Genesis base-snapshot fingerprint per shard;
- one report, process log, launch record, validation record, and checksum
  manifest per shard;
- one aggregate manifest binding all four shard hashes.

This avoids pretending that a new Genesis process reproduced an earlier
process's exact base snapshot. A failed shard is restarted as a new report; it
is never silently appended to incompatible evidence.

## 4. Adaptive action family

Every scene first evaluates the unchanged 18-candidate Gate 3.2 family.

Only when no base candidate passes all hard gates, the evaluator activates a
predeclared 18-candidate expansion using obstacle-retreat distances of
12.5 mm and 37.5 mm. The maximum action family is therefore 36 unique
candidates.

The expansion:

- is triggered by a frozen rule, not by a desired outcome;
- never relaxes the 10 mm certified-clearance gate;
- never relaxes the 0.70 retained-stability gate;
- retains explicit safe-stop behavior if no expanded candidate is eligible;
- records whether expansion was activated and every expanded rollout.

Before cloud launch, a parity smoke must verify that the adaptive evaluator
returns the same selection as Gate 3.2 when the base family already contains
an eligible winner.

## 5. Repeats and workload

For every paired scene:

- baseline executes three independent final repeats;
- GuardianSim executes three independent final repeats unless it issues a
  safe stop;
- the primary scene result requires all three repeats to be safe.

Declared workload:

- 240 independent paired scenes;
- 4,320 mandatory base candidate-screening rollouts;
- at most 8,640 candidate-screening rollouts after adaptive expansion;
- at most 4,320 additional confirmation rollouts;
- 1,440 planned final executions;
- at most 14,400 total simulated action traces.

Only the first number is the independent sample size. The remaining values
describe nested compute and repeatability evidence.

## 6. Endpoints and frozen decision rules

Primary endpoint:

- paired difference in scenario-level repeatable safe completion.

Primary test:

- two-sided exact McNemar test over the 240 paired scene outcomes;
- significance level `0.05`;
- at least `+15` percentage points absolute lift.

Secondary requirements:

- at least 50% fewer clutter-contact executions;
- GuardianSim repeatable task completion no more than 5 percentage points
  below baseline;
- safe-stop count and correctness;
- 10th percentile, median, and mean certified clearance;
- retained-lift stability;
- planning and execution latency;
- per-stratum and per-cell breakdowns;
- adaptive-expansion activation rate and recovery rate.

No threshold, scenario, ordering, or candidate change is allowed after the
first Gate 4 physical outcome is observed. A failed gate remains publishable
negative evidence and cannot be replaced by an edited matrix.

## 7. Launch gates

Radeon execution is blocked until all of these pass:

1. 240-scenario matrix balance and hash validation.
2. Candidate IDs are unique and bounded to 18 base / 36 maximum.
3. Gate 3.2 parity smoke passes on predeclared representative scenes.
4. Two former Gate 3.3 safe-stop geometries are replayed diagnostically:
   expansion may recover them, but the result cannot change Gate 3.3.
5. One two-scenario Gate 4 shard smoke passes strict schema validation.
6. Estimated disk, report-size, and wall-time budgets fit the active cloud
   instance.

This document remains a draft until those launch gates are implemented and
reviewed. No Gate 4 result is currently claimed.
