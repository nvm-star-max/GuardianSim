# GuardianSim - Counterfactual Safety Certification for Robot Manipulation

**Track:** Track 3 - Physical AI Challenge

**Team:** Aegis Motion

**Team structure:** Solo developer, GitHub
[`@nvm-star-max`](https://github.com/nvm-star-max)

## Judge quick start

Open the public **Parallel Futures** evidence arena:
<https://nvm-star-max.github.io/GuardianSim/>

No account or sign-in is required. The main view renders the exact 18 × 256
formal outcome matrix and the `4,608 → 5 → 1` decision funnel. Judges can also
challenge three preserved decisions, inspect the Radeon scale path, and follow
displayed metrics to immutable evidence. The site replays published results;
it does not create new benchmark samples.

## Project overview

GuardianSim is a policy-agnostic safety layer for robot manipulation in
Genesis. Before a Franka arm executes a policy-proposed fruit-picking action,
GuardianSim restores a fingerprinted scene snapshot, evaluates bounded
counterfactual grasp actions through physical rollouts on an AMD Radeon GPU,
applies frozen hard safety gates, and either selects an eligible action or
explicitly stops.

The project addresses a practical failure mode: a robot can complete a grasp
while contacting nearby clutter or following an unnecessarily low-clearance
path. GuardianSim separates task completion from physical execution safety and
preserves an auditable decision report for every scenario.

## Verified result

The primary result comes from a frozen 30-scenario Gate 3.2 Genesis benchmark
with three independent physical executions per strategy and scenario:

| Metric | Nominal baseline | GuardianSim |
| --- | ---: | ---: |
| Repeatable safe scenarios | 18/30 | 30/30 |
| Independent safe executions | 58/90 | 90/90 |
| Sampled clutter-contact executions | 30 | 0 |
| Mean sampled clutter clearance | 23.191 mm | 46.003 mm |

Mean sampled clearance increased by **98.36%**. These are Genesis simulation
measurements, not physical-robot deployment claims.

## Formal decision-scale result

Safety Swarm V2 evaluated **18 candidate actions × 256 uncertainty worlds =
4,608 measured candidate-world pairs**. Five candidates passed all 256 worlds.
Frozen ranking selected
`yaw_-45.0_retreat_+0.000_approach_+0.140`, which recorded:

- **256/256** safe worlds;
- **0** sampled clutter contacts;
- **66.249 mm** worst-case sampled clearance;
- **66.304 mm** fifth-percentile sampled clearance;
- **0.907** minimum stability.

The run advanced **2,299,392** Genesis environment steps in **226.676 s**
(`10,143.979 environment-steps/s`). Radeon telemetry recorded **73.406% mean /
97% peak GPU utilization**. The 4,608 pairs are an engineering
candidate-by-uncertainty population, not independent robot trials.

## AMD Radeon GPU and ROCm

The preserved formal benchmark and evaluator smoke used:

- AMD Radeon Cloud, one `gfx1100` Radeon GPU;
- Genesis 1.2.3 with the `gs.amdgpu` backend;
- PyTorch `2.9.1+gitff65f5b`;
- HIP `7.2.53211-e1a6bc5663`;
- Python 3.12.3.

The Radeon GPU accelerates scene stepping and repeated physical
counterfactual rollouts. The repository includes the exact ROCm wheel
installer, dependency lock, GPU-required preflight, environment collector,
bounded real-Genesis smoke, and complete-source ROCm Dockerfile.

## Measured Radeon scale

A separate throughput suite ran one fixed headless Franka scene at four batch
sizes:

| Parallel worlds | Environment-steps/s | Speedup | Efficiency |
| ---: | ---: | ---: | ---: |
| 1 | 154.1 | 1.00x | 100.0% |
| 16 | 2,383.7 | 15.47x | 96.7% |
| 64 | 9,354.3 | 60.69x | 94.8% |
| 256 | 35,166.1 | 228.16x | 89.1% |

At 256 worlds, mean/peak GPU utilization was 85.5%/96%. The 337,000 timed
environment steps measure raw physics throughput, not safety trials. The
separate formal decision workload is reported in the preceding section and
keeps its candidate-world counts distinct from the Gate 3.2 safety benchmark.

## Innovation

1. **Safety layer rather than another task policy.** GuardianSim can wrap a
   nominal action supplied by a scripted or learned policy.
2. **Snapshot-safe comparison.** Every counterfactual begins from the same
   fingerprinted physical state.
3. **Hard eligibility before utility ranking.** A high utility score cannot
   compensate for a failed safety requirement.
4. **Repeatability-aware evidence.** Formal completion requires three
   independent safe executions.
5. **Explicit safe stop.** Unsupported geometry does not silently fall back to
   an unsafe nominal action.
6. **Auditable evidence.** Reports preserve decisions, physical measurements,
   responsible links and obstacles, protocol identities, logs, and checksums.

## Deliverables

- **Public interactive evidence arena:**
  <https://nvm-star-max.github.io/GuardianSim/>
- **Immutable source and evidence release:**
  <https://github.com/nvm-star-max/GuardianSim/tree/hackathon-2026-submission-v3>
- **Reproducibility guide:**
  <https://github.com/nvm-star-max/GuardianSim/blob/hackathon-2026-submission-v3/REPRODUCIBILITY.md>
- **Technical report:**
  [`GuardianSim-Technical-Report.pdf`](GuardianSim-Technical-Report.pdf)
- **Owner-approved 4:41 English demonstration video:**
  <https://raw.githubusercontent.com/nvm-star-max/GuardianSim/hackathon-2026-submission-v3/docs/submission/GuardianSim-Aegis-Motion-demo-review-v2.mp4>
- **80-second measured Radeon preview:**
  [`GuardianSim-Radeon-Parallel-Futures-preview.mp4`](GuardianSim-Radeon-Parallel-Futures-preview.mp4)
- **Raw Radeon scale and Parallel Futures reports:**
  [`evidence`](evidence)
- **Formal Safety Swarm V2 evidence:**
  <https://github.com/nvm-star-max/GuardianSim/tree/hackathon-2026-submission-v3/docs/evidence/safety-swarm-v2-formal-2026-07-30>
- **Immutable Gate 3.2 evidence:**
  <https://github.com/nvm-star-max/GuardianSim/tree/hackathon-2026-submission-v3/docs/evidence/gate-3-2>
- **Validated Gate 3.3 limitation evidence:**
  <https://github.com/nvm-star-max/GuardianSim/tree/hackathon-2026-submission-v3/docs/evidence/gate-3-3-two-strata>

## Reproduction

On the supported Radeon Cloud Blank OpenCode workspace:

```bash
git clone https://github.com/nvm-star-max/GuardianSim.git
cd GuardianSim
git checkout hackathon-2026-submission-v3

scripts/install_system_deps.sh
uv python install 3.12
export UV_PROJECT_ENVIRONMENT=/opt/venv
uv sync --frozen --python 3.12
scripts/install_rocm_stack.sh

./scripts/evaluator_preflight.sh
./scripts/run_evaluator_smoke.sh
```

The bounded smoke verifies source identity, Radeon/ROCm readiness, the real
Genesis scene, three counterfactual candidates from one captured snapshot,
strict preserved-report validation, and checksums. It checks that the
documented execution path is runnable; it is not used as the performance
benchmark.

## Responsible limitations

- All published evidence comes from Genesis simulation.
- No physical robot was tested.
- Sampled axis-aligned clearance is an engineering proxy, not a formal
  continuous-time collision proof.
- The action family is bounded and planning is not yet real-time.
- Harder unsupported geometry may produce a deliberate safe stop.
- The 30-scenario result applies only to the frozen Gate 3.2 matrix.
- The 4,608 Safety Swarm V2 pairs are candidate-by-uncertainty engineering
  evidence, not 4,608 independent robot trials.
- The scale suite measures steady-state Genesis stepping after warmup; scene
  construction is excluded.

## Team contribution

The solo developer `@nvm-star-max` completed project direction, system design,
implementation, Radeon Cloud experiments, evidence preservation,
reproducibility documentation, report production, and demonstration-video
production. AI-assisted development tools were used for implementation and
documentation support; the submitting team remains responsible for technical
validation, claims, licenses, and competition compliance.
