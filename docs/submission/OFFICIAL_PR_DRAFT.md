# Official Repository Pull Request Record

The English body below is the locally verified V4 replacement for organizer
PR #39. It derives from the V3 public body but now carries the Scale V2 metrics,
V4 immutable URLs, and policy-to-simulation architecture sentence. It must not
be applied until the exact V4 tag and public links pass their release checks.

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

A PPO, VLA, or scripted policy may propose a motion. GuardianSim uses Radeon
as a parallel physical-simulation co-processor before execution, then permits
one eligible action or refuses to move.

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

The frozen Radeon Scale V2 suite ran eight batches from 1 to 4,096 full
headless Franka/table/four-YCB Genesis scenes on one Radeon GPU:

- **4,096** simultaneous worlds in the largest batch;
- **50,331,648** measured environment steps at that batch;
- **152,099 environment-steps/s** and **1,028.07x** speedup versus one world;
- **98.7% mean / 99% peak GPU utilization** and **6.25 GiB peak VRAM**;
- **98,512,896** measured environment steps across the complete sweep.

Strict schema-2 validation passed and every batch completed on its first
attempt. The reported unit is a Genesis environment step, not a PPO training
sample, dataset row, independent safety trial, or physical-robot execution.

The formal Safety Swarm V2 run advanced **2,299,392** Genesis environment
steps in **226.676 s** (**10,143.979 environment-steps/s**). Radeon telemetry
recorded **73.406% mean / 97% peak GPU utilization**. These measurements are
separate from the 30-scenario safety benchmark and the eight-point capacity
curve above.

## Deliverables

- Public interactive evidence arena:
  https://nvm-star-max.github.io/GuardianSim/
- Source and reproducibility instructions:
  https://github.com/nvm-star-max/GuardianSim/tree/hackathon-2026-submission-v4
- Technical report:
  `submissions/Track3-Aegis-Motion-GuardianSim/GuardianSim-Technical-Report.pdf`
- 3–5 minute workflow demo:
  https://raw.githubusercontent.com/nvm-star-max/GuardianSim/hackathon-2026-submission-v4/docs/submission/GuardianSim-Aegis-Motion-demo-review-v2.mp4
- Owner-approved 80-second Scale V2 Radeon preview:
  https://raw.githubusercontent.com/nvm-star-max/GuardianSim/hackathon-2026-submission-v4/docs/submission/GuardianSim-Radeon-Parallel-Futures-narrated-v5.mp4
- Raw Radeon scale and Safety Swarm V2 reports:
  `submissions/Track3-Aegis-Motion-GuardianSim/evidence/`
- Immutable benchmark evidence and checksums:
  https://github.com/nvm-star-max/GuardianSim/tree/hackathon-2026-submission-v4/docs/evidence
- Container path and documented hardware requirement:
  https://github.com/nvm-star-max/GuardianSim/blob/hackathon-2026-submission-v4/REPRODUCIBILITY.md#6-docker-path

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

## V3 historical release checks

- Completed: immutable V3 URLs returned HTTP 200.
- Completed: annotated tag `hackathon-2026-submission-v3` peels to
  `5f7e3f7c8f984fd378f8c147038d84fb2e4983b3`.
- Completed: the official-package PDF and all ten manifest entries passed from
  a fresh clone of PR head `2657aa23e84c9f75e4f55b8cdec49bba985a8870`.
- Completed by owner before release: private registration identity, Discord
  contact, personal eligibility, and the legal acceptance items recorded in
  `RULES_REVIEW_2026-07-28.md`.

## V4 positioning sentence status

This sentence is included in the V4 body above but has not yet been applied to
the public PR:

> A PPO, VLA, or scripted policy may propose a motion. GuardianSim uses Radeon
> as a parallel physical-simulation co-processor before execution, then
> permits one eligible action or refuses to move.

## Pending V4 verified Radeon replacement

The following block is locally verified but has not been applied to the public
organizer PR:

```markdown
## Measured Radeon scale

The frozen Radeon Scale V2 suite ran eight batches from 1 to 4,096 full
headless Franka/table/four-YCB Genesis scenes on one Radeon GPU:

- **4,096** simultaneous worlds in the largest batch;
- **50,331,648** measured environment steps at that batch;
- **152,099 environment-steps/s** and **1,028.07x** speedup versus one world;
- **98.7% mean / 99% peak GPU utilization** and **6.25 GiB peak VRAM**;
- **98,512,896** measured environment steps across the complete sweep.

Strict schema-2 validation passed and every batch completed on its first
attempt. The reported unit is a Genesis environment step, not a PPO training
sample, dataset row, independent safety trial, or physical-robot execution.
```

## Pending V4 deliverable replacement

The local V4 package candidate now contains the Scale V2 eight-page technical
report, owner-approved narrated V5 supplementary preview, strict Scale V2 raw
report, and validator receipt. It has not been pushed to the organizer PR.

At release time, replace every V3 source/evidence URL in the public body with
`hackathon-2026-submission-v4`, replace the old measured-scale section with the
verified block above, and describe the packaged preview as:

```markdown
- Owner-approved 80-second Scale V2 Radeon preview:
  `submissions/Track3-Aegis-Motion-GuardianSim/GuardianSim-Radeon-Parallel-Futures-preview.mp4`
```

Local package manifest SHA-256 before release:
`f8a18439e1b1009ae807e79142f499df4a65de939c7f5e83729e0647afd8b0bd`.
The planned V4 tag and URLs do not exist publicly yet; HTTP checks remain a
release-time gate after the exact local source commit is approved.

The V4 package was also rehearsed from a clean temporary directory on
2026-08-01. All ten manifest entries, strict Scale V2 validation, artifact
identity checks, JSON receipts, and a complete audio/video decode passed. The
candidate totals `3,551,598` bytes across ten payload files plus the manifest.
