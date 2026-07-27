# GuardianSim - Counterfactual Safety Certification for Robot Manipulation

**Track:** Track 3 - Physical AI Challenge

**Team:** Aegis Motion

**Team structure:** Solo developer, GitHub
[`@nvm-star-max`](https://github.com/nvm-star-max)

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

- **Immutable source and evidence commit:**
  <https://github.com/nvm-star-max/GuardianSim/tree/25e27aced13237b5af93fd91697d7abb12101a30>
- **Reproducibility guide:**
  <https://github.com/nvm-star-max/GuardianSim/blob/25e27aced13237b5af93fd91697d7abb12101a30/REPRODUCIBILITY.md>
- **Technical report:**
  [`GuardianSim-Technical-Report.pdf`](GuardianSim-Technical-Report.pdf)
- **Owner-approved 4:41 English demonstration video:**
  <https://raw.githubusercontent.com/nvm-star-max/GuardianSim/25e27aced13237b5af93fd91697d7abb12101a30/docs/submission/GuardianSim-Aegis-Motion-demo-review-v2.mp4>
- **Immutable Gate 3.2 evidence:**
  <https://github.com/nvm-star-max/GuardianSim/tree/25e27aced13237b5af93fd91697d7abb12101a30/docs/evidence/gate-3-2>
- **Validated Gate 3.3 limitation evidence:**
  <https://github.com/nvm-star-max/GuardianSim/tree/25e27aced13237b5af93fd91697d7abb12101a30/docs/evidence/gate-3-3-two-strata>

## Reproduction

On the supported Radeon Cloud Blank OpenCode workspace:

```bash
git clone https://github.com/nvm-star-max/GuardianSim.git
cd GuardianSim
git checkout 25e27aced13237b5af93fd91697d7abb12101a30

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
strict preserved-report validation, and checksums. It proves the documented
execution path; it is not used as the performance benchmark.

## Responsible limitations

- All published evidence comes from Genesis simulation.
- No physical robot was tested.
- Sampled axis-aligned clearance is an engineering proxy, not a formal
  continuous-time collision proof.
- The action family is bounded and planning is not yet real-time.
- Harder unsupported geometry may produce a deliberate safe stop.
- The 30-scenario result applies only to the frozen Gate 3.2 matrix.

## Team contribution

The solo developer `@nvm-star-max` completed project direction, system design,
implementation, Radeon Cloud experiments, evidence preservation,
reproducibility documentation, report production, and demonstration-video
production. AI-assisted development tools were used for implementation and
documentation support; the submitting team remains responsible for technical
validation, claims, licenses, and competition compliance.
