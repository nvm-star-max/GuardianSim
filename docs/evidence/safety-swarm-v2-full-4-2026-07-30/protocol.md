# Radeon Safety Swarm V2 — frozen candidate-selection protocol

## Judge-facing line

**18 actions × 256 uncertain worlds = 4,608 physical counterfactuals. Execute
one action only if it survives its entire uncertainty envelope; otherwise
stop.**

V2 is a new protocol. It does not alter the preserved V1 matrix, thresholds,
reports, or failed 16-world gate.

## Frozen identities

- Candidate catalog: the original ordered Gate 3.2 obstacle-aware family,
  nine yaw angles with centered and `25 mm` retreat variants, exactly 18
  actions.
- Candidate catalog SHA-256:
  `9c3af60dfb812e6128f6e849d27cf2acd0d672cdcb3aa98191656e4009054e44`.
- V1 world matrix SHA-256:
  `71ea95a7194f1e9afdc0690ecdb30037b2a309a03049d26d832b9b21789b43eb`.
- V1 formal protocol SHA-256:
  `9a8c5763d2ca007be924326812e9fd19c3125b8cfa968cdd734e01e7980f462c`.
- V2 formal protocol SHA-256:
  `7fedeeeea436f3b0fe04196e4ad5ec225ccfe7bf26ad60cd3af8a7a4f4da43ac`.
- Full assignment count: `18 × 256 = 4,608` candidate-world pairs.
- Maximum formal GPU batch chunk: 256 environments. Chunks are contiguous in
  candidate-major, then world-ID order and must cover all 4,608 assignments.

## Unchanged hard gates

Each candidate-world result must satisfy all of:

- sampled clutter contact is false;
- inverse-kinematics result is reachable;
- minimum sampled clearance is at least `0.010 m`;
- retained-lift stability is at least `0.70`;
- task completion is true.

A candidate qualifies only if every world in the current declared tier passes
and its contact count is zero. Averages cannot rescue a failed hard gate.

If several candidates qualify, rank only after qualification:

1. highest worst-case clearance;
2. highest 5th-percentile clearance;
3. highest minimum stability;
4. lowest frozen candidate index.

If no candidate qualifies, the only valid decision is `safe_stop`.

## Predeclared execution gates

### Gate V2-A — triad-4

- Candidates:
  - nominal centered action;
  - Gate 3.2 centered `+67.5°` action;
  - corresponding `25 mm` retreat action.
- Worlds: frozen IDs `0, 85, 170, 255`.
- Total: 12 candidate-world pairs in one Genesis GPU scene.
- Purpose: validate candidate×world placement, ordered assignment, physical
  measurements, selection, safe-stop, hashes, and AMD telemetry.
- Acceptance: strict report validation and at least one candidate passing all
  four worlds. This is executor evidence, not a robustness claim.

### Gate V2-B — full-4

- All 18 candidates against the same four worlds.
- Total: 72 candidate-world pairs.
- Acceptance: exact 18×4 coverage, strict validation, and at least one
  qualifying candidate.

### Gate V2-C — full-16

- All 18 candidates against the predeclared orthogonal 16-world subset.
- Total: 288 candidate-world pairs.
- Acceptance: exact 18×16 coverage, strict validation, and at least one
  qualifying candidate.

### Gate V2-D — formal 18×256

Run only after V2-C passes without changing the catalog, V1 matrix, hard
gates, assignment order, selection order, or formal protocol hash. Execute all
4,608 assignments in deterministic chunks, preserve every raw report/log,
validate the complete report, and replay only from that preserved evidence.

## Claim boundary

The 4,608 pairs are an engineering candidate-by-uncertainty stress-test
population, not 4,608 independent real-robot trials and not a physical safety
guarantee. Small-tier results remain `showcase_ready=false`. The workload may
demonstrate AMD ROCm batched-physics throughput only after measured Radeon
telemetry and strict evidence validation.
