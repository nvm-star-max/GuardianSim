# GuardianSim Project Memory

Last updated: 2026-07-26

This file is the durable source of truth for continuing GuardianSim work across
machines and agent sessions. Update it after every verified milestone, cloud
session, architectural decision, or change to the competition plan.

## Mission

Build a competition-ready Physical AI demo that improves Franka pick-and-place
reliability by evaluating counterfactual grasp actions in Genesis, explaining
their risk, monitoring execution, and attempting bounded recovery.

The judge-facing claim must be supported by fixed-seed Genesis experiments on an
AMD Radeon GPU. Synthetic benchmark numbers are development smoke tests only.

## Current stage

**Gate 1 — Baseline: complete.**

Verified on Radeon Cloud:

- ROCm/HIP PyTorch sees one AMD Radeon GPU.
- Genesis builds and steps the retained Franka/YCB scene on the GPU.
- The scripted `011_banana -> 024_bowl` task succeeds.
- Eight reference-policy frames and two scene-probe frames were preserved.
- GuardianSim unit tests pass: 7/7.

Evidence: [`evidence/session-a/README.md`](evidence/session-a/README.md)

**Gate 2 — Counterfactual planning: cloud validation complete.**

The repository includes:

- a serializable episode snapshot and stable SHA-256 state fingerprint;
- a concrete `GenesisSceneDriver` that captures and restores Franka qpos and all
  YCB poses with dynamic velocity cleared;
- physical trace measurement for path length, retained lift, alignment, and
  sampled collision-AABB clearance;
- a real five-candidate Franka grasp-and-lift executor;
- an exact Session B dry-run command that emits ranked JSON;
- JSON-safe export for simulator/NumPy scalar and array-like values.

Verified in Radeon Cloud Session B:

- 14/14 tests passed.
- Genesis 1.2.3 ran on `gs.amdgpu` with 47.98 GB device memory.
- Five fixed-snapshot banana-grasp candidates executed and ranked.
- Exit code: `0`.
- The aligned `0°` candidate ranked first with predicted success `0.4648`.

Evidence: [`evidence/session-b/README.md`](evidence/session-b/README.md)

**Gate 2.5 — Metric calibration: cloud diagnostic complete.**

All five rollouts reported `collision_margin_m = 0.0`, so collision risk
dominates every score. The local diagnostic implementation now:

- records the responsible sample index, simulator step, Franka link, obstacle,
  support-surface flag, strict-overlap state, and AABB overlap depth;
- distinguishes exact AABB contact from strict overlap;
- evaluates the default Cartesian matrix of five yaw angles and three lateral
  offsets, for 15 candidates total;
- preserves the diagnostic alongside each candidate's scoring metrics.

The fixed-snapshot 15-candidate diagnostic completed successfully on Radeon
Cloud. All 15 critical pairs were `right_finger -> table_top`, with strict AABB
overlap depths between roughly 1.1 and 1.6 mm. The degenerate zero-clearance
metric is therefore caused by intentional support-surface contact, not proven
clutter collision.

Evidence:
[`evidence/gate-2-5/README.md`](evidence/gate-2-5/README.md)

The offset dimension is useful: every `-0.02 m` candidate retained zero lift and
ranked 11–15, while zero and positive offsets retained most of the requested
lift.

**Gate 2.6 — Two-channel safety metric: cloud validation complete.**

The recorder now separates support contact from clutter safety:

- clutter clearance excludes support surfaces and drives collision risk;
- support-contact overlap depth remains visible as a diagnostic;
- evidence schema version 3 preserves both critical pairs;
- cloud and local verification pass 17/17 tests;
- the 15-candidate cloud run measured `0.0354–0.0806 m` of non-support clutter
  clearance with no clutter overlap;
- `018_plum` is the measured critical clutter obstacle;
- intentional `right_finger -> table_top` overlap remains visible only in the
  support diagnostic;
- `yaw_-22.5_offset_+0.000` ranked first at estimated success `0.7327`.

The fixed-seed real benchmark implementation is complete locally. It performs
15-candidate counterfactual planning followed by independent baseline and
GuardianSim executions for each deterministic scene perturbation, and writes a
resumable JSON report after every episode. Resume requires the same configuration,
contiguous seeds, and matching rebuilt base-snapshot fingerprint. Local
verification passes 21/21 tests.

**Gate 2.7 — Twenty-episode benchmark complete; planner revision required.**

The paired seeds `101–120` completed with 20 unique episode fingerprints.
Baseline succeeded 20/20; GuardianSim succeeded 17/20. GuardianSim increased
mean clutter clearance by `0.03038 m` and improved clearance in every episode,
but reduced mean retained-lift stability by `0.13996`.

All failures were negative-offset selections on seeds 104, 107, and 120. Their
one-shot counterfactual success estimates were high (`0.70665–0.85040`), while
independent replay stability was zero. This demonstrates rollout-repeatability
risk rather than clutter collision.

Do not present the current planner as outperforming the nominal baseline. The
next gate is a predeclared robust-selection revision: repeated confirmation
rollouts, conservative stability aggregation, and nominal fallback. Preserve
Gate 2.7 unchanged as negative evidence.

Evidence:
[`evidence/gate-2-7/README.md`](evidence/gate-2-7/README.md)

**Gate 2.8 — Robust-selection benchmark complete.**

The fixed policy confirms the top-three initial candidates plus nominal with
two additional rollouts, aggregates metrics pessimistically, requires minimum
stability `0.60`, and requires a `0.02` robust-success advantage over nominal.
Otherwise it executes nominal.

The authorized smoke reruns for failure seeds 104, 107, and 120 all succeeded,
so the full paired benchmark was run without changing the predeclared policy.
Seeds `101–120` produced 20 unique episode fingerprints. Baseline and
GuardianSim both succeeded 20/20. GuardianSim increased mean clutter clearance
from `0.04399 m` to `0.07212 m` (`+63.93%`) while mean stability changed from
`0.90338` to `0.89731`.

Schema 3 records 240 confirmation observations. Nominal fallback activated once
and succeeded. Compared with Gate 2.7, GuardianSim success improved from 17/20
to 20/20 and mean stability improved by `0.13315`.

Evidence:
[`evidence/gate-2-8/README.md`](evidence/gate-2-8/README.md)

**Gate 3 — Judge-facing evidence showcase implemented locally.**

The showcase turns the preserved Gate 2.7 failure and Gate 2.8 recovery into an
interactive presentation without rerunning Genesis:

- evidence-first hero with 20/20 success and `+63.93%` mean clutter clearance;
- switchable failure → policy → proof narrative;
- verified benchmark cards, selection distribution, and recovered failure seeds;
- 90-second presenter mode;
- downloadable schema-3 report and cloud exit screenshot;
- explicit simulation-only claim boundary.

The standalone production build and rendered-content tests pass. The site is
contained in [`../showcase`](../showcase) and launches from the repository root
with `./scripts/run_showcase.sh`.

Sites version 1 is privately deployed at
<https://guardiansim-proof.dghcdtddgh.chatgpt.site>. Public access has not been
enabled; sharing it with judges requires an explicit owner decision.

**Gate 3.1 — Multi-object adversarial benchmark complete; primary result
negative.**

The predeclared 30-episode schema-4 benchmark completed on Radeon Cloud without
protocol or threshold changes. Baseline safe completion was 19/30; GuardianSim
safe completion was 18/30, an absolute difference of `-3.33` percentage points.
Ordinary task success was 20/30 versus 18/30.

GuardianSim increased mean clutter clearance from `0.02157 m` to `0.03099 m`
(`+43.67%`) but did not reduce clutter contact: both strategies contacted
clutter in 10/30 episodes. Mean stability decreased from `0.90845` to `0.85091`.

The failure is localized and actionable:

- lemon/lateral and plum/lateral produced 5/5 clutter contacts for both
  strategies, showing that the current yaw/lateral-offset action family cannot
  resolve those geometries;
- GuardianSim had unstable lifts on lemon/radial seed 318 and plum/radial seed
  326;
- nominal fallback activated in 19/30 episodes.

Do not claim that Gate 3.1 improved safety. Its verified contribution is a
reproducible generalization stress test demonstrating that average-clearance
optimization is insufficient.

Evidence:
[`evidence/gate-3-1/README.md`](evidence/gate-3-1/README.md)

## Verified environment

- Cloud template: Radeon Cloud Blank OpenCode Workspace
- Python: 3.12.3
- PyTorch: 2.9.1 (`gitff65f5b`)
- HIP: 7.2.53211
- `uv`: `/opt/venv/bin/uv`
- Compatible image stack:
  - `numpy>=1.26.4,<2.3`
  - `scikit-image>=0.25.2`

The NumPy upper bound is required by Numba. The newer scikit-image is required
to avoid a NumPy 2 ABI mismatch.

## Repository state

- Repository: <https://github.com/nvm-star-max/GuardianSim>
- Active evidence branch: `agent/gate-3-1-adversarial-benchmark`
- Latest verified evidence milestone commit: `2d8ea2f`
- Relevant commits:
  - `2119d0d` — Genesis evaluation and benchmark pipeline
  - `2283818` — compatible NumPy/scikit-image bounds
  - `64991a7` — Radeon Cloud Session A evidence
  - `1c17e90` — durable project memory and worklog
  - `c658a39` — snapshot-safe Genesis candidate rollouts
  - `d0017fd` — Gate 2 local milestone record
  - `004e47c` — JSON-safe simulator numeric export
  - `ae34c62` — Radeon Cloud Session B evidence and stage-gate record
  - `e6bfe2f` — named clearance diagnostics and 15-candidate matrix
  - `858a039` — Gate 2.5 Radeon Cloud evidence
  - `816cf9b` — Gate 2.7 benchmark evidence
  - `3c63236` — repeatability-aware robust selection
  - `2b3ffe1` — Gate 2.8 benchmark evidence and resume showcase
  - `e5ce9b8` — predeclared Gate 3.1 adversarial benchmark
  - `e68753a` — persisted-report validation fix
  - `bca798a` — Gate 3.1 smoke evidence
  - `2d8ea2f` — Gate 3.1 formal benchmark evidence

## Architecture already implemented

- Deterministic grasp-candidate generation.
- Simulator-independent candidate metrics and risk scoring.
- Failure diagnosis and bounded recovery planning.
- Baseline-vs-GuardianSim benchmark schema and CSV/JSON export.
- Lazy Genesis adapter boundary so local macOS tests do not import Genesis.

## Current execution route

Gate 3 packaging is implemented. The owner reviewed the competitive gap and
authorized Gate 3.1: a multi-object adversarial safety benchmark.

**Gate 3.1 is complete and fully validated. Its primary endpoint is negative,
so the current selector must not be presented as a general safety
improvement.**

- Frozen protocol hash:
  `472bb6ea13984dff02124c091ac8d94c67154bbe68858bb782aed8014d2afbba`.
- Frozen scenario-matrix hash:
  `b3ba08b367a0c634f66ddbba8670311c9b449aaa4ad7ee55d418bca7c2147936`.
- Matrix: three pick objects x two close-clutter layouts x five repeats = 30
  paired episodes, seeds `301–330`.
- Physical variation includes target XY/yaw, shared friction, and target mass.
- Primary endpoint is safe completion, requiring ordinary task success plus at
  least `0.010 m` sampled non-support clutter clearance.
- Ordinary task success, actual clutter contact, stability, clearance, failure
  type, and wall time remain separate secondary evidence.
- The Gate 2.8 robust-selection thresholds remain unchanged.
- Formal result:
  - baseline task success `20/30`, safe completion `19/30`;
  - GuardianSim task success `18/30`, safe completion `18/30`;
  - safe-completion difference `-3.33` percentage points;
  - mean clearance increased `43.67%`, but contacts remained `10/30` for both.
- The JSON round-trip validator mismatch was fixed in commit `e68753a`; protocol
  and scenario-matrix hashes did not change.
- Raw formal evidence:
  [`evidence/gate-3-1/README.md`](evidence/gate-3-1/README.md).
- Formal protocol:
  [`GATE_3_1_PROTOCOL.md`](GATE_3_1_PROTOCOL.md).

Next gate requires owner review. The recommended route is a separately
predeclared Gate 3.2 that expands the candidate action space with obstacle-aware
approach direction/height and strengthens execution-repeatability checks. Gate
3.1 must remain unchanged as negative evidence.

## Working agreement

- Maintain [`WORKLOG.md`](WORKLOG.md) as an append-only experiment log.
- Update this memory after verified changes or decisions.
- Work locally whenever GPU execution is not required.
- Before a major stage, stop and present:
  - what has been proven;
  - the proposed route;
  - major alternatives and tradeoffs;
  - the exit criteria and expected credit cost.
- Do not begin the next major stage until the route has been reviewed with the
  owner.
- Cloud-instance lifecycle follows the owner's latest explicit instruction.
  The current owner decision is to keep Session B running because the profile
  still shows zero credits consumed after an extended runtime.

## Cloud access and instance state

- A dedicated local ED25519 key was created at
  `~/.ssh/guardiansim_radeon_ed25519`.
- Only its public key was saved to Radeon Cloud.
- Key fingerprint:
  `SHA256:8VLTCjgZI8Ufo+CTDck01Zv8WUJMgPw9zTFa/FPF83Q`.
- The key applies only to future SSH-enabled templates that expose a host and
  port. Blank OpenCode did not display an SSH endpoint.
- Session A was destroyed after its evidence was secured.
- Session B instance `u-13907-735d71cb` is intentionally still running.
- At the latest verified profile check, the instance was ready, 10 credits were
  available, and 0 credits had been consumed despite an extended runtime.
