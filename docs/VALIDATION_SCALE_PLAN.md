# GuardianSim Validation Scale Plan

Status: Stage 1 two-scenario engineering prefix complete; full 24-scenario
smoke awaits owner direction. This document does not alter the frozen Gate 3.2
protocol, thresholds, scenario order, report, or claims.

## Decision

Gate 3.2 is sufficient as a hackathon proof on its frozen test matrix, but it
is not sufficient for a broad generalization claim.

- The primary sample size is 30 paired scenarios, not 90 independent samples.
  The three executions per strategy are nested repeatability checks inside
  each scenario.
- GuardianSim improved 12 paired scenarios and regressed on none. The exact
  two-sided McNemar p-value is `0.000488`.
- A 30/30 rate still has a Wilson 95% confidence interval of approximately
  `88.65%–100%`. It does not prove a population success rate of 100%.
- The conclusion must remain: GuardianSim achieved 30/30 repeatable safe
  completion on the predeclared Gate 3.2 matrix in Genesis simulation on an AMD
  Radeon GPU.

## External scale references

- LIBERO implementations commonly evaluate 10 tasks with 50 rollouts per task,
  or 500 rollouts in total:
  [UniVLA](https://github.com/OpenDriveLab/UniVLA) and
  [LightVLA](https://github.com/LiAutoAD/LightVLA/blob/main/LIBERO.md).
- RoboCasa evaluates each task across 50 trials over five fixed scenes:
  [RoboCasa RSS 2024 paper](https://robocasa.ai/assets/robocasa_rss24.pdf).
  Its current leaderboard spans 50 tasks and three evaluation splits:
  [RoboCasa leaderboard](https://robocasa.ai/leaderboard.html).
- A ManiSkill real-robot PickCube demonstration reports 18/20:
  [ManiSkill demo gallery](https://maniskill.readthedocs.io/en/latest/user_guide/demos/gallery.html).
  This supports using 20–30 trials for a focused demonstration, not for a
  benchmark-wide claim.
- Recent benchmark analysis cautions that fixed-suite improvements can be
  statistically fragile or exploit benchmark shortcuts:
  [What Are We Actually Benchmarking in Robot Manipulation?](https://arxiv.org/abs/2606.04233).

## Staged validation plan

### Stage 0 — Visual proof now

Purpose: let judges and the owner inspect the physical behavior before more
compute is spent.

- Replay a verified Gate 3.2 recovery case from a fresh scene process.
- Show the nominal baseline and GuardianSim side by side from the same initial
  snapshot.
- Overlay the selected action, clearance, stability, and final safety class.
- Preserve an MP4 and JSON sidecar.
- Label it as a visual replay, not as additional formal benchmark evidence.

Exit criteria:

- video decodes successfully;
- baseline and GuardianSim panels use the frozen scenario configuration;
- GuardianSim uses the candidate recorded in the formal report;
- replay metadata and file checksum are preserved.

### Stage 1 — Breadth smoke

Purpose: cheaply detect whether the current action family collapses outside the
Gate 3.2 geometry before launching a formal run.

- 24 engineering-only scenarios.
- New seeds and no overlap with Gate 3.1 or Gate 3.2.
- Stratify four perturbation families:
  1. target-position and yaw shifts;
  2. tighter/wider clutter gaps and changed obstacle bearing;
  3. friction and target-mass extremes;
  4. perception noise and pose bias.
- Use one execution per strategy during smoke; do not report these outcomes as
  final performance.
- Freeze the Stage 2 matrix only after implementation defects found by this
  smoke are resolved.

Stop conditions:

- any snapshot mismatch or validator failure;
- more than 25% GuardianSim task failures;
- any unexplained collision regression;
- more than 20% scenarios with no representable hard-safe candidate.

Expected compute:

- approximately 2–4 GPU hours after reusing cached/static action analysis;
- do not proceed automatically to Stage 2.

Implementation status:

- Frozen as Gate 3.3 schema 6 in
  [`GATE_3_3_PROTOCOL.md`](GATE_3_3_PROTOCOL.md).
- Protocol SHA-256:
  `5f9497c363c32f8bbabb62e395d5814958e273d3b6d235fb46a7a5f23be6b130`.
- Matrix SHA-256:
  `c934f3427a937f2cc8594a1408e97d1ed9bf3692fa41af066f2fb8652435e983`.
- Adds true/perceived-pose separation and a per-candidate uncertainty
  certificate.
- Seeds 501–502 passed the engineering prefix and strict partial validator with
  no stop reason. Evidence:
  [`evidence/gate-3-3-smoke/README.md`](evidence/gate-3-3-smoke/README.md).
- The independent complete `pose_shift` stratum (seeds 501–506) passed strict
  partial schema-6 validation with no stop reason. Baseline safe completion was
  4/6 with two lateral-clutter contacts; GuardianSim completed 6/6 with zero
  contacts and zero safe stops. Evidence:
  [`evidence/gate-3-3-pose-shift-stratum/README.md`](evidence/gate-3-3-pose-shift-stratum/README.md).
- A separate continuous 12-scenario run completed `pose_shift` and
  `gap_bearing`, seeds 501–512. GuardianSim made ten safe task executions and
  two explicit safe stops with zero contacts; baseline produced seven safe
  completions, four contacts, and one clearance violation. Strict schema-6
  validation passed and the cumulative frozen stop-reason list was empty.
- The isolated `gap_bearing` stratum had two safe stops in six scenarios.
  Its `33.33%` task-noncompletion and no-hard-safe-action rates expose an
  action-space coverage limitation even though the cumulative 12-scenario
  rates remain below the stored stop thresholds. Evidence:
  [`evidence/gate-3-3-two-strata/README.md`](evidence/gate-3-3-two-strata/README.md).
- Do not run the remaining `dynamics_extreme` or `perception_bias` strata
  before the submission package is complete. Do not proceed to Stage 2 under
  the current action family.

### Stage 2 — Hackathon robustness gate

Purpose: support a defensible robustness claim while remaining feasible on the
available cloud instance.

- 120 new paired scenario units:
  - 3 target objects;
  - 2 clutter-layout families;
  - 4 perturbation strata;
  - 5 new seeds per cell.
- Three independent final executions per strategy:
  360 baseline and 360 GuardianSim executions.
- One predeclared formal run with a new immutable protocol hash and matrix hash.
- Keep all Gate 3.2 data out of the Stage 2 estimator.

Primary endpoint:

- paired difference in scenario-level repeatable safe completion.

Secondary endpoints:

- clutter-contact executions;
- repeatable task completion;
- safe-stop frequency and correctness;
- 10th percentile, median, and mean clearance;
- retained-lift stability;
- planning and execution latency;
- results split by object, layout, and perturbation stratum.

Predeclared pass criteria:

- at least `+15` percentage points absolute repeatable-safe-completion lift;
- lower bound of the paired 95% confidence interval above zero;
- at least 50% fewer clutter-contact executions;
- GuardianSim repeatable task completion no more than 5 percentage points below
  baseline;
- no hidden threshold or scenario edits after the first formal outcome is
  observed.

Compute warning:

- Gate 3.2 planning averaged `264.95 s` per scenario.
- A naive 120-scenario run would require about 8.8 hours for planning alone,
  before final executions and validation.
- Stage 2 therefore requires profiling and a correctness-preserving cache or
  batched rollout design before launch. Speed changes must be validated against
  the original selector on a predeclared parity set.
- The 12-scenario Gate 3.3 run averaged `221.53 s` of planning per scenario
  and still exposed two no-hard-safe-action cases. Before any Stage 2 launch,
  expand the representable approach family for tight lateral lemon/plum
  geometry and preserve safe-stop semantics. This must be a new declaration,
  not a retune of Gate 3.3.

### Stage 3 — Public-benchmark adapter

Purpose: make the result comparable with work outside this repository.

Preferred order:

1. ManiSkill manipulation task subset for the fastest integration;
2. LIBERO subset with 5–10 tasks and 50 rollouts per task;
3. RoboCasa only after the policy interface and compute budget are stable.

Minimum target:

- 5 held-out tasks × 50 rollouts = 250 task trials;
- report per-task means, confidence intervals, and aggregate results;
- preserve benchmark-native success criteria alongside GuardianSim safety
  metrics.

This stage is separate from the hackathon submission and should not block the
current demo.

### Stage 4 — Real-robot evidence

Purpose: test the simulator-to-reality claim.

- 2–3 tasks;
- 20–30 uncut trials per task;
- fixed camera and safety observer;
- report interventions, contacts, task success, and safe stops;
- publish failures and full-length representative videos.

No real-robot claim is permitted before this stage.

## Submission claim boundary

Allowed:

> On a predeclared 30-scenario adversarial Genesis matrix, GuardianSim improved
> repeatable safe completion from 18/30 to 30/30 and reduced clutter-contact
> executions from 30 to 0 on an AMD Radeon GPU.

Not allowed:

- “100% safe in general”;
- “solves robotic grasping”;
- “validated in the real world”;
- treating 90 nested executions as 90 independent scenarios;
- merging visual replay outcomes into the frozen formal report.
