## Project

**GuardianSim — Think Thousands. Execute One.**

Team: **Aegis Motion** (solo developer)  
Track: **Track 3 — Physical AI Challenge**

GuardianSim turns AMD Radeon parallel physics into an auditable robot decision.
A PPO, VLA, or scripted policy proposes a motion; GuardianSim restores one
fingerprinted Genesis state, evaluates bounded counterfactual actions across
thousands of complete simulated robot worlds, applies frozen hard safety gates,
then permits one eligible action or explicitly stops.

## Try it first

Open the public evidence arena — no sign-in required:
https://nvm-star-max.github.io/GuardianSim/

The first screen shows the measured Radeon workload directly: **16,384**
complete robot worlds, **278,051 environment-steps/s P50**, **293,601,280**
measured environment steps, **98.33%** weighted mean GPU utilization, and
**22.05 GiB** peak VRAM. The site then traces the compute to the separate
**4,608 → 5 → 1** action-selection funnel and preserved robot replay.

## 90-second judge path

1. Read the Scale V3 strip and 4,096/8,192/16,384-world endurance curve.
2. Inspect the **4,608 candidate-world pairs → 5 qualifiers → 1 action** funnel.
3. Open Seed 411 to compare the same-state nominal overlap with GuardianSim's
   **17.1 mm** sampled-clearance action.
4. Follow any evidence link to the immutable report, validator, and checksums.

## Official Track 3 judging map

| Criterion | Evidence in this submission |
| --- | --- |
| Robot capability performance — 30 | Frozen 30-scenario benchmark: repeatable safe scenarios **18/30 → 30/30**, independent safe Genesis simulations **58/90 → 90/90**, sampled clutter contacts **30 → 0**. |
| AMD Radeon GPU and ROCm adoption — 20 | One Radeon GPU ran **16,384** complete Franka/table/four-YCB Genesis worlds at **278,051 env-steps/s P50**, with **98.817%** largest-batch mean GPU use and **22.05 GiB** peak VRAM. |
| Innovation and originality — 20 | Policy-agnostic, same-state counterfactual safety search: thousands of physical futures become one eligible action or an explicit safe stop. |
| Real-world application value — 20 | A pre-execution decision layer for manipulation policies that separates task completion from clutter-contact risk and leaves an auditable receipt. Evidence is simulation-only. |
| Upstream open-source contribution — 10 | Evaluator, validators, ROCm setup, reports, evidence site, and complete-source Docker path are open and reproducible. No external upstream patch is claimed. |

## Verified Radeon Scale V3 result

The frozen endurance suite built one full headless manipulation scene per
world. Each batch ran in five independent processes, with 200 warmup and 2,048
measured steps per process:

| Parallel worlds | P50 env-steps/s | P95 env-steps/s | Mean GPU | Peak VRAM |
| ---: | ---: | ---: | ---: | ---: |
| 4,096 | 152,697.384 | 153,087.797 | 97.768% | 6.246 GiB |
| 8,192 | 214,944.307 | 215,406.452 | 97.978% | 11.524 GiB |
| 16,384 | 278,051.244 | 278,660.488 | 98.817% | 22.051 GiB |

Across all 15 formal measurements, the suite advanced **293,601,280** Genesis
environment steps, recorded **98.330%** weighted mean GPU utilization, and
reached **100%** observed peak utilization. The largest batch's five-repeat
range was **274,989.939–278,671.733 env-steps/s**.

Strict schema-3 validation and every sealed checksum passed. Environment steps
are physics-throughput units, not PPO samples, inference tokens, dataset rows,
independent safety trials, or physical-robot executions.

## Verified robot-decision result

The separate Safety Swarm V2 run evaluated **18 actions × 256 uncertainty
worlds = 4,608 candidate-world pairs**. Five actions passed all 256 worlds.
Frozen ranking selected one action with **256/256** safe worlds, **0** sampled
clutter contacts, **66.249 mm** worst-case sampled clearance, and **0.907**
minimum stability.

The primary frozen Gate 3.2 benchmark separately recorded:

- repeatable safe scenarios: **18/30 baseline → 30/30 GuardianSim**;
- independent safe Genesis simulations: **58/90 → 90/90**;
- sampled clutter-contact executions: **30 → 0**;
- mean sampled clutter clearance: **23.191 mm → 46.003 mm**.

These are Genesis simulation results, not physical-robot deployment claims.

## AMD Radeon / ROCm implementation

The evidence was produced on AMD Radeon Cloud with one `gfx1100` Radeon GPU,
Genesis 1.2.3 using `gs.amdgpu`, PyTorch `2.9.1+gitff65f5b`, and HIP
`7.2.53211-e1a6bc5663`. The repository includes the pinned environment,
GPU-required preflight, real-Genesis smoke, strict validators, telemetry,
checksums, and complete-source ROCm Dockerfile.

## Deliverables

- Public evidence arena:
  https://nvm-star-max.github.io/GuardianSim/
- Immutable V5 source and evidence:
  https://github.com/nvm-star-max/GuardianSim/tree/hackathon-2026-submission-v5
- Technical report:
  https://raw.githubusercontent.com/nvm-star-max/Radeon-hackathon-2026-07/submission/track3-aegis-motion-guardiansim/submissions/Track3-Aegis-Motion-GuardianSim/GuardianSim-Technical-Report.pdf
- 3–5 minute complete workflow demo:
  https://raw.githubusercontent.com/nvm-star-max/GuardianSim/hackathon-2026-submission-v5/docs/submission/GuardianSim-Aegis-Motion-demo-review-v2.mp4
- 90-second Scale V3 narrated Radeon preview:
  https://raw.githubusercontent.com/nvm-star-max/GuardianSim/hackathon-2026-submission-v5/docs/submission/GuardianSim-Radeon-Scale-V3-narrated-v3.mp4
- Compact organizer evidence:
  https://github.com/nvm-star-max/Radeon-hackathon-2026-07/tree/submission/track3-aegis-motion-guardiansim/submissions/Track3-Aegis-Motion-GuardianSim/evidence
- Full Scale V3 report, trials, logs, telemetry, and checksums:
  https://github.com/nvm-star-max/GuardianSim/tree/hackathon-2026-submission-v5/docs/evidence/radeon-scale-v3-formal-2026-08-03
- Reproducibility and Docker path:
  https://github.com/nvm-star-max/GuardianSim/blob/hackathon-2026-submission-v5/REPRODUCIBILITY.md

## Reproduction

The documented one-command Radeon smoke verifies source identity, GPU/ROCm
readiness, a real Genesis scene, same-snapshot alternatives, strict report
validation, and checksums. The smoke checks the execution path; it is not used
as the Scale V3 performance benchmark.

## Limitations

GuardianSim currently uses Genesis simulation, sampled clearance proxies, a
bounded action space, and non-real-time planning. Unsupported geometry can
produce a deliberate safe stop. No physical robot was tested. The three
published units — Scale V3 environment steps, Safety Swarm candidate-world
pairs, and Gate 3.2 independent simulations — are deliberately kept separate.
