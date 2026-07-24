# Gate 2.5 Clearance Diagnostic Evidence

Date: 2026-07-25 (China Standard Time)

This run diagnoses the degenerate zero-clearance metric observed in Radeon
Cloud Session B and tests lateral grasp offsets before any multi-episode
benchmark.

## Run identity

- Instance: `u-13907-735d71cb`
- Repository commit: `e6bfe2f`
- Backend: Genesis on `gs.amdgpu`
- Object: `011_banana`
- Seed: `41`
- Candidate matrix: five yaw angles × three offsets
- Candidate count: 15
- Snapshot:
  `347dfaf0e99c698474afbf06091886915fabf91fafe61581e8c6762685b2bc8b`
- Cloud tests: 16/16 passed
- Process exit code: `0`
- Exact output: [`candidates.json`](candidates.json)

## Decisive finding

All 15 candidates have the same critical collision class:

```text
link: right_finger
obstacle: table_top
support_surface: true
strict AABB overlap: true
overlap depth range: 0.001054–0.001594 m
```

Therefore the previous `collision_margin_m = 0.0` result is not evidence that
every path collides with clutter. The metric is dominated by a roughly
1.1–1.6 mm finger/table overlap during the grasp phase. The table is the
intentional support surface for the target object, so folding this contact into
the same risk feature as collisions with other objects over-penalizes all
candidates and hides true clutter clearance.

## Candidate behavior

- `yaw 0°, offset 0.00 m` remains rank 1 with predicted success `0.46485`.
- `yaw 0°, offset +0.02 m` ranks second with predicted success `0.46406`.
- Every `offset -0.02 m` candidate retained no lift and occupied ranks 11–15.
- Zero and positive offsets retained roughly 87–92% of the requested lift.
- The lateral candidate dimension is therefore informative and should remain.

## Gate decision

Gate 2.5 proves the diagnostic instrumentation and explains the degenerate
metric. The recommended next implementation is a two-channel safety model:

1. `clutter_clearance_m` excludes support surfaces and drives collision risk;
2. `support_contact_depth_m` is reported separately as a grasp/contact
   diagnostic and does not receive the same collision penalty.

After that change, run one more 15-candidate fixed-snapshot check. The
20-episode benchmark remains blocked until at least one clutter-clearance value
is non-zero or a second structural limitation is identified.

The owner requested that the cloud instance remain running, so it was not
destroyed.
