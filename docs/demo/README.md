# Gate 3.2 Visual Replay

This directory contains a judge-facing visual replay of one verified Gate 3.2
recovery case.

## Files

- `gate-3-2-seed-411-aegis-showcase-v3.mp4` — recommended 17.55-second,
  1920×1080 Aegis Motion hero clip. It adds a branded hook, measured
  top-down action-geometry explanation, verified Genesis replay, contact-frame
  pause, and separate single-replay versus 30-scenario result cards.
- `gate-3-2-seed-411-aegis-showcase-v3.json` — deterministic provenance and
  output metadata for the hero clip.
- `gate-3-2-seed-411-aegis-showcase-v3-validation.json` — strict binding of
  the presentation to the schema-5 formal report, protocol hash, source
  sidecar, source-video hash, and presentation-video hash.
- `gate-3-2-seed-411-aegis-showcase-v3-preview.png` — final result-card
  preview.
- `gate-3-2-seed-411-explained-v2.mp4` — superseded 18.1-second explainer,
  retained for provenance and comparison.
- `gate-3-2-seed-411-explained-v2.json` — provenance showing that the
  explainer is presentation-only post-processing of the verified source MP4.
- `gate-3-2-seed-411-explained-v2-preview.png` — final result-card preview.
- `gate-3-2-seed-411.mp4` — side-by-side nominal/GuardianSim replay.
- `gate-3-2-seed-411.json` — scenario, selected action, measured metrics, and
  classification.
- `gate-3-2-seed-411-preview.png` — browser playback preview.

Recommended V3 MP4 SHA-256:
`38e9adfb2a3f2d90719b60449d092e4caca53afaa2b2f71fe1ade136357dff86`

Superseded V2 MP4 SHA-256:
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

The recommended Aegis Motion V3 MP4 does not re-execute Genesis physics. Its
sidecar binds it to the verified source-video SHA-256 above and records
`physics_reexecuted: false` and `statistical_trial_added: false`.

Strictly validate the entire chain:

```bash
uv run --frozen --no-sync python scripts/validate_gate32_demo.py \
  --presentation-sidecar \
    docs/demo/gate-3-2-seed-411-aegis-showcase-v3.json \
  --presentation-video \
    docs/demo/gate-3-2-seed-411-aegis-showcase-v3.mp4
```

The validator requires the complete 30-episode schema-5 report, matching
frozen protocol hash, matching formal candidate IDs, three formal baseline
contacts, three formal GuardianSim safe executions, a replayed
contact-to-safe contrast, measured overlap, at least 10 mm replay clearance,
and matching video hashes.
