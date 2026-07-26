# Gate 3.2 Visual Replay

This directory contains a judge-facing visual replay of one verified Gate 3.2
recovery case.

## Files

- `gate-3-2-seed-411.mp4` — side-by-side nominal/GuardianSim replay.
- `gate-3-2-seed-411.json` — scenario, selected action, measured metrics, and
  classification.
- `gate-3-2-seed-411-preview.png` — browser playback preview.

MP4 SHA-256:
`a6b8fa20b924268955c7c40e002faf3b048f5de534f3c19a2ba071f0c7a4e3be`

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
