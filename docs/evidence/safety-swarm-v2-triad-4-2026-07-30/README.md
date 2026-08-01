# Safety Swarm V2 Gate V2-A Radeon evidence

This directory preserves the raw evidence for the predeclared `triad-4`
engineering smoke executed on AMD Radeon Cloud on 2026-07-30.

## Frozen scope and provenance

- Source commit:
  `dd300f98320f39666f684c3aed1f3afa25884d20`
- Mode: `radeon_engineering_smoke`
- Tier: `triad-4`
- Candidates: 3
- Worlds per candidate: 4
- Candidate-world pairs: 12
- Tier protocol SHA-256:
  `4fad8ddaebbff6f2b328af83671465574a0482046a1361522ae8399c15fd574c`
- Formal protocol SHA-256:
  `7fedeeeea436f3b0fe04196e4ad5ec225ccfe7bf26ad60cd3af8a7a4f4da43ac`
- Report SHA-256:
  `61fff08c21accbae5d237905d754e48e530e2bbfa33ca0642d62b2331f58874a`

The run used a clean detached worktree at
`/workspace/persistent/GuardianSim-safety-swarm-v2`. The earlier V1 evidence
commit was not an ancestor of the V2 source commit, so the existing cloud
worktree and its evidence were left untouched.

## Strictly validated result

Strict schema-1 validation passed with decision `execute`. Exactly one
candidate qualified across all four frozen worlds:

- `yaw_+00.0_offset_+0.000`: 4/4 safe, zero contacts, `42.136 mm`
  worst-case sampled clearance, `42.985 mm` fifth-percentile sampled
  clearance, and `0.923` minimum stability.
- `yaw_+67.5_retreat_+0.000_approach_+0.140`: 2/4 safe and two
  clutter-contact failures.
- `yaw_+67.5_retreat_+0.025_approach_+0.140`: 0/4 safe, with one
  clutter-contact failure and three stability failures.

Across all 12 candidate-world pairs, 6 were safe and 3 recorded sampled
clutter contact. Gate V2-A passes because the frozen acceptance rule requires
at least one candidate to pass all four worlds; it does not assert that every
candidate-world pair is safe.

The offline fixture selected a different candidate. The Radeon result above
therefore also confirms that fixture values were not reused as performance or
decision evidence.

## AMD Radeon execution

- Device: AMD Radeon Graphics
- PyTorch: `2.9.1+gitff65f5b`
- HIP: `7.2.53211-e1a6bc5663`
- Genesis: `1.2.3`
- Batched execution wall time: `10.755 s`
- Environment steps: `5,988`
- Environment steps/s: `556.783`
- Candidate-world pairs/s: `1.116`
- GPU telemetry samples: 27
- Mean GPU utilization: `69%`
- Peak GPU utilization: `94%`
- Maximum VRAM used: `1,126,154,240 bytes` (about `1.049 GiB`)
- Telemetry sampling errors: none

## Integrity and claim boundary

- Downloaded archive:
  `safety-swarm-v2-triad-4-evidence-2026-07-30.tar.gz`
- Archive SHA-256:
  `7280f59866980954ec52287fd4046069c487dfb23bca5f8c51d91c72568f877f`
- Archive inspection: 15 members, 14 files, no absolute paths, parent
  traversal, symbolic links, or hard links.
- All 13 payloads listed in `SHA256SUMS` passed local verification.
- The imported `report.json` passed the repository validator again with
  `--require-radeon`.

This is small-tier executor evidence with `showcase_ready=false`. It is not a
formal robustness result, a real-robot trial, or a physical safety guarantee.
No threshold, candidate order, world order, or protocol identity was changed
after observing the result.

The next unopened gate is V2-B: all 18 frozen candidates against the same four
worlds, or 72 candidate-world pairs.
