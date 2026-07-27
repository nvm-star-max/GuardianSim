# GuardianSim Project Plan

## Competition thesis

GuardianSim makes robot manipulation safer and more reliable by evaluating several
candidate actions before execution, monitoring task post-conditions during execution,
and applying bounded recovery actions after a failure.

The competition demo will use one AMD Radeon GPU on Radeon Cloud for:

1. Genesis physics simulation and parallel counterfactual rollouts.
2. Risk-model training and inference.
3. Closed-loop robot evaluation and video generation.

## MVP acceptance criteria

- Franka Panda completes a YCB-object pick-and-place task in Genesis.
- At least five grasp candidates are evaluated per scene.
- Candidate ranking exposes predicted success and risk.
- The system detects collision, missed grasp, slip, wrong placement, and timeout.
- Recovery is bounded to at most three attempts and ends in success or safe stop.
- Evaluation compares baseline and GuardianSim over at least 100 randomized episodes.
- Final artifacts include ROCm/GPU evidence, English report, reproducible README, and a 3–5 minute video.

## Experimental conditions

1. Nominal scene.
2. Partial target occlusion.
3. Low-friction object.
4. Object mass shift.
5. Camera extrinsic perturbation.
6. Target movement after planning.

## Primary metrics

- Task success rate.
- First-attempt success rate.
- Recovery success rate.
- Collision rate.
- Mean attempts per task.
- Mean planning and inference latency.
- Parallel-rollout throughput on AMD Radeon GPU.

## Stage gates

### Gate 1 — Baseline

Run the upstream Franka demo and save a rendered frame, GPU report, and baseline evaluation.

### Gate 2 — Counterfactual planning

Replace synthetic candidate metrics with measurements from cloned Genesis environments.

### Gate 3 — Learned risk

Generate labeled rollouts and train RiskNet to predict candidate success and failure modes.

### Gate 4 — Competition package

Run the full benchmark, record the Radeon Cloud demo, publish an upstream contribution,
and prepare the English submission.

The date-driven Gate 4 execution plan, official Track 3 deliverables, readiness
gaps, stop/go rules, and final checklist are maintained in
[`HACKATHON_SUBMISSION_PLAN.md`](HACKATHON_SUBMISSION_PLAN.md). Submission
engineering is now P0: after the currently authorized Gate 3.3 two-strata run,
no additional benchmark may displace clean-room reproduction, the English
technical report, or the 3–5 minute complete demo.
