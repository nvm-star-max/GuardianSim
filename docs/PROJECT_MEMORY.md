# GuardianSim Project Memory

Last updated: 2026-07-27

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
- Latest verified evidence milestone commit: `5335f41`
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
  - `04e30c2` — Gate 3.1 durable memory update
  - `0530454` — predeclared Gate 3.2 repeatable-safety implementation
  - `12b90a8` — Gate 3.2 cloud smoke milestone record
  - `5335f41` — preserved and locally verified Gate 3.2 smoke evidence

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

**Gate 3.2 is complete. Its separately preserved engineering smoke and full
30-scenario Radeon Cloud formal report are schema-5-valid.**

- New untouched seeds: `401–430`.
- Frozen 18-action family: nine yaws from `-90°` to `90°`, with centered and
  `0.025 m` obstacle-retreating targets.
- Non-nominal pregrasp height: `0.14 m`.
- Safety-first shortlist hard-filters overlap, clearance below `0.010 m`,
  stability below `0.70`, and unreachable actions before ranking.
- Unsafe nominal cannot be used as fallback; choose a safe alternative or
  explicit safe-stop.
- Baseline and GuardianSim each receive three independent final executions;
  repeatable safe completion requires 3/3.
- Protocol SHA:
  `8f23247001e05f39817225ed13f028321fbb9b9c694aaacd5b987fe61ee1fb3c`.
- Matrix SHA:
  `69f87994b87f2def788cd944ad75210cdeddeafcaa3d0a3844fef04efca9cb03`.
- Formal protocol:
  [`GATE_3_2_PROTOCOL.md`](GATE_3_2_PROTOCOL.md).
- Smoke seeds `401–402` completed on the Radeon GPU:
  - both baseline and GuardianSim achieved `2/2` repeatable safe completion
    and zero clutter contacts;
  - mean clearance was `0.04797 m` for baseline and `0.09272 m` for
    GuardianSim;
  - mean stability was `0.90203` for baseline and `0.86074` for GuardianSim;
  - both episodes selected a `higher_margin_alternative`;
  - planning wall time was `269.55 s` and `266.57 s`;
  - all 18 initial metrics, four observations per confirmed candidate, and
    three final executions per strategy passed the partial schema-5 validator.
- These two smoke episodes are an engineering check only and must not be used
  as a competition performance claim.
- The raw cloud bundle was downloaded and its four-file SHA-256 manifest passed
  locally. The local schema-5 validator reproduced the cloud protocol,
  completed count, and full summary exactly; local tests passed 39/39.
- Preserved evidence:
  [`evidence/gate-3-2-smoke/README.md`](evidence/gate-3-2-smoke/README.md).

- Formal seeds `401–430` completed in one Radeon Cloud process:
  - baseline repeatable safe completion: `18/30` (`60%`);
  - GuardianSim repeatable safe completion: `30/30` (`100%`);
  - paired absolute lift: `+40.00` percentage points;
  - baseline clutter-contact executions: `30`; GuardianSim: `0`;
  - mean clearance: baseline `0.023191 m`, GuardianSim `0.046003 m`;
  - mean stability: baseline `0.892762`, GuardianSim `0.905099`;
  - GuardianSim decisions: 11 higher-margin alternatives, 10 unsafe-nominal
    replacements, and 9 eligible nominal fallbacks.
- The original smoke report was not appended across process initialization.
  Strict resume validation correctly rejected two attempts because Genesis
  produced a different base-scene snapshot fingerprint. Both rejection logs
  are preserved. The full formal result therefore used a separate output and
  ran all 30 scenarios in one process without `--fresh`.
- Strict complete schema-5 validation passed 30/30.
- Formal evidence archive SHA-256:
  `57b53cda9d4352cb2d99ae9da01e1051840705725002a9e32e4076493b7b84ad`.
- Preserved formal evidence:
  [`evidence/gate-3-2/README.md`](evidence/gate-3-2/README.md).

The judge-facing showcase and Chinese resume/interview package now use the
verified Gate 3.2 result. The interactive site presents the preserved Gate 3.1
failure, frozen Gate 3.2 method, formal outcome, explainable decision taxonomy,
recovered adversarial cells, and immutable evidence links. Its build, rendered
HTML tests, and lint checks pass. Private production version 2 is deployed at
<https://guardiansim-proof.dghcdtddgh.chatgpt.site>.

Next gate: owner review of the deployed presentation, followed by competition
submission copy and a short demo video plan. Do not start another cloud
benchmark or retune Gate 3.2 before that review.

The first judge-facing visual replay is now complete for Gate 3.2 seed 411.
It shows the nominal baseline and GuardianSim side by side from the same fresh
snapshot. Baseline contacted the plum obstacle at zero measured clearance;
GuardianSim executed the action recorded in the formal report and completed
safely with `0.017094 m` clearance. The replay is explicitly separate from the
formal statistical evidence. Its MP4 SHA-256 is
`a6b8fa20b924268955c7c40e002faf3b048f5de534f3c19a2ba071f0c7a4e3be`,
and the files are preserved under [`demo/README.md`](demo/README.md).

Gate 3.2's 30 paired scenarios are sufficient for the current frozen-matrix
hackathon proof, not a broad generalization claim. The primary sample size is
30 scenarios; three executions per strategy are nested repeatability checks.
The proposed next validation route is documented in
[`VALIDATION_SCALE_PLAN.md`](VALIDATION_SCALE_PLAN.md): owner review of the
video first, then a 24-scenario breadth smoke, followed only if justified by a
predeclared 120-scenario robustness gate. Do not start that next gate until the
owner reviews the actual replay and plan.

The recommended judge-facing video is now
[`demo/gate-3-2-seed-411-explained-v2.mp4`](demo/gate-3-2-seed-411-explained-v2.mp4),
not the original five-second MP4. It is an 18.1-second, 2560×1080 annotated
presentation derived only from the verified source replay. It marks the plum
obstacle, pauses the contact event, and explicitly contrasts:

- baseline: `0°` direct approach, `1.42 mm` overlap, `0 mm` clearance;
- GuardianSim: `+67.5°` rotated approach, no overlap, `17.09 mm` clearance.

The explained-video SHA-256 is
`2092b9604fa7d37ab9a67bfc9299258e74eb8d2362e9132e38b4e5d65573b6d7`.
Its sidecar records that physics was not re-executed and no statistical trial
was added. A separate fresh rerender produced only `4.26 mm` Guardian clearance
and was rejected rather than substituted, preserving the evidence boundary.

**Gate 3.3 is implemented locally and predeclared, but no cloud outcome has
been inspected.**

- Purpose: turn the single close-clutter demo into a multi-factor embodied
  safety system without changing Gate 3.2.
- Matrix: 24 new engineering-only scenarios, seeds `501–524`, covering pose
  shifts, gap/bearing changes, dynamics extremes, and perception bias.
- Every stratum covers three objects × two layouts.
- Planning uses biased perceived poses; Genesis execution uses the true scene.
- A per-candidate risk certificate subtracts the frozen target-plus-obstacle
  position-error bound from measured clearance before the existing safety
  selector may execute an action.
- Protocol SHA:
  `5f9497c363c32f8bbabb62e395d5814958e273d3b6d235fb46a7a5f23be6b130`.
- Matrix SHA:
  `c934f3427a937f2cc8594a1408e97d1ed9bf3692fa41af066f2fb8652435e983`.
- Protocol:
  [`GATE_3_3_PROTOCOL.md`](GATE_3_3_PROTOCOL.md).
- Owner approved the two-scenario cloud smoke after reviewing the route.
- The first launch executed scenario 501 physically but the schema-6 validator
  rejected the pre-serialization in-memory tuple/NumPy pose representation
  before writing any report. This is an engineering interface defect, not a
  physical outcome; the failure log must be preserved.
- The validator fix accepts numerically equivalent pre-serialization tuples
  and real-number scalars while retaining strict JSON validation. Protocol and
  matrix hashes remain unchanged.
- A second launch reached the same pre-write certificate comparison and exposed
  `numpy.bool_` normalization missing from that internal comparison. It also
  produced no report. The project-wide `json_default` adapter is now used for
  both pre-write and round-tripped certificate validation.
- The third launch on commit `5ec31f3` completed frozen seeds 501–502:
  - strict partial schema-6 validation passed 2/2;
  - baseline and GuardianSim both achieved 2/2 safe completion;
  - zero clutter contacts and no safe stops;
  - GuardianSim chose a higher-margin alternative twice;
  - mean clearance was `0.062413 m` baseline versus `0.090384 m`
    GuardianSim;
  - mean stability was `0.881576` baseline versus `0.879571` GuardianSim;
  - selected certified clearances after the frozen 4 mm uncertainty deduction
    were `0.090467 m` and `0.087469 m`;
  - no stop rule triggered.
- These are engineering-only outcomes and cannot be used as a robustness-rate
  claim.
- Downloaded evidence archive SHA-256:
  `f2040a53f4fbf2172a94df1003feac1137bcf4684bc9281d60f8991780da83ea`.
- Preserved evidence:
  [`evidence/gate-3-3-smoke/README.md`](evidence/gate-3-3-smoke/README.md).
- The owner then approved an independent, one-process run of the complete
  `pose_shift` stratum rather than attempting a cross-process resume.
- Cloud commit `dac822a` completed frozen seeds 501–506:
  - strict partial schema-6 validation passed 6/6;
  - frozen stop-reason list was empty;
  - baseline safe completion was 4/6 with clutter contact on the lateral lemon
    and lateral plum scenes;
  - GuardianSim safe completion was 6/6 with zero clutter contacts and zero
    safe stops;
  - absolute safe-completion lift was `+33.33` percentage points;
  - mean clearance was `0.026178 m` baseline versus `0.042806 m`
    GuardianSim;
  - mean stability was `0.908395` baseline versus `0.905240` GuardianSim;
  - the selector replaced the unsafe nominal action in both baseline-contact
    cases;
  - mean planning time was `230.48 s` per scenario.
- The cloud evidence archive and locally reconstructed archive matched:
  `fba1e73b1bce8da0079547a312b90389f14ce3f41ee631e99b3571f4ceae780c`.
- Evidence:
  [`evidence/gate-3-3-pose-shift-stratum/README.md`](evidence/gate-3-3-pose-shift-stratum/README.md).
- This is complete-stratum engineering evidence, not a robustness-rate claim.
  Seeds 507–524 remain unexecuted pending the next major-stage review.

## Official submission contract and current deadline

The organizer announcement received on 2026-07-27 states that the hackathon is
open and submissions close on **2026-08-06 at 23:59**. Treat the working
timezone as GMT+8 based on the previously displayed event calendar, but the
owner must manually confirm the exact deadline and timezone on Luma before the
internal freeze.

The authoritative requirement order is:

1. Luma Rules & Conditions:
   <https://luma.com/amd-4dhi?utm_source=CN>
2. Official contest repository:
   <https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07>
3. Organizer announcements and live Q&A.
4. Internal project documents.

The official Track 3 README requires an English technical report, dedicated
source repository, detailed reproduction README, and 3–5 minute complete
workflow video. A Docker image with all source and runtime components is
preferred. The final submission is made by forking the official contest
repository and opening an English pull request titled like
`Track 3, <Team Name>, GuardianSim`. All submission materials, descriptions,
and pull-request text must be English.

The live Radeon Cloud instance does not need to be submitted. Its environment
does: exact OS/image, GPU/ROCm/HIP/PyTorch/Python/Genesis versions, dependency
locks, setup scripts, assets/dataset provenance, preflight, execution commands,
expected outputs, checksums, and troubleshooting must be sufficient for an
evaluator to reproduce the result. The owner must still manually read the full
Luma Rules & Conditions because the page was not programmatically accessible.

The durable countdown and acceptance checklist are in
[`HACKATHON_SUBMISSION_PLAN.md`](HACKATHON_SUBMISSION_PLAN.md). Internal code
and evidence freeze is 2026-08-05 23:59 GMT+8, with a target submission time no
later than 2026-08-06 18:00 GMT+8.

## Gate 3.3 two-strata execution complete and priority decision

The independent continuous run of the first two complete Gate 3.3 strata
finished on Radeon Cloud instance `u-13907-735d71cb`. It ran seeds 501–512 from
zero in one process and did not splice the earlier six-scenario report.

- Strict cloud and local partial schema-6 validation passed 12/12.
- Frozen protocol and matrix hashes matched exactly.
- Stored and recomputed frozen `stop_reasons`: `[]`.
- Baseline produced:
  - 7 safe task completions from 12 executions;
  - 4 clutter-contact classifications;
  - 1 clearance violation;
  - mean clearance `0.019033 m`.
- GuardianSim produced:
  - 10 physical executions, all safe task completions;
  - 2 explicit safe stops;
  - zero clutter contacts and zero clearance-violating executions;
  - mean executed-action clearance `0.043547 m`.
- `pose_shift`: GuardianSim completed 6/6 with no stop or contact, versus
  baseline 4/6 with two contacts.
- `gap_bearing`: GuardianSim executed 4/4 safely and safe-stopped 2/6, versus
  baseline 3/6 safe completions, two contacts, and one clearance violation.
- The lateral lemon and plum `gap_bearing` cases had no action satisfying every
  frozen hard safety gate. Refusing execution is correct fail-safe behavior,
  but the isolated 2/6 safe-stop/task-noncompletion rate is a material
  action-space coverage limitation.
- The frozen implementation evaluates stop rates over the cumulative prefix:
  2/12 task noncompletions and 2/12 safe stops are each 16.67%, so the strict
  report correctly preserves an empty stop-reason list. The isolated
  `gap_bearing` diagnostic is recorded without rewriting the report.
- Mean planning wall time was `221.53 s` per scenario.

Both Seed 503 visual replay attempts were rejected by the hard claim-boundary
check. They reproduced the baseline contact but only `2.8406 mm` and
`3.0122 mm` GuardianSim clearance versus `24.0836 mm` in the formal stratum
report. Logs, PID files, and diagnostic JSON are preserved as replay
diagnostics, not videos or performance evidence.

Cloud and local evidence-archive SHA-256 matched:
`49ce9196de91f997f7233a4f4533e94292d0b502e8b2cc85fdbeac6173694595`.
All 14 raw-file checksums and local schema validation passed. Evidence:
[`evidence/gate-3-3-two-strata/README.md`](evidence/gate-3-3-two-strata/README.md).

Stop at this major-stage boundary. Do not automatically run
`dynamics_extreme`, `perception_bias`, or the proposed 120-scenario gate.
Submission engineering is P0. A future geometry-coverage change must use a new
declaration and cannot alter Gate 3.3.

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

## P0 evaluator reproduction engineering — first batch

On 2026-07-27, submission work replaced the implicit developer setup with an
evaluator-facing reproduction path:

- Added and committed a 132-package `uv.lock`; the previous Dockerfile
  referenced this file even though it did not exist, so a direct build would
  have failed before dependency installation.
- Added the English root `REPRODUCIBILITY.md` with:
  - supported Radeon Cloud and Docker targets;
  - exact native install commands;
  - GPU and non-GPU preflight paths;
  - a bounded real Genesis counterfactual smoke;
  - strict formal-report and checksum validation;
  - expected outputs, claim boundaries, and troubleshooting.
- Added a portable environment-manifest collector covering source revision,
  dirty state, OS, Python, tracked package versions, PyTorch/HIP, visible
  devices, `rocm-smi`, cloud template metadata, and explicit readiness checks.
- Added `scripts/evaluator_preflight.sh`:
  - GPU mode fails unless Linux, Python 3.12, ROCm PyTorch, and exactly one GPU
    are present;
  - `--no-gpu` mode validates source and preserved evidence without claiming
    ROCm proof;
  - outputs are recursively checksummed.
- Pinned every post-install evaluator invocation to
  `uv run --frozen --no-sync`. This prevents uv from reconciling the
  platform-independent lock after the exact ROCm wheels have intentionally
  replaced its default PyTorch distribution.
- Added `scripts/run_evaluator_smoke.sh`, which performs the GPU preflight,
  builds and renders the real Genesis scene, evaluates three yaw alternatives
  against one captured snapshot, validates the candidate report, and writes
  checksums. It is a bounded path proof, not a replacement performance claim.
- Updated the Dockerfile to use GuardianSim names and paths, include source,
  tests, scripts, and bundled assets, install the evaluator project, and run
  unit tests during the build. The optional upstream LeRobot training stack is
  excluded from the core evaluator image. The base remains
  `rocm/dev-ubuntu-24.04:7.2.1-complete`.
- Added concise formal-report output via `validate_gate32_report.py --compact`.
- Added tests for portable environment capture, candidate-smoke validation,
  and deterministic recursive checksum manifests.

Verified locally on macOS arm64:

- `uv lock --check` passed with 132 resolved packages.
- Bash syntax and Python byte-compilation passed.
- Unit tests passed `54/54`.
- The one-command non-GPU evaluator preflight passed.
- A post-commit `git clone --no-local` clean-room test created a new Python
  3.12 environment from only `uv.lock`, installed 80 runtime packages plus
  GuardianSim, reported a clean source tree, passed 54/54 tests, validated the
  formal report, and verified its generated preflight checksums.
- Gate 3.2 strict schema-5 validation passed 30/30 with the frozen protocol
  hash.
- All eight entries in `formal-sha256.txt` passed checksum verification.
- The local machine correctly reported `gpu_ready: false`; this is expected
  and proves that non-GPU mode does not masquerade as Radeon validation.

The Docker daemon was unavailable on the Mac, and macOS cannot expose
`/dev/kfd`; therefore a full container build plus real GPU smoke remains an
explicit Radeon Linux acceptance item. Do not mark that item complete based
only on this local batch.

## P0 evaluator reproduction engineering — Radeon acceptance

On 2026-07-27, the committed evaluator workflow was accepted on the retained
Radeon Cloud Blank OpenCode instance `u-13907-735d71cb` without destroying or
replacing it:

- Cloud source identity was exact commit
  `58a76d407a255f11d57bc401dcecb2604eafaca8` with a clean worktree.
- The image's working ROCm Python was `/opt/venv/bin/python`, although
  `VIRTUAL_ENV` was unset. A direct uv invocation would otherwise create an
  empty `.venv`. The evaluator scripts now detect and reuse `/opt/venv`.
- GPU-required preflight passed with Python 3.12.3, PyTorch
  `2.9.1+gitff65f5b`, HIP `7.2.53211-e1a6bc5663`, one AMD Radeon GPU, all
  54 tests from the tested commit, strict Gate 3.2 validation, and recursive
  checksum verification.
- The one-command real Genesis smoke built and rendered the Franka scene on
  `gs.amdgpu`, captured one physical snapshot, evaluated three yaw
  alternatives from that identical snapshot, and produced a strictly valid
  candidate report.
- Candidate validation recorded:
  - `validated: true`;
  - candidate count `3`;
  - snapshot fingerprint
    `8a3692e8f016af7602ecb54e6f4db1cde765ce232138c9e72f8939ca2c8e2ee2`;
  - top candidate `yaw_+00.0_offset_+0.000`.
- All 15 files in the smoke evidence directory passed the cloud checksum
  manifest. This is an evaluator-path proof only, not a performance result.
- The owner downloaded the 253 KB cloud archive through the normal Jupyter
  file browser. Local path-safety checks passed, the outer SHA-256 was
  `6457a20c7a1740eba2df5e62334a3f0c0bce55c4de4fface2675c9cd9861249c`,
  and all 16 root-manifest entries passed after extraction. The archive and
  expanded raw files are preserved under
  [`evidence/evaluator-smoke-58a76d4`](evidence/evaluator-smoke-58a76d4).
- Drafted the English Track 3 technical report and 4-minute demo-video script
  under [`submission`](submission). The team-attribution item recorded at that
  checkpoint was later resolved as Aegis Motion / solo `@nvm-star-max`. The
  video still requires one accepted Gate 3.2 comparison replay with exact,
  report-backed clearance overlays.
- Generated a six-page A4 review PDF with a reproducible ReportLab builder.
  All six pages were visually inspected after rendering to PNG; table
  contrast, wrapping, clipping, page numbers, draft labeling, and required
  Gate 3.2 metrics passed review. The original pending-attribution notice was
  later replaced with the verified public Aegis Motion identity.
- Final local acceptance for this batch passed shell syntax, `uv lock
  --check`, 55/55 unit tests, PDF compilation/text checks, whitespace checks,
  and a targeted secret/personal-email scan.

Do not start a new formal benchmark before the submission report and video are
reviewable. The next major stage is production of the accepted comparison
replay and final report/video assets.

## Submission identity and competitive position — 2026-07-27

- The owner selected **Aegis Motion** as the public solo-team name.
- The public contributor identity is GitHub `@nvm-star-max`. Do not invent a
  legal name; confirm whether Luma requires one in the public report.
- The intended official PR title is
  `Track 3, Aegis Motion, GuardianSim`.
- A same-day scan of all 37 official-repository PRs found four declared Track
  3 projects: NaviSense AI, 1bit.systems real-time NPU inference,
  G1D-Organize-Table, and the withdrawn-as-premature VisionPilot PR.
- G1D-Organize-Table is the strongest direct visual competitor because it
  demonstrates a real Unitree G1-D robot. VisionPilot may return with strong
  dataset, model, and throughput evidence.
- GuardianSim's defensible category is not another grasp policy or inference
  engine. It is a policy-agnostic, counterfactual execute-or-safe-stop
  assurance layer with frozen protocols, hard eligibility, independent
  executions, preserved negative results, and checksum-backed evidence.
- The largest remaining award risks are visual clarity and non-real-time
  planning (verified Gate 3.2 mean: `264.95 s/scenario`), not lack of another
  benchmark.
- Do not start a broader formal run solely to increase scenario count. The next
  P0 milestone is an accepted Gate 3.2 comparison replay followed by the final
  3–5 minute video.

Evidence and working material:

- [`submission/COMPETITOR_SCAN_2026-07-27.md`](submission/COMPETITOR_SCAN_2026-07-27.md)
- [`submission/OFFICIAL_PR_DRAFT.md`](submission/OFFICIAL_PR_DRAFT.md)
- [`submission/TECHNICAL_REPORT.md`](submission/TECHNICAL_REPORT.md)
- [`submission/DEMO_VIDEO_SCRIPT.md`](submission/DEMO_VIDEO_SCRIPT.md)

## Accepted Gate 3.2 hero clip — 2026-07-27

- The preserved Seed 411 source replay was accepted without another GPU run.
  It is the frozen `014_lemon-lateral_clutter-r01-s411` scenario:
  - formal baseline: three of three executions contacted clutter;
  - formal GuardianSim: three of three executions were safe;
  - replay baseline: `1.419 mm` measured plum overlap;
  - replay GuardianSim: `17.094 mm` measured plum clearance.
- Added an independent strict replay validator. It binds the complete schema-5
  report, protocol SHA-256, scenario identity, formal/replay candidate IDs,
  three-contact versus three-safe formal results, replay classifications,
  source video, presentation sidecar, and presentation video by SHA-256.
- Local tests now pass `58/58`.
- Generated
  [`demo/gate-3-2-seed-411-aegis-showcase-v3.mp4`](demo/gate-3-2-seed-411-aegis-showcase-v3.mp4):
  - 1920×1080, 20 FPS, 17.55 seconds;
  - branded Aegis Motion hook;
  - explicitly labeled top-down action-geometry illustration;
  - real Genesis side-by-side replay;
  - measured contact-frame pause;
  - single-replay and formal 30-scenario result cards;
  - SHA-256
    `38e9adfb2a3f2d90719b60449d092e4caca53afaa2b2f71fe1ade136357dff86`.
- The clip is presentation-only post-processing. It does not re-execute
  physics, add a statistical trial, or replace the immutable formal report.
- Do not spend GPU time re-recording Seed 411 unless the owner rejects the
  new visual. The next major stage is assembly of the complete 3–5 minute
  video around this accepted clip, including final-commit Radeon proof,
  evaluator-smoke footage, architecture, narration, safe-stop limitation, and
  repository close.
