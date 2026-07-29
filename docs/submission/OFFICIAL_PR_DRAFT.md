# Official Repository Pull Request Draft

Do not open this pull request until the final report, video, source commit, and
the owner's personal eligibility and legal acceptance checks are complete.

## Title

```text
Track 3, Aegis Motion, GuardianSim
```

## Body

```markdown
## Project

**GuardianSim — Counterfactual Safety Certification for Robot Manipulation on
AMD Radeon GPUs**

Team: **Aegis Motion** (solo developer)

GuardianSim is a policy-agnostic safety layer for robot manipulation in
Genesis. It evaluates bounded counterfactual grasp actions from the same
fingerprinted physical state on an AMD Radeon GPU, applies frozen hard safety
gates, and either selects an eligible action or explicitly stops.

## Try it first

Open the public **Parallel Futures** evidence arena (no sign-in required):
https://nvm-star-max.github.io/GuardianSim/

It lets judges challenge three preserved decisions and trace every displayed
metric back to immutable reports. It replays published evidence and does not
claim new benchmark samples.

## Verified result

In the frozen 30-scenario Gate 3.2 Genesis benchmark:

- repeatable safe completion: **18/30 baseline → 30/30 GuardianSim**;
- independent safe executions: **58/90 → 90/90**;
- sampled clutter contacts: **30 → 0**;
- mean sampled clutter clearance: **23.191 mm → 46.003 mm**.

These are simulation results, not physical-robot deployment claims.

## AMD Radeon use

Counterfactual physical rollouts were evaluated with Genesis 1.2.3 on the
`gs.amdgpu` backend in Radeon Cloud. The preserved evaluator environment used
PyTorch `2.9.1+gitff65f5b` with HIP `7.2.53211-e1a6bc5663` and one gfx1100
Radeon GPU.

## Measured Radeon scale

A separate fixed-workload suite measured:

- **1 / 16 / 64 / 256** parallel Genesis worlds;
- **154.1 / 2,383.7 / 9,354.3 / 35,166.1 environment-steps/s**;
- **228.16x** speedup and **89.1%** parallel efficiency at 256 worlds;
- **85.5% mean / 96% peak GPU utilization** at 256 worlds.

A 54-world engineering run evaluated 18 candidate actions with three repeats
in 12.839 seconds; 32 passed the unchanged hard gates and 22 were rejected.
These are compute measurements. The 337,000 timed environment steps and 54
candidate futures are not additional formal safety scenarios.

## Deliverables

- Public interactive evidence arena:
  https://nvm-star-max.github.io/GuardianSim/
- Source and reproducibility instructions:
  https://github.com/nvm-star-max/GuardianSim/tree/hackathon-2026-submission-v2
- Technical report:
  `submissions/Track3-Aegis-Motion-GuardianSim/GuardianSim-Technical-Report.pdf`
- 3–5 minute workflow demo:
  https://raw.githubusercontent.com/nvm-star-max/GuardianSim/hackathon-2026-submission-v2/docs/submission/GuardianSim-Aegis-Motion-demo-review-v2.mp4
- 80-second measured Radeon preview:
  `submissions/Track3-Aegis-Motion-GuardianSim/GuardianSim-Radeon-Parallel-Futures-preview.mp4`
- Raw Radeon scale and Parallel Futures reports:
  `submissions/Track3-Aegis-Motion-GuardianSim/evidence/`
- Immutable benchmark evidence and checksums:
  https://github.com/nvm-star-max/GuardianSim/tree/hackathon-2026-submission-v2/docs/evidence
- Container path and documented hardware requirement:
  https://github.com/nvm-star-max/GuardianSim/blob/hackathon-2026-submission-v2/REPRODUCIBILITY.md#6-docker-path

## Reproduction

The repository documents a bounded evaluator smoke that verifies source
identity, Radeon/ROCm readiness, the real Genesis scene, three alternatives
from one scene snapshot, strict report validation, and checksums. The smoke is
an execution-path check and is not used as the performance benchmark.

## Limitations

GuardianSim currently uses Genesis simulation, sampled clearance proxies, a
bounded action space, and non-real-time planning. Harder unsupported geometry
can produce a deliberate safe stop. The scale suite measures steady-state
simulation stepping after warmup, not model-training throughput.
```

## Release-time checks

- Confirm every immutable URL remains publicly accessible.
- Confirm tag `hackathon-2026-submission-v2` resolves to the released
  GuardianSim commit containing the Radeon scale implementation and reports.
- Confirm the official-repository PDF path after copying the prepared package.
- Confirm the private Luma registration uses the legal name and intended team
  identity; public materials may use Aegis Motion / `@nvm-star-max`.
- Confirm a valid Discord ID and personal eligibility.
- Do not open the PR until the owner accepts the entry-license,
  publicity/release, winner-form, and tax terms recorded in
  `RULES_REVIEW_2026-07-28.md`.
