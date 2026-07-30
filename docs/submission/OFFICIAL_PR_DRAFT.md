# Official Repository Pull Request Record

This English body was applied to existing organizer PR #39 on 2026-07-30 after
the final report, video, source commit, checksum, public-link, and owner
authorization checks completed. It remains the canonical local copy of the
public PR text.

## Title

```text
Track 3, Aegis Motion, GuardianSim
```

## Body

```markdown
## Project

**GuardianSim — Parallel Counterfactual Safety Search for Robot Manipulation on
AMD Radeon GPUs**

Team: **Aegis Motion** (solo developer)

GuardianSim is a policy-agnostic safety layer for robot manipulation in
Genesis. It evaluates bounded counterfactual grasp actions from the same
fingerprinted physical state on an AMD Radeon GPU, applies frozen hard safety
gates, and either selects an eligible action or explicitly stops.

## Try it first

Open the public **Parallel Futures** evidence arena (no sign-in required):
https://nvm-star-max.github.io/GuardianSim/

The main view renders the exact 18 × 256 formal outcome matrix and the
`4,608 → 5 → 1` decision funnel. Judges can also challenge three preserved
decisions and trace displayed metrics back to immutable reports. The site
replays published evidence and does not create new benchmark samples.

## Verified result

In the frozen 30-scenario Gate 3.2 Genesis benchmark:

- repeatable safe completion: **18/30 baseline → 30/30 GuardianSim**;
- independent safe executions: **58/90 → 90/90**;
- sampled clutter contacts: **30 → 0**;
- mean sampled clutter clearance: **23.191 mm → 46.003 mm**.

These are simulation results, not physical-robot deployment claims.

In the separate Safety Swarm V2 formal decision run:

- **18 candidate actions × 256 uncertainty worlds = 4,608 measured pairs**;
- **5** candidates passed all 256 worlds;
- frozen ranking selected **1** action with **256/256 safe worlds** and
  **0 sampled clutter contacts**;
- selected worst-case sampled clearance: **66.249 mm**;
- selected minimum stability: **0.907**.

The 4,608 pairs are a candidate-by-uncertainty engineering stress-test
population. They are not 4,608 independent robot trials.

## AMD Radeon use

Counterfactual physical rollouts were evaluated with Genesis 1.2.3 on the
`gs.amdgpu` backend in Radeon Cloud. The preserved evaluator environment used
PyTorch `2.9.1+gitff65f5b` with HIP `7.2.53211-e1a6bc5663` and one gfx1100
Radeon GPU.

## Measured Radeon scale and decision workload

A separate fixed-workload suite measured:

- **1 / 16 / 64 / 256** parallel Genesis worlds;
- **154.1 / 2,383.7 / 9,354.3 / 35,166.1 environment-steps/s**;
- **228.16x** speedup and **89.1%** parallel efficiency at 256 worlds;
- **85.5% mean / 96% peak GPU utilization** at 256 worlds.

The formal Safety Swarm V2 run advanced **2,299,392** Genesis environment
steps in **226.676 s** (**10,143.979 environment-steps/s**). Radeon telemetry
recorded **73.406% mean / 97% peak GPU utilization**. These measurements are
separate from the 30-scenario safety benchmark and from the raw 1-to-256-world
throughput curve.

## Deliverables

- Public interactive evidence arena:
  https://nvm-star-max.github.io/GuardianSim/
- Source and reproducibility instructions:
  https://github.com/nvm-star-max/GuardianSim/tree/hackathon-2026-submission-v3
- Technical report:
  `submissions/Track3-Aegis-Motion-GuardianSim/GuardianSim-Technical-Report.pdf`
- 3–5 minute workflow demo:
  https://raw.githubusercontent.com/nvm-star-max/GuardianSim/hackathon-2026-submission-v3/docs/submission/GuardianSim-Aegis-Motion-demo-review-v2.mp4
- 80-second measured Radeon preview:
  `submissions/Track3-Aegis-Motion-GuardianSim/GuardianSim-Radeon-Parallel-Futures-preview.mp4`
- Raw Radeon scale and Safety Swarm V2 reports:
  `submissions/Track3-Aegis-Motion-GuardianSim/evidence/`
- Immutable benchmark evidence and checksums:
  https://github.com/nvm-star-max/GuardianSim/tree/hackathon-2026-submission-v3/docs/evidence
- Container path and documented hardware requirement:
  https://github.com/nvm-star-max/GuardianSim/blob/hackathon-2026-submission-v3/REPRODUCIBILITY.md#6-docker-path

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

- Completed: immutable V3 URLs returned HTTP 200.
- Completed: annotated tag `hackathon-2026-submission-v3` peels to
  `5f7e3f7c8f984fd378f8c147038d84fb2e4983b3`.
- Completed: the official-package PDF and all ten manifest entries passed from
  a fresh clone of PR head `2657aa23e84c9f75e4f55b8cdec49bba985a8870`.
- Completed by owner before release: private registration identity, Discord
  contact, personal eligibility, and the legal acceptance items recorded in
  `RULES_REVIEW_2026-07-28.md`.
