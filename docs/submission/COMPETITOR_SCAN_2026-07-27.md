# Official Submission Scan — 2026-07-27

This is a time-stamped competitive snapshot, not a permanent count. Pull
request state, descriptions, and deliverables may change before the deadline.

## Official repository inventory

At the time of inspection, the official AMD repository contained 37 pull
requests: 29 open and 8 closed. Classification from the declared PR title and
body produced:

| Track | Total | Open | Closed |
| --- | ---: | ---: | ---: |
| Track 1 — Multimodal content creation | 6 | 4 | 2 |
| Track 2 — AI PC applications | 27 | 22 | 5 |
| Track 3 — Physical AI | 4 | 3 | 1 |

Official pull-request list:
<https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pulls>

## Track 3 projects

| PR | Project | Demonstrated strength | Submission risk or limitation visible in the PR |
| --- | --- | --- | --- |
| [#11](https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/11) | NaviSense AI | Spoken or typed maritime commands, local LLM feedback, MuJoCo ship simulation, Radeon W7900 metrics, live demo and video links | Primarily training and interaction; the PR presents less formal safety-evaluation evidence than GuardianSim |
| [#13](https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/13) | 1bit.systems real-time NPU inference | Broad XDNA2, Vulkan, HIP, and CPU routing claims with source, report, and demo video | PR description is empty; the concrete embodied task and frozen evaluation protocol are less visible |
| [#28](https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/28) | G1D-Organize-Table | Real Unitree G1-D dual-arm tabletop organization with a VLA policy, training curves, extensive code, and a three-minute video | Reproduction depends on a real robot and local client; the submission is large and includes substantial upstream framework code |
| [#24](https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/24) | VisionPilot | Camera-only runway perception, a humanoid cockpit simulator, a published dataset, model weights, and high inference throughput | The author closed the PR as premature and stated that a final submission would follow |

## GuardianSim position

GuardianSim should not be presented as another grasp policy or another
inference engine. Its defensible category is a policy-agnostic safety-assurance
layer:

> Given a policy-proposed action, evaluate bounded counterfactual alternatives
> from the same physical state on a Radeon GPU, execute only an action that
> passes every frozen safety gate, or stop.

The strongest differentiators are:

1. a frozen, hash-identified benchmark protocol;
2. three independent physical executions for every Gate 3.2 scenario;
3. hard eligibility before utility ranking;
4. explicit safe-stop behavior when no candidate is eligible;
5. immutable raw reports, logs, environment manifests, and checksums;
6. preserved negative evidence rather than only successful demonstrations.

## Award risks and response

| Risk | Response before submission |
| --- | --- |
| A real-robot project has stronger immediate visual impact | Make one accepted baseline-contact versus GuardianSim-safe replay unmistakable with paths, freeze-frame callouts, and exact clearance |
| Current planning is not real-time | State the measured limitation honestly; do not call the system real-time |
| Simulation-only evidence can feel narrow | Position GuardianSim as a safety layer that can wrap policies such as scripted control or VLA, while keeping physical deployment as future work |
| Formal evidence can be difficult to understand quickly | Lead with `CONTACT`, `SAFE`, and `SAFE STOP`; move schema and hashes to the supporting proof |
| A withdrawn strong competitor may return | Freeze a high-quality report and video early instead of expanding experiments |

## Decision

Do not start another broad benchmark merely to increase the scenario count.
The next award-critical milestone is an accepted formal comparison replay and a
complete 3–5 minute video. The report, reproducibility path, and raw Radeon
evidence are already stronger than the visual presentation.

## 2026-08-01 addendum

The open Track 3 count increased to six. The two material additions were:

- PR #45, a SmolVLA fruit-sorting pipeline with LeRobot training on Radeon,
  a small closed-loop evaluation, Docker materials, and a documented upstream
  LeRobot compatibility issue;
- PR #49, Chaal, with PPO locomotion training from random initialization,
  4,096-robot formal training, a separate 32,768-robot scale test, robustness
  measurements, and upstream Genesis contributions.

The official Luma scoring weights were re-verified as 30/20/20/20/10 for robot
capability, Radeon/ROCm adoption, innovation, application value, and upstream
contribution. The resulting judge-view audit and response are recorded in
`JUDGE_RED_TEAM_2026-08-01.md`.
