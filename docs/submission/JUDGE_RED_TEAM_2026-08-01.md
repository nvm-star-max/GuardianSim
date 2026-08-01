# Judge-view red-team audit — 2026-08-01

This is a time-stamped review of the public Track 3 field and GuardianSim's
submission path. It is not a permanent project count and does not change any
frozen benchmark protocol, report, release tag, or threshold.

## Official criteria and hard requirements

The Luma page and governing Rules & Conditions were re-read on 2026-08-01.
Track 3 is scored out of 100 points:

| Criterion | Points |
| --- | ---: |
| Robot capability performance | 30 |
| AMD Radeon GPU and ROCm adoption | 20 |
| Innovation and originality | 20 |
| Real-world application value | 20 |
| Upstream open-source contribution | 10 |

The rules require a Radeon Cloud Radeon GPU and ROCm, a technical report,
dedicated source, detailed reproduction instructions, and a 3–5 minute
workflow demonstration. They encourage, but do not require, a Docker image.
All environment execution and applicable training or inference must use one
Radeon GPU. The final deadline is 2026-08-06 23:59 UTC+8.

Primary sources:

- <https://luma.com/amd-4dhi>
- <https://docs.google.com/document/d/1TwgwBNUAv8fRNQbkcTZmcRR0__Oi4WMsBfkW38ALZp4/edit>
- <https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/blob/main/README.md>

## Public Track 3 field

Six Track 3 pull requests were open in the organizer repository at inspection
time. Pull-request descriptions may change before the deadline.

| PR | Project | Strongest judge-facing evidence | GuardianSim response |
| --- | --- | --- | --- |
| #11 | NaviSense AI | Clear maritime application, local Qwen and Whisper, MuJoCo, live demo, and published Radeon latency/throughput | Lead with auditable contact avoidance and same-state physical counterfactuals rather than another command interface |
| #13 | 1bit.systems NPU robotics | Broad NPU, HIP, Vulkan, and CPU routing story | Keep GuardianSim's concrete manipulation task, frozen measurements, and reproducible evidence visible |
| #28 | G1D Organize Table | Real Unitree G1-D, VLA policy, tabletop task, and physical-robot video | State the simulation-only boundary; emphasize policy-agnostic safety wrapping and evidence quality rather than claiming hardware equivalence |
| #39 | GuardianSim | Frozen safety comparison, 4,608-pair decision search, 4,096-world Radeon capacity curve, public evidence arena | Make the official scoring evidence scannable in 90 seconds |
| #45 | SmolVLA fruit sorting | End-to-end LeRobot training on Radeon, a compact closed-loop demo, Docker, and a genuine upstream LeRobot issue | Do not imply training; emphasize that GuardianSim can sit after a VLA proposal and before execution |
| #49 | Chaal | PPO from scratch, 4,096 robots, 49.152M training steps, 32,768-robot scale test, robustness table, and upstream Genesis work | Do not compare unlike throughput units; explain full manipulation-scene complexity and the separate safety decision workload |

## GuardianSim score-path audit

| Criterion | Existing verified evidence | Remaining risk |
| --- | --- | --- |
| Robot capability — 30 | 30/30 repeatable safe scenarios, 90/90 safe executions, 30 to 0 sampled clutter contacts | Simulation-only and bounded action family |
| Radeon/ROCm — 20 | 4,096 full scenes, 50,331,648 steps at the largest batch, 152,099 environment-steps/s, 98.7% mean GPU utilization | It is simulation stepping, not PPO or model-training throughput |
| Innovation — 20 | Same-state counterfactual search, hard eligibility before ranking, explicit safe stop, checksummed receipts | The idea can be missed if judges see only a fruit-picking scene |
| Application value — 20 | Policy-agnostic pre-execution safety layer for manipulation in clutter | No physical-robot validation yet |
| Upstream — 10 | Reusable open-source evaluator, validators, ROCm setup, and evidence tooling | No external upstream patch is claimed |

## Decision

The highest-value post-release change is navigation, not another benchmark:

1. add a 90-second judge path to organizer PR #39;
2. map verified evidence to all five official criteria near the top;
3. keep Chaal's PPO numbers, GuardianSim's environment steps, Safety Swarm
   candidate-world pairs, and independent robot executions as separate units;
4. preserve the immutable V4 tag and all frozen reports;
5. do not manufacture an upstream contribution before the deadline.

The public message should be: a policy proposes; Radeon simulates thousands of
physical futures; GuardianSim executes one eligible action or stops, with an
auditable receipt.
