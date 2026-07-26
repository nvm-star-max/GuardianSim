# Gate 3.2 Visual Replay

This directory contains a judge-facing visual replay of one verified Gate 3.2
recovery case.

## Files

- `gate-3-2-seed-411-explained-v2.mp4` — recommended 18.1-second
  judge-facing explainer with slow playback, obstacle callouts, red/green
  borders, phase labels, a contact-frame pause, and a final result card.
- `gate-3-2-seed-411-explained-v2.json` — provenance showing that the
  explainer is presentation-only post-processing of the verified source MP4.
- `gate-3-2-seed-411-explained-v2-preview.png` — final result-card preview.
- `gate-3-2-seed-411.mp4` — side-by-side nominal/GuardianSim replay.
- `gate-3-2-seed-411.json` — scenario, selected action, measured metrics, and
  classification.
- `gate-3-2-seed-411-preview.png` — browser playback preview.

Explained MP4 SHA-256:
`2092b9604fa7d37ab9a67bfc9299258e74eb8d2362e9132e38b4e5d65573b6d7`

MP4 SHA-256:
`a6b8fa20b924268955c7c40e002faf3b048f5de534f3c19a2ba071f0c7a4e3be`

## What to look for

- Left, red: the nominal gripper approaches at `0°` and intersects the circled
  plum obstacle. The sampled overlap depth is `1.42 mm`.
- Right, green: GuardianSim rotates the gripper to `+67.5°`, avoids overlap,
  and retains `17.09 mm` minimum clearance.
- Both panels come from the same verified source replay and initial state.
- The apparent difference is primarily gripper orientation and obstacle
  clearance, not whether the target lemon is lifted.

## Verified replay outcome

- Scenario: `014_lemon-lateral_clutter-r01-s411`.
- Primary obstacle: `018_plum`.
- Nominal baseline:
  - candidate `yaw_+00.0_offset_+0.000`;
  - clutter contact;
  - minimum measured clearance `0.000000 m`;
  - retained-lift stability `0.936245`.
- GuardianSim:
  - candidate `yaw_+67.5_retreat_+0.000_approach_+0.140`;
  - safe completion;
  - minimum measured clearance `0.017094 m`;
  - retained-lift stability `0.948657`.

## Claim boundary

This is a fresh visual replay from the same frozen scenario configuration using
the Guardian action recorded in the formal report. It is not appended to the
formal schema-5 report and is not an additional statistical trial. The formal
Gate 3.2 result remains the separately preserved 30-scenario benchmark under
[`../evidence/gate-3-2`](../evidence/gate-3-2).

The recommended `explained-v2` MP4 does not re-execute Genesis physics. Its
sidecar binds it to the verified source-video SHA-256 above and records
`physics_reexecuted: false` and `statistical_trial_added: false`.
