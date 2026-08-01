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

## Post-run record — Gate V2-A (2026-07-30)

Gate V2-A completed all 12 predeclared candidate-world pairs and passed strict
schema-1 Radeon validation. The preserved report SHA-256 is
`61fff08c21accbae5d237905d754e48e530e2bbfa33ca0642d62b2331f58874a`.

Only `yaw_+00.0_offset_+0.000` qualified, passing all four worlds with zero
contacts. The centered `+67.5°` candidate failed two worlds through sampled
clutter contact. Its `25 mm` retreat counterpart failed all four worlds
through one contact and three stability failures.

This outcome satisfies the frozen V2-A acceptance rule and opens Gate V2-B.
It does not open V2-C or V2-D and remains `showcase_ready=false`. No hard
gate, candidate, world, ordering rule, or protocol identity was changed after
the run.

## Post-run record — Gate V2-B (2026-07-30)

Gate V2-B completed the exact frozen 18×4 assignment set: all 18 candidates
against worlds `0, 85, 170, 255`, or 72 candidate-world pairs. Strict
schema-1 Radeon validation passed. The preserved report SHA-256 is
`3b8d816c73efd99bdd2d34123e60eed8fb70161ed0d599ddb00e959aae38d4f4`.

Eight candidates qualified across all four worlds. The frozen ranking selected
`yaw_-22.5_retreat_+0.025_approach_+0.140`, with zero contacts,
`96.009 mm` worst-case sampled clearance, `96.857 mm` fifth-percentile sampled
clearance, and `0.847` minimum stability. Across the search population, 41/72
candidate-world pairs were safe and five recorded sampled clutter contact.

The AMD Radeon batch executed `35,928` environment steps in `15.098 s`,
equivalent to `2,379.598` environment steps/s and `4.769` candidate-world
pairs/s. Telemetry recorded `76.378%` mean and `96%` peak GPU utilization over
37 samples, about `1.162 GiB` maximum VRAM use, and no sampling errors.

This outcome satisfies the frozen V2-B acceptance rule and opens Gate V2-C.
It remains `showcase_ready=false`, does not open Gate V2-D, and is not the
4,608-pair formal robustness result. No hard gate, candidate, world, ordering
rule, threshold, or protocol identity changed after inspection.

## Post-run record — Gate V2-C (2026-07-30)

Gate V2-C completed the exact frozen 18×16 assignment set: all 18 candidates
against the predeclared orthogonal 16-world subset, or 288 candidate-world
pairs. Strict schema-1 Radeon validation passed. The preserved report SHA-256
is `0ba9c8db2754c72b2e4e99ebda6ef163763a4244bd9fc068df0b74b21b6f166d`.

Five candidates qualified across all 16 worlds. The frozen ranking selected
`yaw_-45.0_retreat_+0.000_approach_+0.140`, with zero contacts,
`66.339 mm` worst-case sampled clearance, `70.144 mm` fifth-percentile sampled
clearance, and `0.909` minimum stability. The V2-B winner was not the V2-C
winner, and the qualifying set narrowed from eight candidates to five.

Across the 288-pair search population, 165 pairs were safe and 14 recorded
sampled clutter contact. The AMD Radeon batch executed `143,712` environment
steps in `15.870 s`, equivalent to `9,055.573` environment steps/s and
`18.147` candidate-world pairs/s. Telemetry recorded `78.282%` mean and `96%`
peak GPU utilization over 39 samples, about `1.414 GiB` maximum VRAM use, and
no sampling errors.

This outcome satisfies the frozen V2-C acceptance rule and opens Gate V2-D.
It remains `showcase_ready=false` and is not the 4,608-pair formal robustness
result. No hard gate, candidate, world, assignment order, selection rule,
threshold, or protocol identity changed after inspection.

## Pre-run implementation record — Gate V2-D (2026-07-30)

Before any formal execution, the runner was extended to implement the
protocol's existing 256-environment maximum chunk size. The full assignment
stream is divided into exactly 18 candidate-major chunks: one frozen candidate
against all 256 worlds per chunk.

Every chunk has an independently hashed report and strict validator. Failed
attempts are retained under numbered directories; resume skips a chunk only
after strict AMD/HIP/ROCm validation. The complete report requires all 18
chunks in frozen order and reconstructs all 4,608 measurements, labels,
candidate envelopes, selection, source/device identity, timing, telemetry,
and hashes.

The implementation passed `101/101` local tests and kept the formal protocol
SHA-256 unchanged at
`7fedeeeea436f3b0fe04196e4ad5ec225ccfe7bf26ad60cd3af8a7a4f4da43ac`.
This record is not a result: no formal Radeon chunk had run when it was
written.

## Post-run record — Gate V2-D (2026-07-30)

Gate V2-D completed all 18 candidate-major chunks on AMD Radeon Cloud. Each
frozen candidate was evaluated against all 256 frozen worlds exactly once, so
the complete report contains all 4,608 predeclared candidate-world pairs.
Every chunk completed in its first numbered attempt and the source commit
remained `4d0aaec1da077e333cbfdd9ee3f413d852c1cbec`.

Strict complete-report validation passed under the unchanged formal protocol.
The preserved report SHA-256 is
`a3e86baa03e84d75a81062fee5f9f22770a3753708c116168174ea291c7a93cf`.

Five candidates qualified across every one of their 256 worlds with zero
sampled clutter contacts. The frozen ranking selected
`yaw_-45.0_retreat_+0.000_approach_+0.140`, with `256/256` safe worlds,
`66.249 mm` worst-case sampled clearance, `66.304 mm` fifth-percentile
sampled clearance, `0.907` minimum stability, and zero contacts.

Across all evaluated alternatives, 2,614/4,608 candidate-world pairs were
safe and 270 recorded sampled clutter contact. The Radeon workload executed
2,299,392 environment steps in 226.676 seconds, equivalent to 10,143.979
environment steps/s and 20.329 candidate-world pairs/s. Telemetry recorded
73.406% mean and 97% peak GPU utilization over 588 samples, about 1.381 GiB
maximum VRAM use, and no sampling errors.

The evidence archive SHA-256 is
`0450857c2d50446ba76c1358bdf622c7e5cc4f43dbcc6dd48abb2e855b48e9ee`.
The downloaded hash matched, all 90 inner checksums passed, and the imported
report passed local strict Radeon validation.

This result satisfies Gate V2-D and is `showcase_ready=true` for the declared
engineering protocol. Its scope remains the frozen candidate-by-uncertainty
simulation stress test. It does not establish physical-robot safety and the
4,608 pairs must not be represented as independent real-robot trials.
