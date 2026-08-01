# GuardianSim Project Memory

Last updated: 2026-07-31

This file is the durable source of truth for continuing GuardianSim work across
machines and agent sessions. Update it after every verified milestone, cloud
session, architectural decision, or change to the competition plan.

## Mission

Build a competition-ready Physical AI demo that improves Franka pick-and-place
reliability by evaluating counterfactual grasp actions in Genesis, explaining
their risk, monitoring execution, and attempting bounded recovery.

The judge-facing claim must be supported by fixed-seed Genesis experiments on an
AMD Radeon GPU. Synthetic benchmark numbers are development smoke tests only.

## Writing and presentation standard

- Write like the engineer who ran the experiment: state what was run, what was
  measured, what changed, and what remains unproven.
- Prefer short concrete sentences and first-person explanations where useful.
- Avoid stacked slogans, inflated transitions, generic superlatives, rhetorical
  questions, and phrases such as “redefine,” “unlock,” “revolutionize,” or
  “formal proof” when the evidence is a bounded simulation result.
- Keep one strong hook only when it helps a judge understand the project
  quickly; the body copy must return to plain technical language.
- Never trade precision for a more dramatic claim. Preserve the distinction
  between throughput worlds, simulated futures, formal scenarios, and
  physical-robot evidence.

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
- Latest accepted hero-video milestone commit: `25c6c37`
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

## Narrated 4:15 submission-video review cut — 2026-07-27

- Generated
  [`submission/GuardianSim-Aegis-Motion-demo-review-v1.mp4`](submission/GuardianSim-Aegis-Motion-demo-review-v1.mp4):
  - 1920×1080, 20 FPS, 4 minutes 15.4 seconds;
  - English Samantha narration and burned-in English captions;
  - eight chapters covering the problem, AMD Radeon evidence, architecture,
    evaluator smoke, accepted physical replay, Gate 3.2 formal result,
    Gate 3.3 safe-stop limitation, and repository close;
  - output SHA-256
    `5abebe2ce3727a5404df70b814765b5d6978dea47b6b265816eb982ad6d0d262`.
- The review cut is presentation-only. It does not re-run Genesis or add a
  benchmark trial.
- Formal claims remain exclusively bound to the complete Gate 3.2 schema-5
  report: `18/30 → 30/30` repeatable safe scenarios, `58/90 → 90/90`
  independent safe executions, `30 → 0` clutter-contact executions, and
  `23.191 → 46.003 mm` mean sampled clearance.
- The Seed 411 hero section retains the validated `1.419 mm` baseline overlap,
  `17.094 mm` GuardianSim clearance, and formal `0/3 → 3/3` safe-execution
  contrast.
- Gate 3.3 appears only as separately labeled engineering breadth evidence:
  four safe executions, two explicit safe stops, and zero unsafe executions
  in the six-case gap/bearing stratum.
- Strict validation passed:
  - duration inside the required 3–5 minute range;
  - 1920×1080 at 20 FPS;
  - full H.264/AAC decode;
  - seven time-distributed sample decodes;
  - source SHA-256 identity;
  - formal-metric and claim-boundary checks;
  - QR decoding to the public GuardianSim repository.
- High-resolution inspection found the real replay's bottom measurement line
  was initially obstructed by subtitles. The replay subtitles were moved to
  the top information area and the video was rebuilt and revalidated.
- This is a review cut, not the final upload. Before final approval, the owner
  should assess pacing, synthetic narration, and whether to replace the
  archived Radeon-terminal presentation with a real-time final-commit screen
  recording. The cloud instance remains untouched.

## Qwen-narrated fixed-caption V2 review cut — 2026-07-28

- The owner rejected the sentence-by-sentence changing captions and the
  mechanical macOS Samantha narration in V1.
- Added a dependency-free Qwen3-TTS client at `scripts/qwen_tts.py`:
  - model `qwen3-tts-instruct-flash-2026-01-26`;
  - built-in `Ethan` voice;
  - English instruction control for a calm, warm, conversational robotics
    engineer presentation;
  - sentence-boundary splitting below the API character limit;
  - content-addressed local chunk caching;
  - PCM WAV concatenation with short natural pauses;
  - credential loading only from `DASHSCOPE_API_KEY` or the Git-ignored
    `.env.local`.
- The user-supplied credential is stored locally with mode `600`; it is not in
  source control, logs, sidecars, checksums, or generated documentation.
  Rotate it after the submission-video work because it was originally shared
  in chat.
- Replaced dynamic narration captions with eight fixed evidence captions that
  change only at chapter boundaries.
- Generated
  [`submission/GuardianSim-Aegis-Motion-demo-review-v2.mp4`](submission/GuardianSim-Aegis-Motion-demo-review-v2.mp4):
  - 1920×1080, 20 FPS, 4 minutes 41.5 seconds;
  - Qwen3-TTS Instruct English narration;
  - H.264 video and AAC audio;
  - loudness-normalized audio measured at mean `-17.5 dB`, maximum `-1.2 dB`;
  - SHA-256
    `e235a315cf4370ccd10cce5f50d317a7ec3376725940235482b530a641804888`.
- Strict V2 validation passed full A/V decode, seven distributed frame
  decodes, 3–5 minute duration, source identities, formal claims, simulation
  boundary, narration provider/model/voice, fixed-caption policy, and
  per-segment audio hashes. The closing QR code decoded to the public
  GuardianSim repository.
- Local tests pass `61/61`.
- No cloud command, physics run, benchmark trial, protocol, threshold, formal
  report, or Radeon Cloud instance changed.
- On 2026-07-28, the owner approved this exact V2 cut with the instruction
  “就这个版本吧.” It is now the frozen submission-video artifact. Do not alter
  its narration, fixed captions, timing, metrics, or evidence claims without a
  new explicit owner decision. Uploading/submitting it remains a separate
  external action.

## Final technical report and official-repository package — 2026-07-28

- Generated and visually inspected the final English six-page A4 report:
  [`submission/GuardianSim-Technical-Report.pdf`](submission/GuardianSim-Technical-Report.pdf).
  It covers the target application, architecture, evaluation matrix, Radeon
  and ROCm use, innovation, deliverables, responsible limitations, and the
  solo Aegis Motion contribution. SHA-256:
  `d4d5596645c4f971280f779eb585d0e675b62695d5f114db72dbbbf398054a66`.
- Corrected the report's statistical boundary: the declared scenarios are not
  described as a learned-policy holdout because the wrapped nominal policy is
  scripted. The strict validator is described as validating the complete
  30-episode report and frozen protocol identity, not as re-running physics.
- Prepared the English organizer-repository payload under
  [`submission/official-package/Track3-Aegis-Motion-GuardianSim`](submission/official-package/Track3-Aegis-Motion-GuardianSim).
  It contains the project entry, final PDF, and an internal checksum manifest.
  The package README SHA-256 is
  `f37cc735292d6f5502d2aeef778d97f16b68942701a467fd57967f11ef792ec4`.
- Verified that the immutable source tree and frozen video URLs at commit
  `25e27aced13237b5af93fd91697d7abb12101a30` both return HTTP 200. This commit
  remains the evidence and video source identity used by the report and
  official package.
- The local Docker client is installed, but its daemon is unavailable and
  macOS cannot provide the ROCm `/dev/kfd` device. Therefore no local
  Radeon-container execution is claimed. The pinned complete-source
  Dockerfile remains optional packaging, while the documented native Radeon
  Cloud path is the verified reproduction route.
- Final local acceptance passed: `ruff` reported no issues in the report/video
  tooling, the full suite passed `61/61`, strict V2 video validation passed,
  both checksum manifests passed, the two packaged PDF copies are byte
  identical, and tracked-file secret-pattern scanning found zero hits.
- Public-release boundary:
  - `origin/main` is an ancestor of the feature branch, so a fast-forward
    release remains available;
  - the owner's official contest fork
    `nvm-star-max/Radeon-hackathon-2026-07` does not yet exist;
  - the owner authorized release preparation after the rules review, so the
    public default branch and official fork may be prepared;
  - do not open the organizer pull request until the owner accepts the
    personal eligibility and legal terms recorded below.

## Official Rules and Conditions review — 2026-07-28

- Retrieved the 15-page governing document directly from the Google Docs link
  on Luma and recorded the source, retrieval hash, technical requirements,
  eligibility provisions, prize/payment terms, and legal effects in
  [`submission/RULES_REVIEW_2026-07-28.md`](submission/RULES_REVIEW_2026-07-28.md).
- The public report and pull request do not need the legal name. The legal name
  is required in the private Luma registration. Public materials can continue
  to identify the solo entry as **Aegis Motion** / `@nvm-star-max`.
- GuardianSim meets the technical package requirements: Track 3 simulation,
  one Radeon GPU and ROCm, Genesis, English report and repository, detailed
  reproduction instructions, optional Docker packaging, and a 4:41.5 workflow
  video. Qwen TTS is presentation-only and is not a core project function.
- Personal facts remain outside repository verification: legal-name
  registration, age/majority, sanctions/export-control and employment
  eligibility, valid Discord ID, and Luma team-name consistency.
- Opening the organizer pull request constitutes the competition entry. Do not
  perform that final action until the owner accepts the broad entry license,
  publicity/release provisions, possible winner forms, and tax obligations
  summarized in the rules review.

## Public release and organizer-fork preparation — 2026-07-28

- Fast-forwarded `nvm-star-max/GuardianSim` public `main` to release payload
  commit `1059d0d5af402a20fe01ea190951d3abb27faef8`.
- Created and pushed annotated tag `hackathon-2026-submission-v1` for the
  frozen release payload.
- Created the official contest fork:
  <https://github.com/nvm-star-max/Radeon-hackathon-2026-07>.
- Created and pushed branch
  `submission/track3-aegis-motion-guardiansim` at
  `abd0cfd72056eefe94298f513449e4f48842620b`.
- Copied the prepared package to
  `submissions/Track3-Aegis-Motion-GuardianSim`, verified both package
  checksums, and added a path-scoped `.gitattributes` rule so the PDF is
  represented as a binary artifact in the organizer diff.
- No organizer pull request exists yet. The exact prepared PR title remains
  `Track 3, Aegis Motion, GuardianSim`.

## Final organizer submission — 2026-07-28

- The owner explicitly confirmed the personal eligibility and legal terms
  summarized from the official Rules and Conditions and authorized final
  submission.
- Opened official pull request
  <https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/39>
  with title `Track 3, Aegis Motion, GuardianSim`.
- Verified the PR is open, non-draft, mergeable, targets official `main`, and
  uses head branch `nvm-star-max:submission/track3-aegis-motion-guardiansim`
  at `abd0cfd72056eefe94298f513449e4f48842620b`.
- Verified the comparison contains exactly the path-scoped binary attribute,
  English submission README, final technical-report PDF, and checksum
  manifest.
- Verified every immutable source, video, evidence, and Docker/reproduction
  link in the PR body returned HTTP 200.
- The durable non-private record is
  [`submission/FINAL_SUBMISSION_2026-07-28.md`](submission/FINAL_SUBMISSION_2026-07-28.md).
  Do not change the PR's frozen quantitative claims unless a factual
  correction is required.

## P0 award strategy and Parallel Futures showcase — 2026-07-28

- The owner reprioritized post-submission work:
  - **P0:** a judge-facing wow hook;
  - **P1:** a useful upstream Genesis/ROCm contribution;
  - **P3:** ordinary slogan and copy refinement.
- Implemented **GuardianSim: Parallel Futures**, an interactive safety time
  machine under `showcase/`. A judge chooses among three candidate actions,
  reveals verified counterfactual outcomes, and can download an evidence
  receipt containing immutable report identity and the simulation-only claim
  boundary.
- The three challenges use only preserved evidence:
  - Gate 3.2 Seed 411 collision trap;
  - Gate 3.2 Seed 401 high-clearance but unstable decoy;
  - Gate 3.3 Seed 509 impossible gap ending in a safe stop.
- The interaction does not alter or regenerate any frozen benchmark report.
  Gate 3.2 aggregate values remain `18/30 -> 30/30` repeatable-safe scenarios,
  `58/90 -> 90/90` independent safe executions, `30 -> 0` clutter contacts,
  and `23.191 -> 46.003 mm` mean sampled clearance.
- Added a dedicated Seed 411 replay asset and a generated 1200×630 social
  card showing one robot branching into red, amber, and green futures.
- Local acceptance before deployment:
  - showcase rendered-HTML and evidence cross-check tests passed;
  - showcase lint passed;
  - production build passed.
- Sites production version **3** deployed successfully at
  <https://guardiansim-proof.dghcdtddgh.chatgpt.site>.
  - GitHub feature commit:
    `e566b69848a4ffc79168ac39087d6c86c9ac897b`;
  - Sites source commit:
    `a8bf2af3b7a367c0e5b07960028b9ee58e9156f3`.
- Access remains owner-only. Public judge access is not enabled without a
  separate access-control decision.

## Evidence-scale correction and Gate 4 draft — 2026-07-28

- The owner requested further improvement before any merge or public push,
  specifically because competitor materials contain visually large
  hundreds/thousands-scale numbers. Do not push or launch Gate 4 without a new
  explicit checkpoint.
- Audited the preserved reports at the correct statistical grain:
  - 42 independent scene units: 30 formal Gate 3.2 + 12 engineering Gate 3.3;
  - 1,185 counterfactual candidate rollouts;
  - 202 final baseline/GuardianSim executions;
  - 1,387 total simulated action traces.
- These are not 1,387 independent trials. The site is being revised locally
  to present both the scene count and nested trace count together.
- Public Track 3 audit found that G1D's prominent 30,000 number is training
  steps, while NaviSense and 1bit emphasize tokens/s and latency. Their public
  materials do not establish thousands of independent robot evaluation
  scenes. Preserve this apples-to-apples distinction.
- Implemented an outcome-blind Gate 4 draft:
  - 240 new paired scenes, seeds 1001–1240;
  - four balanced 60-scene perturbation shards;
  - three final repeats per strategy, 1,440 planned final executions;
  - original 18 candidates first, then a frozen adaptive expansion to at most
    36 candidates only when the base family has no hard-safe action;
  - up to 14,400 nested simulated action traces;
  - exact McNemar primary test and unchanged safety thresholds.
- Draft protocol hash:
  `b20494f26fad7574d8c59e3a8393563bd44d49432edcae21e76d6dc46375300d`.
- Draft matrix hash:
  `4d96a2125a2744df96add7e2633e6011221908f492827e89bae5bee8d25c051c`.
- This is not yet a formal Gate 4 claim. Required next gates are parity,
  diagnostic replay, two-scenario schema smoke, runtime profiling, and owner
  review before Radeon launch.

## Radeon parallel-compute presentation layer — 2026-07-29

- The owner asked for a visible demonstration of large-scale computation and
  AMD Radeon GPU strength.
- Preserve two separate evidence grains:
  - GuardianSim safety effectiveness: independent paired scenes, candidate
    rollouts, and final executions;
  - Radeon compute capability: batched Genesis physics throughput.
- Existing `build_scene(n_envs=...)` genuinely builds batched Genesis worlds,
  but the complete GuardianSim grasp/candidate execution path still contains
  single-environment helpers. Do not claim that the current GuardianSim
  candidate futures are already evaluated as one GPU batch.
- Added a local Radeon scaling benchmark protocol for `1 / 16 / 64 / 256`
  headless Franka worlds, with 100 warmup steps and 1,000 measured steps per
  trial. The planned timed workload is 337,000 environment steps.
- Every batch size runs in a fresh process. Build/JIT time is recorded but
  excluded from steady-state throughput. HIP synchronization brackets the
  timed region and `rocm-smi` is sampled for utilization and VRAM.
- Strict validation rejects protocol drift, missing batches, non-AMD/HIP
  execution, missing telemetry, and inconsistent derived metrics.
- The local showcase now contains a clearly labeled 256-world scale-lab
  placeholder. It says measurement is pending and explicitly states that
  337,000 environment steps are not independent safety trials.
- No Radeon result exists yet; no throughput/speedup/utilization value may be
  published until the cloud report passes strict validation. No commit, push,
  public deployment, or official PR update has been made.

## Radeon inference and parallel-futures execution layer — 2026-07-29

- The judge-facing product position is now:
  **One Radeon GPU. Hundreds of robot futures. One safe decision.**
- This is a zero-configuration presentation path. A judge should watch the
  autoplay proof or page and inspect already-preserved evidence; judging must
  not depend on training a model, operating an API, or provisioning a runtime.
- Added a scene-held-out Safety Critic dataset and benchmark:
  - all `1,185` unique preserved candidate rollouts from `42` scene units;
  - `34` train scenes / `8` held-out test scenes, with no scene leakage;
  - `571` hard-safe positive rows;
  - fixed 28-feature schema;
  - multi-task MLP predicting a hard-safe logit plus clearance, stability, and
    path length;
  - ROCm batch-inference matrix
    `1 / 18 / 54 / 108 / 256 / 1,024 / 4,096`;
  - predeclared showcase quality gates: held-out hard-safe F1 `>= 0.80` and
    unsafe precision `>= 0.90`.
- The Safety Critic is an advisory prefilter only. The existing deterministic
  hard physics verifier remains authoritative. Do not describe the model as a
  formal safety guarantee or use inference throughput as independent-scene
  evidence.
- Added a real batched candidate-futures runner:
  - `18` obstacle-aware candidate actions × `3` repeats;
  - `54` simultaneous Genesis environments;
  - batched IK, GPU-resident controls, and vectorized AABB clearance;
  - unchanged Gate 3.2 hard-safety boundary;
  - preflight protocol written before execution and strict post-run report
    validation.
- Local acceptance passed `82/82` tests plus targeted Ruff and diff checks.
- Cloud measurements remain pending because no active Radeon/Jupyter tab is
  currently available in the connected Chrome session. Do not publish model
  quality, inference throughput, 54-future throughput, utilization, VRAM, or
  physics speedup until the corresponding Radeon reports pass validation.
- No commit, push, deployment, official PR update, or frozen-report mutation
  was made in this stage.

## Radeon P0 execution and evidence acceptance — 2026-07-29

- Reused Radeon Cloud instance `u-13907-735d71cb` without destroying it.
  The instance had recycled its ephemeral root workspace, so the repository
  was restored under `/workspace/persistent/GuardianSim`.
- Verified the execution environment before measurement:
  - PyTorch `2.9.1+gitff65f5b`;
  - HIP `7.2.53211-e1a6bc5663`;
  - Genesis `1.2.3`;
  - one visible `AMD Radeon Graphics` device.
- The first scale attempt failed before measurement because the fresh instance
  lacked Genesis. Both diagnostic logs were preserved. Installing the project
  into the existing ROCm `/opt/venv` fixed the environment without replacing
  the ROCm PyTorch build.
- The frozen Radeon scale matrix passed strict schema-1 validation:
  - `1` world: `154.1 env-steps/s`;
  - `16` worlds: `2,383.7 env-steps/s`, `15.47×`, `96.7%` efficiency;
  - `64` worlds: `9,354.3 env-steps/s`, `60.69×`, `94.8%` efficiency;
  - `256` worlds: `35,166.1 env-steps/s`, `228.16×`, `89.1%` efficiency;
  - all points reached `96%` peak GPU use;
  - 256-world mean GPU use `85.5%`, peak VRAM `1.34 GiB`;
  - total timed workload `337,000` environment steps.
- Scale protocol SHA-256:
  `4944cd288c1a855414c987e4229e1488498e56cd61e4d45136c62f3fb98d7603`.
- Scale report SHA-256:
  `a372727b5280ca6be9e58ca6ab82b01899ed24eaa45c8df39359aab83dfe539e`.
- The 54-way Parallel Futures engineering run passed strict validation:
  - `18` candidates × `3` repeats = `54` simultaneous worlds;
  - batched wall time `12.839 s`, throughput `4.206 futures/s`;
  - `32` hard-safe futures and `22` rejected futures;
  - mean/peak GPU use `71.8% / 95%`, peak VRAM `1.13 GiB`.
- Parallel Futures protocol SHA-256:
  `0a741806852b4333d41a1296c016d67dce988f5393f7800eaf1020a185a4c076`.
- Parallel Futures report SHA-256:
  `126c0a2e10ffd387652c866c7c9407a4e84bbd4d5b6af1b47169bd429a37b4c4`.
- The fixed Safety Critic run is a preserved negative result:
  - schema valid and batch inference measured through `4,096`;
  - held-out hard-safe F1 `0.789`, below the predeclared `0.80` gate;
  - unsafe precision `0.791`, below the predeclared `0.90` gate;
  - `showcase_ready=false`;
  - thresholds were not changed and learned-model throughput is withheld from
    the judge-facing showcase.
- Cloud and local evidence archive SHA-256 matched:
  `35c1110711c96a7271fe723ffd2dd8160e179e63cd46864df4e5198f518fa46d`.
- Local evidence:
  `docs/evidence/radeon-p0-2026-07-29`.
- Local regression passed `82/82`; the showcase build and rendered-HTML tests
  passed before measured copy was inserted.
- No commit, push, deployment, official PR edit, frozen Gate 3.2/Gate 3.3
  mutation, or instance destruction occurred.

## Scale-first judge narrative and 80-second visual review — 2026-07-29

- Reordered the local judge experience around the verified Radeon compute
  story:
  - hero: `256 robot worlds. One safe move.`;
  - measured `1 / 16 / 64 / 256` scale progression;
  - animated 256-world wall;
  - 54-world Parallel Futures funnel;
  - interactive safety arena, preserved replay, and formal proof afterward.
- The page keeps compute throughput and formal safety evidence explicitly
  separate. The 337,000 timed environment steps are not independent safety
  trials; the 54 candidate/repeat worlds are not added formal scenes.
- Desktop and 390-pixel mobile layouts were inspected with Playwright.
  Console inspection reported zero errors and zero warnings.
- Added an 80-second, 1920×1080, 20 FPS scale-first visual review cut:
  `docs/submission/GuardianSim-Radeon-Parallel-Futures-review-v1.mp4`.
  It contains six chapters: compute hook, Radeon scale, Parallel Futures
  funnel, preserved Seed 411 replay, formal safety proof, and claim boundary.
- The cut is intentionally silent. The owner-approved Qwen voice direction
  should be applied only after visual approval, avoiding repeated TTS
  generation while the edit is still moving.
- Strict review validation passed:
  - output SHA-256
    `76948ac89f3026cf6d0b845d6d009ab63cff27975b62ba952858355b4cb5073f`;
  - eight decoded sample points;
  - all source hashes and claim boundaries verified;
  - displayed scale, Parallel Futures, and formal safety metrics locked to
    their preserved reports.
- Local repository regression remained `82/82`; the showcase production build
  and rendered-HTML tests passed `3/3`.
- No commit, push, deployment, official PR edit, frozen-report mutation, cloud
  rerun, or Radeon instance destruction occurred.

## Scale-first Qwen narration candidate — 2026-07-29

- Preserved the validated 80-second visual cut byte-for-byte and used it as
  the immutable source for a narrated review candidate.
- Generated six cached English narration segments with Alibaba Cloud Model
  Studio:
  - model `qwen3-tts-instruct-flash-2026-01-26`;
  - voice `Ethan`;
  - calm, conversational robotics-engineer direction;
  - no API credential written to the sidecar, captions, video, or logs.
- Added fixed chapter captions and an original low-volume synthesized ambient
  bed with transition chimes. Final loudness inspection measured approximately
  `-18.2 dB` mean and `-1.3 dB` peak.
- Built
  `docs/submission/GuardianSim-Radeon-Parallel-Futures-narrated-v2.mp4`:
  - `80.0` seconds;
  - `1920×1080` at `20 FPS`;
  - output SHA-256
    `b07d0c71e7aceea5f2ebe82cd87d94ea223a99c090c5a6e1f6e06ce06559a2c9`.
- Strict narrated validation passed:
  - full audio/video decode;
  - all six narration hashes and timing windows;
  - fixed-caption hash;
  - immutable silent-source identity;
  - preserved evidence hashes, locked metrics, and claim boundaries.
- Final local regression passed `82/82`; the showcase production build and
  rendered-HTML tests passed `3/3`; Python compilation and `git diff --check`
  passed.
- Key caption frames were inspected at the Radeon scale, Parallel Futures,
  Seed 411, and formal-proof chapters. Captions remained readable without
  hiding the primary visual comparison.
- This is still a local owner-review candidate. It does not supersede the
  approved 4:41 submission video until explicit owner approval.
- No commit, push, deployment, official PR edit, frozen-report mutation, cloud
  run, or Radeon instance destruction occurred.

## Typography and human-copy revision — 2026-07-29

- The owner identified a real overflow defect on the frozen-result screen:
  `46.003 mm` extended beyond the fourth metric card.
- Added width-aware font fitting for every metric-card title, before value,
  after value, and detail line. The longest value now remains inside the
  fourth card with visible right padding.
- Replaced slogan-heavy copy with direct experiment language:
  - the opening says what ran on Radeon and what was tested;
  - the throughput section is labeled as a measured workload;
  - the action section explains the 18×3 candidate structure;
  - “formal proof” was replaced by the accurate “frozen 30-scenario run”;
  - the close states the actual rule: use an action that passes every gate or
    stay put.
- Added the durable writing standard above so future reports, PR text, site
  copy, and narration avoid generic AI-generated prose.
- Built and strictly validated a new immutable visual source:
  `docs/submission/GuardianSim-Radeon-Parallel-Futures-review-v2.mp4`.
  SHA-256:
  `5033b75ed91fd8883e70fd6ec7f4ce52c8a2ee8092822d8c89404b7894cb6edb`.
- Built and strictly validated the revised Qwen narration candidate:
  `docs/submission/GuardianSim-Radeon-Parallel-Futures-narrated-v3.mp4`.
  SHA-256:
  `70c1bf9734b29c7e698dacc3a09e9a0602757c3be93a6917fbd17372530bb9c8`.
- V3 remains `80.0` seconds at `1920×1080`, `20 FPS`. Full audio/video
  decoding, visual-source identity, six narration hashes, fixed captions,
  evidence hashes, locked metrics, and claim boundaries passed.
- Representative V3 frames from the opening, Parallel Futures, frozen result,
  and closing screens were inspected. No text crossed its container boundary.
- Final local regression passed `82/82`; the showcase production build and
  rendered-HTML tests passed `3/3`; Python compilation and `git diff --check`
  passed.
- No commit, push, deployment, official PR edit, frozen benchmark mutation,
  cloud run, or Radeon instance destruction occurred.

## Optical-centering correction — 2026-07-29

- The owner correctly identified that V3 prevented overflow but still used
  fixed left/right value anchors. Short rows such as `30 → 0` therefore had an
  off-center visual group.
- Replaced fixed value anchors with measured group layout:
  - measure the rendered widths of the before value, arrow, after value, and
    dynamic gaps;
  - shrink the shared value font only when the complete group requires it;
  - center the complete group inside the card;
  - assert during rendering that the group is inside the card and its left and
    right padding differ by no more than one pixel.
- Card titles and detail lines are also centered from their measured rendered
  width.
- The final encoded frame was extracted from the narrated video and inspected;
  `30 → 0` is centered as one group, while the longer `23.191 → 46.003 mm`
  remains inside its card.
- New immutable artifacts:
  - silent V3 SHA-256
    `4e2c6eddc1bb127818dcf0368c83e4eb30f4b3dcdfe754d8933d3ed36799c85d`;
  - narrated V4 SHA-256
    `2be66996eb0e3bb460148c5afc8060f69680f1d7e314e2e46cf2d363d53a923a`.
- Strict silent and narrated validation passed, including the recorded layout
  policy, full decode, source hashes, narration hashes, captions, evidence
  metrics, and claim boundaries.
- Final local regression passed `82/82`; the showcase production build and
  rendered-HTML tests passed `3/3`; Python compilation and `git diff --check`
  passed.
- No commit, push, deployment, official PR edit, cloud execution, or Radeon
  instance destruction occurred.

## Local official-package P0 update — 2026-07-29

- Rechecked the organizer repository. Track 3 still recommends a 3-5 minute
  complete-workflow video and allows supplementary material. The approved
  4:41 V2 remains the primary demo; the optically centered 80-second V4 is a
  supplementary Radeon compute preview.
- Kept the frozen Gate 3.2 safety result unchanged and added two separately
  labeled compute sections:
  - fixed 1/16/64/256-world Genesis throughput;
  - one 54-world Parallel Futures engineering run.
- Preserved the statistical boundary in the report, package README, and PR
  draft:
  - 337,000 timed environment steps are a throughput workload, not safety
    trials;
  - 54 futures are 18 candidates times three repeats, not 54 independent
    scenes.
- Updated the technical-report source with direct experiment language and
  replaced the generic innovation section with `What GuardianSim adds`.
- Rebuilt the final report as a seven-page PDF. Every page was rendered to PNG
  at 150 DPI and inspected; no clipping, table overflow, footer collision, or
  draft marking was found.
- New report SHA-256:
  `6a735fe0a77c0c6ec3e9461051bac29ce371a3ca04d74246f0d39d6a64a3291c`.
- Local package-manifest SHA-256:
  `392e624b5839e4af0799d59d321ae27d31b12a34cb225fe20d342bd4ceef0d94`.
- The local official package now contains:
  - the seven-page technical report;
  - the 80-second V4 preview;
  - raw Radeon scale and Parallel Futures reports;
  - their strict validation results;
  - a recursive SHA-256 manifest.
- Validation passed:
  - Python unit tests `82/82`;
  - showcase rendered-HTML tests `3/3`;
  - showcase production build and ESLint;
  - strict Radeon scale and Parallel Futures validators;
  - V4 full audio/video decode and hash/claim checks;
  - package checksum verification.
- The update remains local. Before changing organizer PR #39, create a final
  public GuardianSim release commit containing the P0 code and evidence, then
  replace the older immutable source/evidence commit in the package and PR
  draft. Do not update the PR until the owner authorizes that release step.
- No push, deployment, organizer PR edit, cloud execution, or Radeon instance
  destruction occurred.

## Public Radeon P0 release and organizer PR update — 2026-07-29

- The owner authorized the prepared release step.
- Published GuardianSim commit
  `830e4fc8e2467bc4a0eacbb9777b91351e20f924` on branch
  `agent/parallel-futures-showcase`.
- Created and pushed the annotated immutable tag
  `hackathon-2026-submission-v2`; its peeled commit is exactly
  `830e4fc8e2467bc4a0eacbb9777b91351e20f924`.
- All release links were checked after publication and returned HTTP 200:
  source tree, reproducibility guide, 4:41 workflow video, 80-second Radeon
  preview, and P0 evidence directory.
- Updated official contest fork branch
  `submission/track3-aegis-motion-guardiansim` with commit
  `d73bad667db22d67d737ec50ceb8ff761b0c3816`.
- Updated organizer PR #39 in place. Verified state:
  - URL: <https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/39>;
  - state `OPEN`;
  - not a draft;
  - merge state `CLEAN`;
  - head commit `d73bad667db22d67d737ec50ceb8ff761b0c3816`.
- Downloaded the remote report, preview, manifest, and evidence files from the
  fork branch. The recursive manifest passed and the report/preview hashes
  matched local artifacts.
- Final identities:
  - technical report:
    `6a735fe0a77c0c6ec3e9461051bac29ce371a3ca04d74246f0d39d6a64a3291c`;
  - supplementary preview:
    `2be66996eb0e3bb460148c5afc8060f69680f1d7e314e2e46cf2d363d53a923a`;
  - official-package manifest:
    `392e624b5839e4af0799d59d321ae27d31b12a34cb225fe20d342bd4ceef0d94`;
  - submission working-set manifest:
    `98ab53ab4d900d9dacfabf04a2ae22dfc5e1dec1fe6b27484c04a42550a9a57c`.
- Local V1/V2/V3 intermediate scale-video iterations and Playwright captures
  were deliberately not staged or published.
- The organizer PR was not merged, and the Radeon instance was not accessed or
  destroyed.

## Public judge-facing showcase — 2026-07-29

- The owner authorized changing the interactive showcase to public access and
  adding it to organizer PR #39.
- The existing Sites workspace rejected internet-public access. The private
  deployment was left unchanged; no bypass credential was published.
- Added a separate static build that reuses the verified React experience and
  preserves the existing Sites build:
  - source commit
    `1d66d3ffe6d6a05956d4e4ae314347f1ebb9d073`;
  - GitHub Pages commit
    `3b4b438b57d3d7c1539f74c33e8c14358fe45cc1`;
  - public URL:
    <https://nvm-star-max.github.io/GuardianSim/>.
- Both the original server-rendered build/tests (`3/3`) and the static
  build/tests (`2/2`) passed, together with ESLint.
- Verified without authentication:
  - HTML HTTP 200;
  - compiled JavaScript HTTP 200;
  - stylesheet HTTP 200;
  - Seed 411 replay HTTP 200;
  - social-preview image HTTP 200.
- Added a no-sign-in judge quick-start to the official package and PR body.
  Official fork commit:
  `289e4c09211974f12f74b8298e493ab93e78037f`.
- The updated recursive official-package manifest passed; its SHA-256 is
  `5ffab05ff5ef602fefc6b42f1d993090a113f411fb2bc8ab16c45d1868fee621`.
- The updated submission working-set manifest passed; its SHA-256 is
  `fe7b8bae188b96585010a44b6b43d0d6057826745a0643336d6e6e06fab5eff4`.
- Organizer PR #39 remained `OPEN`, non-draft, and `CLEAN`, with no comments,
  reviews, or failed checks. It was not merged.
- No Radeon Cloud instance was accessed or destroyed.

## Arena measurement visibility and open-source overlap audit — 2026-07-29

- The public arena previously hid clearance and stability behind em dashes
  until the frozen gates were applied. This was valid interaction state but
  looked like missing data.
- Changed the interaction boundary:
  - evidence-backed clearance and stability are visible immediately;
  - collision/rejection/selection verdicts remain hidden until the user
    applies the frozen hard gates;
  - the call to action now says `APPLY GATES TO 18 FUTURES`.
- Verified the static build in a real browser:
  - all three Future cards exposed their measurements before evaluation;
  - selecting Future C and applying the gates revealed the expected
    collision, rejection, and selected states;
  - no card overflow was observed at the tested desktop viewport.
- Local acceptance passed Python unit tests `82/82`, both showcase test suites
  `3/3`, ESLint, submission checksum verification, and `git diff --check`.
- Added
  `docs/submission/OPEN_SOURCE_OVERLAP_AUDIT_2026-07-29.md` using only
  project-owned repositories and documentation.
- Closest reviewed layers:
  - cuRobo and MoveIt 2: motion generation/planning and collision checking;
  - ManiSkill and Isaac Lab: high-throughput robotics simulation/training;
  - Safety-Gymnasium: constrained safe-RL benchmarking;
  - Genesis: GuardianSim's physics foundation.
- AMD finding:
  - Genesis explicitly documents ROCm/HIP, `gs.amdgpu`, and an AMD Dockerfile;
  - cuRobo and Isaac Lab document NVIDIA/CUDA requirements;
  - ManiSkill's official matrix does not support AMD GPU simulation;
  - MoveIt 2 is a vendor-neutral CPU planning stack without a documented ROCm
    acceleration path;
  - Safety-Gymnasium does not document an AMD/ROCm acceleration path.
- Positioning boundary: GuardianSim is not a replacement for these projects.
  Its distinct layer is same-state physical counterfactual evaluation,
  frozen gates, repeatability, execute-or-stop behavior, and an evidence
  receipt on a demonstrated AMD ROCm path.
- Published source commit:
  `ea775906a4e40d38b976b21e3e1b97e27312173b`.
- Published GitHub Pages commit:
  `ec824eeaa8a5d9959f7d0135c14f0ac609ab6aa8`.
- GitHub Pages reported `built`. Public HTML, JavaScript, CSS, and the Seed 411
  replay each returned HTTP 200. The remote JavaScript contained the expected
  visible measurement values and new gate-action copy.
- The immutable contest tag was not moved and organizer PR #39 was not
  changed or merged.
- No Radeon Cloud instance was accessed or destroyed.

## Radeon maintenance backup and Safety Swarm P0 gate — 2026-07-29

- The organizer announced a Radeon Cloud publication/maintenance window for
  2026-07-31 at 18:00 UTC+8 and asked participants to preserve important data
  in NFS plus Git and local backups.
- The announcement names `/workspace/persistence`; instance
  `u-13907-735d71cb` actually exposes `/workspace/persistent`. The repository
  remains at `/workspace/persistent/GuardianSim`.
- Preserved the raw 2026-07-29 Radeon P0 archive and checksum in both:
  - `/workspace/persistent/`;
  - `/Users/aolos/Downloads/GuardianSim-backups/2026-07-29/`.
- Verified archive SHA-256:
  `35c1110711c96a7271fe723ffd2dd8160e179e63cd46864df4e5198f518fa46d`.
  The archive contains Radeon scale, Parallel Futures, Safety Critic, and
  session-environment outputs. Safety Critic remains a negative result with
  `showcase_ready=false`.
- Added a restorable maintenance-backup implementation:
  - auto-detects both persistence mount spellings;
  - writes a Git bundle plus complete working-tree archive;
  - includes optional external raw artifacts;
  - records Git/environment metadata and recursive SHA-256 checksums;
  - excludes `.env*`, credentials, private keys, caches, virtual
    environments, Playwright scratch data, and Git internals.
- Added backup runbook
  `docs/submission/RADEON_MAINTENANCE_BACKUP_2026-07-29.md`.
- Rechecked the two currently visible Track 3 competitors:
  - NaviSense AI's strongest delivery mechanisms are a single end-to-end
    workflow, explicit measured Radeon inference, live demo, fallback path,
    and reusable upstream component;
  - 1bit.systems' strongest presentation mechanism is visible hardware-level
    telemetry and throughput, not a mechanism GuardianSim should duplicate.
- Combined the useful mechanisms from current entries and adjacent open-source
  projects into the next P0 gate, **Radeon Safety Swarm**:
  - one selected move;
  - a frozen 256-world uncertainty grid;
  - a 16×16 robustness wall;
  - typed safety costs, worst-case margin, failure histogram, and
    execute-or-stop result;
  - visible AMD/ROCm batch telemetry and a checksummed evidence receipt.
- The plan is recorded in
  `docs/submission/RADEON_SAFETY_SWARM_PLAN_2026-07-29.md`.
- Claim boundary: the 256 worlds are a separate engineering uncertainty
  stress-test population, not additional formal Gate 3.2 scenarios and not a
  physical-robot safety guarantee. The protocol, matrix, schema, thresholds,
  and telemetry method must be frozen before the formal cloud run.
- Local acceptance passed `84/84` Python unit tests, Python compilation, and
  `git diff --check`.
- Published the backup tool and P0 gate on
  `agent/parallel-futures-showcase` at commit
  `b97fd7e9a08a9c0fc7fdf2c9232dac76fb998afd`.
- Executed the complete backup against the live NFS mount. The restorable
  backup directory is:
  `/persistent/GuardianSim-backups/20260729T035224Z-1481f51cd706`.
- The cloud source repository was intentionally left on
  `main@1481f51cd706`; its Git status and all untracked P0 working files are
  captured in the working-tree archive. The separately pushed feature branch
  preserves the new backup implementation and plan.
- Independent cloud verification passed:
  - seven manifest payloads, including both raw external Radeon artifacts;
  - verified Git bundle;
  - readable working-tree tar archive with 580 members.
- The Radeon instance was reused without restart or destruction.

## Safety Swarm local protocol and replay — 2026-07-29

- Implemented the first local Radeon Safety Swarm slice without accessing or
  changing the cloud instance.
- Frozen one 256-world uncertainty matrix as a `4 × 4 × 4 × 4` Cartesian
  product:
  - target XY/yaw pose group;
  - clutter gap/bearing group;
  - end-effector XY bias group;
  - action-start delay group.
- Frozen matrix SHA-256:
  `71ea95a7194f1e9afdc0690ecdb30037b2a309a03049d26d832b9b21789b43eb`.
- Frozen protocol SHA-256:
  `9a8c5763d2ca007be924326812e9fd19c3125b8cfa968cdd734e01e7980f462c`.
- The execute rule is deliberately strict: all 256 worlds must pass the
  existing `10 mm` clearance and `0.70` stability gates, with zero clutter
  contacts and no reachability/task failure. Otherwise the result is
  `safe_stop`.
- Added typed safety costs, deterministic stop reasons, Wilson lower bound,
  worst/5th-percentile clearance, failure histogram, measured wall time, and
  environment-steps/s.
- Added a strict schema-1 validator that reconstructs all world labels,
  aggregates, and hashes. Radeon-formal reports additionally require:
  - `genesis_gpu_batched`;
  - an AMD device name;
  - a HIP version;
  - at least one ROCm telemetry sample;
  - a Git source commit.
- Added a standalone 16×16 HTML evidence replay and checked it in a real
  Chromium viewport at 1920×1450. No metric, hash, grid cell, footer, or
  decision card overflow was observed.
- The current 128-green/128-orange page is a deterministic UI fixture, not a
  simulation result. It is labelled
  `OFFLINE UI FIXTURE · NOT A RADEON RESULT`, has
  `showcase_ready=false`, and is rejected by `--require-radeon`.
- Next gate: implement per-environment Genesis perturbation and measurement
  capture, then run isolated 4-world and 16-world cloud smoke tests before one
  untouched 256-world formal run. Do not alter the frozen matrix or thresholds
  after seeing partial cloud outcomes.
- No commit, push, deployment, organizer-PR edit, formal Radeon run, instance
  restart, or instance destruction occurred in this slice.

## Safety Swarm Genesis smoke executor — 2026-07-29

- Added a dedicated engineering-smoke path for 4 and 16 Radeon environments.
- Smoke selection is predeclared and balanced:
  - 4-world IDs: `0, 85, 170, 255`;
  - the 16-world orthogonal subset represents each level of all four factors
    exactly four times.
- Every environment executes the same selected obstacle-aware candidate while
  receiving its own target pose, clutter geometry, end-effector bias, and
  start delay.
- The runner writes a frozen preflight before Genesis starts, refuses to
  overwrite evidence, records AMD/HIP/ROCm identity, and strictly validates
  raw world measurements and derived labels.
- Partial smoke reports use a separate report identity and remain
  `showcase_ready=false`; they cannot be combined with the 256-world formal
  report.
- The original formal identities remain unchanged:
  - matrix:
    `71ea95a7194f1e9afdc0690ecdb30037b2a309a03049d26d832b9b21789b43eb`;
  - protocol:
    `9a8c5763d2ca007be924326812e9fd19c3125b8cfa968cdd734e01e7980f462c`.
- Local checks passed `92/92` tests, compilation, and diff hygiene.
- Next action is an isolated 4-world Radeon smoke. Only a passing and strictly
  validated 4-world result may open the 16-world visual smoke gate.

## Safety Swarm Radeon smoke gate — 2026-07-29

- Reused Radeon Cloud instance `u-13907-735d71cb` without restart or
  destruction. The existing dirty `main` worktree was not modified; all
  Safety Swarm execution used the separate clean worktree
  `/workspace/persistent/GuardianSim-safety-swarm`.
- Preserved the first 4-world negative run. It was bound to the wrong
  already-defined candidate,
  `yaw_+67.5_retreat_+0.025_approach_+0.140`, and passed `0/4` because the
  extra `25 mm` retreat caused the gripper to miss the target. This was an
  implementation-binding error, not a reason to tune thresholds.
- Corrected the binding from the preserved Gate 3.2 replay to
  `yaw_+67.5_retreat_+0.000_approach_+0.140`.
- The corrected 4-world engineering smoke passed strict validation:
  - safe worlds `4/4`;
  - clutter contacts `0`;
  - worst sampled clearance `16.372 mm`;
  - minimum stability `0.925`;
  - `1,996` total environment steps in `8.323 s`;
  - `239.806` environment steps/s;
  - AMD GPU use: `62.545%` mean, `89%` peak across 22 samples.
- The predeclared balanced 16-world engineering smoke was report-valid but
  failed its all-world acceptance gate:
  - safe worlds `12/16`;
  - clutter-contact worlds `3`;
  - worst sampled clearance `0 mm`;
  - minimum stability `0`;
  - `7,984` total environment steps in `10.676 s`;
  - `747.843` environment steps/s;
  - AMD GPU use: `68.231%` mean, `94%` peak across 26 samples.
- The four failed rows were:
  - world `69`: `9.680 mm` clearance, no contact, stability `1.0`;
  - worlds `91`, `109`, and `209`: sampled contact, zero clearance, zero
    stability, and task failure.
- Gate decision: do not start the frozen 256-world formal run. Do not change
  the V1 matrix, thresholds, row order, or protocol based on these partial
  outcomes. A subsequent attempt requires a separately frozen protocol
  version that can select another eligible candidate or safely stop under the
  full uncertainty envelope.
- The cloud evidence was committed as
  `599c04770aca17b32971ed417d678122dbe4c453`. The package at
  `/workspace/safety-swarm-smoke-evidence-2026-07-29.tar.gz` has SHA-256
  `31a4c1c6923c793a501915260fa66eb5f8179dab8e728fc003d99b41687571c0`.
- The manually downloaded package matched that hash. Pre-extraction safety
  checks found 21 archive members, no absolute or parent-traversal paths, and
  no symbolic or hard links. All 16 payloads in the recursive checksum
  manifest passed locally.
- Imported the raw reports, preflights, validation receipts, logs, PIDs, and
  provenance under
  `docs/evidence/safety-swarm-smoke-2026-07-29`. All three reports passed the
  repository's strict `--require-radeon` validator.

## Safety Swarm V2 frozen candidate selection — 2026-07-29

- V1 remains immutable, including its reports, matrices, thresholds, hashes,
  and negative 16-world gate result. V2 is a new protocol rather than a
  reinterpretation or overwrite of V1 evidence.
- V2 freezes the 18 existing Gate 3.2 action candidates against the complete
  256-world uncertainty matrix:
  - 18 candidates × 256 worlds = 4,608 candidate-world pairs;
  - candidate catalog SHA-256:
    `9c3af60dfb812e6128f6e849d27cf2acd0d672cdcb3aa98191656e4009054e44`;
  - formal protocol SHA-256:
    `7fedeeeea436f3b0fe04196e4ad5ec225ccfe7bf26ad60cd3af8a7a4f4da43ac`;
  - maximum formal Genesis chunk: 256 environments.
- The unchanged hard gates are sampled clearance at least `10 mm`, stability
  at least `0.70`, no clutter contact, reachable, and task completed.
  A candidate qualifies only when every selected world passes and the
  candidate records zero contacts.
- Selection happens only among qualifying candidates and is deterministic:
  worst clearance descending, 5th-percentile clearance descending, minimum
  stability descending, then candidate index ascending. If none qualifies,
  the typed result is `safe_stop`; V2 does not choose the least-bad unsafe
  action.
- The predeclared cloud progression is:
  - `triad-4`: 3 candidates × 4 worlds = 12 pairs, protocol
    `4fad8ddaebbff6f2b328af83671465574a0482046a1361522ae8399c15fd574c`;
  - `full-4`: 18 × 4 = 72 pairs, protocol
    `e6c24948ee708c20d6c6ea270ac4ff3fb5b503d18896508d7d66fa69536aa984`;
  - `full-16`: 18 × 16 = 288 pairs, protocol
    `128a494aec03498c8ba6c807a3e26f8e733c87f61ec5e696371839270c3d9f44`;
  - formal: 18 × 256 = 4,608 pairs.
  Each larger gate opens only after the preceding gate passes strict report
  validation and its frozen acceptance rule.
- The Genesis runner can now flatten one V2 candidate-world tier into one GPU
  scene while preserving candidate-major/world-ID ordering. The V2 schema-1
  validator reconstructs assignments, measurements, qualification,
  selection, AMD/HIP/ROCm identity, telemetry, and report hashes.
- The local `triad-4` fixture covers all 12 assignments and validates the
  report/rendering path, but is explicitly offline, has
  `showcase_ready=false`, and is not an AMD result or performance claim.
- Local acceptance passed `98/98` tests, Python compilation, fixture strict
  validation, renderer checks, and diff hygiene.
- No cloud workload, instance restart, instance destruction, threshold
  change, or formal claim occurred in this stage. The next gate is the
  isolated 12-environment `triad-4` Radeon smoke.

## Safety Swarm V2 Gate V2-A Radeon result — 2026-07-30

- Reused Radeon Cloud instance `u-13907-735d71cb` without restart or
  destruction. Ran from the clean detached worktree
  `/workspace/persistent/GuardianSim-safety-swarm-v2` at source commit
  `dd300f98320f39666f684c3aed1f3afa25884d20`. The previous V1 cloud evidence
  commit was not an ancestor of this V2 source, so its worktree and evidence
  were not modified.
- The predeclared `triad-4` run completed all 3 candidates × 4 frozen worlds,
  or 12 candidate-world pairs. Strict schema-1 Radeon validation passed with
  report SHA-256
  `61fff08c21accbae5d237905d754e48e530e2bbfa33ca0642d62b2331f58874a`.
- Decision: `execute`. The only qualifying candidate was
  `yaw_+00.0_offset_+0.000`, with 4/4 safe worlds, zero contacts,
  `42.136 mm` worst-case sampled clearance, `42.985 mm` fifth-percentile
  sampled clearance, and `0.923` minimum stability.
- The centered `+67.5°` candidate passed 2/4 and contacted clutter twice. Its
  `25 mm` retreat counterpart passed 0/4, with one contact and three
  stability failures. Across all 12 pairs, 6 were safe and 3 had sampled
  clutter contact.
- The offline fixture had selected a different candidate. The measured
  Radeon decision therefore confirms that fixture data was not used as
  result evidence.
- Measured AMD execution: `5,988` environment steps in `10.755 s`,
  `556.783` environment steps/s, `69%` mean and `94%` peak GPU utilization
  across 27 telemetry samples, and maximum VRAM use of
  `1,126,154,240 bytes` (about `1.049 GiB`). No telemetry sampling errors
  occurred.
- The downloaded evidence archive matched cloud SHA-256
  `7280f59866980954ec52287fd4046069c487dfb23bca5f8c51d91c72568f877f`.
  It contained no unsafe paths or links, all 13 inner checksums passed, and
  the imported report passed local strict `--require-radeon` validation.
  Raw evidence is under
  `docs/evidence/safety-swarm-v2-triad-4-2026-07-30`.
- Gate V2-A is executor evidence only and remains `showcase_ready=false`.
  No thresholds, candidates, worlds, ordering, or protocol hashes changed.
  The next unopened gate is V2-B, all 18 candidates × 4 worlds = 72 pairs.
  Do not start V2-C, V2-D, or make a formal robustness claim from this result.

## Safety Swarm V2 Gate V2-B Radeon result — 2026-07-30

- Reused Radeon Cloud instance `u-13907-735d71cb` without restart or
  destruction and ran the unchanged clean detached worktree at source commit
  `dd300f98320f39666f684c3aed1f3afa25884d20`.
- The frozen `full-4` tier completed all 18 candidates × 4 worlds, exactly 72
  candidate-world pairs. Strict schema-1 Radeon validation and the independent
  acceptance check passed. The report SHA-256 is
  `3b8d816c73efd99bdd2d34123e60eed8fb70161ed0d599ddb00e959aae38d4f4`.
- Eight candidates qualified across all four worlds with zero contacts. The
  deterministic ranking selected
  `yaw_-22.5_retreat_+0.025_approach_+0.140`, which passed 4/4 with:
  - `96.009 mm` worst-case sampled clearance;
  - `96.857 mm` fifth-percentile sampled clearance;
  - `0.847` minimum stability;
  - zero clutter contacts.
- Across the complete 72-pair batch, 41 candidate-world pairs were safe and
  five recorded sampled clutter contact. These are search-population
  diagnostics; V2-B passes because at least one candidate satisfied every
  frozen world and the deterministic selector executed only a qualifying
  candidate.
- Measured AMD execution completed `35,928` environment steps in `15.098 s`:
  `2,379.598` environment steps/s and `4.769` candidate-world pairs/s.
  Radeon telemetry recorded `76.378%` mean and `96%` peak GPU utilization
  across 37 samples, maximum VRAM use of `1,247,768,576 bytes` (about
  `1.162 GiB`), and no sampling errors.
- The evidence archive SHA-256 is
  `78e3df66673037cfde9ff04e19bd35ffd040c257b4468ac2268dd1e8c3a75359`.
  Its cloud and downloaded hashes matched; pre-extraction checks found no
  absolute paths, parent traversal, symbolic links, or hard links. All 17
  inner checksums passed. Evidence is preserved under
  `docs/evidence/safety-swarm-v2-full-4-2026-07-30`.
- The first derived acceptance summary incorrectly looked for protocol hashes
  at the report root. The original report and strict validator were correct;
  the summary was regenerated from `report.protocol`, rechecked, and only the
  corrected version was packaged.
- No candidate, world, hard gate, ordering rule, threshold, or protocol hash
  changed. V2-B remains partial engineering evidence with
  `showcase_ready=false`; it opens only Gate V2-C (`18 × 16 = 288` pairs).
  Gate V2-D and any 4,608-pair robustness claim remain closed.

## Safety Swarm V2 Gate V2-C Radeon result — 2026-07-30

- Reused Radeon Cloud instance `u-13907-735d71cb` without restart or
  destruction. The clean detached worktree and source commit remained
  `dd300f98320f39666f684c3aed1f3afa25884d20`.
- The frozen `full-16` tier completed all 18 candidates × 16 orthogonal
  worlds, exactly 288 candidate-world pairs. Strict schema-1 Radeon validation
  and the independent acceptance check passed. The report SHA-256 is
  `0ba9c8db2754c72b2e4e99ebda6ef163763a4244bd9fc068df0b74b21b6f166d`.
- Five candidates qualified across all 16 worlds with zero contacts. The
  deterministic ranking selected
  `yaw_-45.0_retreat_+0.000_approach_+0.140`, which passed 16/16 with:
  - `66.339 mm` worst-case sampled clearance;
  - `70.144 mm` fifth-percentile sampled clearance;
  - `0.909` minimum stability;
  - zero clutter contacts.
- The larger uncertainty envelope changed the decision. V2-B's four-world
  winner was `yaw_-22.5_retreat_+0.025_approach_+0.140`; it was not the
  V2-C winner. The qualifying set also narrowed from eight candidates to
  five. This is measured evidence that expanding world coverage changes
  robust action selection.
- Across the complete 288-pair search population, 165 candidate-world pairs
  were safe and 14 recorded sampled clutter contact. These values describe
  evaluated alternatives, not the selected action and not 288 independent
  real-robot trials.
- Measured AMD execution completed `143,712` environment steps in `15.870 s`:
  `9,055.573` environment steps/s and `18.147` candidate-world pairs/s.
  Radeon telemetry recorded `78.282%` mean and `96%` peak GPU utilization
  across 39 samples, maximum VRAM use of `1,518,317,568 bytes` (about
  `1.414 GiB`), and no sampling errors.
- The evidence archive SHA-256 is
  `b5262da3769e41fb67838eb537b37357c99544902ee8d6fa9effb9890fe82fd5`.
  Cloud and downloaded hashes matched; the archive contained no absolute
  paths, parent traversal, symbolic links, or hard links, and all 17 inner
  checksums passed. Evidence is under
  `docs/evidence/safety-swarm-v2-full-16-2026-07-30`.
- No candidate, world, hard gate, assignment order, selection rule, threshold,
  or protocol hash changed. V2-C remains partial engineering evidence with
  `showcase_ready=false`. It opens Gate V2-D under the frozen protocol, but the
  18 × 256 = 4,608-pair formal run has not started and no formal robustness
  claim is permitted yet.

## Safety Swarm V2 Gate V2-D formal executor — 2026-07-30

- Implemented the previously missing formal execution chain without changing
  the frozen protocol SHA-256
  `7fedeeeea436f3b0fe04196e4ad5ec225ccfe7bf26ad60cd3af8a7a4f4da43ac`.
- The 4,608 assignments are now represented as exactly 18 ordered chunks.
  Chunk `i` contains candidate `i` against all world IDs `0..255`, with global
  assignment interval `[i×256, (i+1)×256)`. No chunk can be presented as
  standalone formal evidence.
- Each attempt writes to a new numbered directory and is never overwritten.
  A restart revalidates an existing complete chunk before skipping it; failed
  or interrupted attempts remain preserved and the next attempt receives a
  new number.
- The final report can be assembled only from all 18 strictly validated AMD
  chunks in frozen order. Validation reconstructs all 4,608 labels,
  qualification and ranking, verifies source/device consistency, recomputes
  wall-time and ROCm telemetry aggregation from chunk receipts, and checks
  report hashes.
- Local verification passed `101/101` tests, Python compilation, Ruff checks,
  protocol-hash identity, and diff hygiene. This is implementation
  verification only: no formal Radeon chunk has run yet and no formal result
  or performance claim exists.

## Safety Swarm V2 Gate V2-D formal Radeon result — 2026-07-30

- Reused Radeon Cloud instance `u-13907-735d71cb` without restart or
  destruction. The formal run used the clean detached persistent worktree
  `/workspace/persistent/GuardianSim-safety-swarm-v2-formal` at source commit
  `4d0aaec1da077e333cbfdd9ee3f413d852c1cbec`.
- Completed all 18 frozen candidate-major chunks on their first numbered
  attempt. Each chunk evaluated one candidate against all 256 frozen worlds,
  for exactly `18 × 256 = 4,608` candidate-world pairs. No chunk was resumed,
  replaced, or combined across source revisions.
- Strict schema-1 `--require-radeon` validation passed for the complete report
  under unchanged formal protocol SHA-256
  `7fedeeeea436f3b0fe04196e4ad5ec225ccfe7bf26ad60cd3af8a7a4f4da43ac`.
  The complete report SHA-256 is
  `a3e86baa03e84d75a81062fee5f9f22770a3753708c116168174ea291c7a93cf`.
- Five candidates qualified across all 256 worlds. Frozen ranking selected
  `yaw_-45.0_retreat_+0.000_approach_+0.140`, which recorded:
  - `256/256` safe worlds and zero sampled clutter contacts;
  - `66.249 mm` worst-case sampled clearance;
  - `66.304 mm` fifth-percentile sampled clearance;
  - `0.907` minimum stability.
- Across the full candidate-search population, `2,614/4,608` pairs were safe
  and 270 recorded sampled clutter contact. These counts characterize rejected
  alternatives as well as qualifying candidates; they are not 4,608
  independent robot trials.
- Measured AMD execution completed `2,299,392` environment steps in
  `226.676 s`, or `10,143.979` environment steps/s and `20.329`
  candidate-world pairs/s. Scene construction across all chunks took
  `385.078 s`.
- Radeon telemetry recorded `73.406%` mean and `97%` peak GPU utilization
  across 588 samples, maximum VRAM use of `1,482,690,560 bytes` (about
  `1.381 GiB`), and no sampling errors. Device evidence identifies
  `AMD Radeon Graphics`, HIP `7.2.53211-e1a6bc5663`, PyTorch
  `2.9.1+gitff65f5b`, and Genesis `1.2.3`.
- Cloud archive SHA-256
  `0450857c2d50446ba76c1358bdf622c7e5cc4f43dbcc6dd48abb2e855b48e9ee`
  matched the downloaded file. Safe extraction passed, all 90 recursive inner
  checksums matched, and the imported report passed local strict Radeon
  validation. Raw evidence is under
  `docs/evidence/safety-swarm-v2-formal-2026-07-30`.
- The first post-run validator command used the smoke filename `report.json`
  instead of the formal filename `formal-report.json`. It did not alter the
  report or run; the empty failed receipt was preserved as
  `strict-validation.failed-missing-report-path.txt`, after which validation
  was rerun against the correct file and passed. The generated
  `report-summary.json` is a convenience derivative; the authoritative
  sources are `formal-report.json`, `formal-validation.json`,
  `strict-validation.txt`, and `SHA256SUMS`.
- Gate V2-D is complete and `showcase_ready=true` under the frozen engineering
  protocol. The allowed claim is a Radeon candidate-by-uncertainty stress
  test and measured batched-physics throughput. It is not a physical-robot
  safety guarantee and must not be described as 4,608 independent real-robot
  trials.

## Judge-facing Safety Swarm V2 showcase — 2026-07-30

- Promoted the verified Gate V2-D result to the main website narrative:
  `4,608 measured candidate-world pairs → 5 candidates passing 256/256 →
  1 action selected by frozen ranking`.
- Added `scripts/build_showcase_safety_swarm_data.py`. It reads the preserved
  5.9 MB formal report and generates the compact tracked module
  `showcase/app/safetySwarmFormal.generated.ts`; website heatmap values and
  summary metrics are therefore derived from evidence rather than copied or
  illustrated by hand.
- Added an 18 × 256 canvas heatmap with exact per-pair labels:
  safe, clutter contact, stability-gate failure, and clearance-gate failure.
  The selected `-45° · R0` row is highlighted and reports the preserved
  256/256 safe result, zero contact, `66.249 mm` worst clearance,
  `66.304 mm` fifth-percentile clearance, and `0.907` minimum stability.
- Separated the formal decision workload from the existing raw simulator
  scaling benchmark. The formal card reports only the verified values:
  `2,299,392` environment steps, `226.676 s`, `10,143.979 steps/s`,
  `73.406%` mean GPU and `97%` peak GPU. The 256-world raw benchmark remains
  separately labelled at `35,166 steps/s`.
- Added immutable report/evidence links pinned to evidence commit
  `975a82b3e09d0458a4c02ac945859f2fdf874c4f` and kept the visible boundary:
  this is a candidate-by-uncertainty engineering simulation stress test, not
  4,608 independent robot trials or a physical-robot safety guarantee.
- Desktop QA at 1440 × 1000 measured zero page overflow and zero card
  overflow. Mobile QA at 390 × 844 measured zero page overflow; the hero
  button/performance-card overlap was corrected to a `32.8 px` gap. The
  dense matrix scrolls only inside its own bounded viewer on mobile.
- Two generated social-card attempts were rejected because their depicted
  number of fully passing rows did not match the formal report. Neither image
  entered the repository; OG-image references were removed rather than
  publish inaccurate evidence.
- Showcase server build, rendered evidence tests, GitHub Pages build/static
  tests, ESLint, and browser console checks passed. No Radeon instance,
  frozen evidence, submission media, or unrelated local files changed.

## Private production showcase deployment — 2026-07-30

- Pushed showcase source commit
  `f5b9ed061e9483027f367ebfd1d950ee76ed7312` to the existing Sites source
  branch and saved it as site version `4`.
- Deployed version `4` successfully to the existing owner-only production
  site:
  `https://guardiansim-proof.dghcdtddgh.chatgpt.site`.
- The uploaded archive was built from that exact commit and recorded content
  hash
  `sha256:91c98971aa4498571b257676b098633ddf70b1d36d45cf50fe11d81ce1916eba`.
- Sites reported deployment
  `appgdep_6a6b1cfe6b608191a0bd8509f0cccae2` as `succeeded`. Access remained
  owner-only; no sharing or permission setting changed.
- Anonymous and current browser smoke checks correctly reached the site's
  sign-in gate, so no claim is made that the protected production DOM was
  inspected without owner authentication. The exact deployed commit had
  already passed desktop/mobile visual, overflow, data-reconciliation,
  console, build, static-page, and lint checks locally.

## V3 submission package and public showcase — 2026-07-30

- Reconciled the official Track 3 requirements against the organizer
  repository: English technical report, dedicated source, detailed
  reproducibility README, and a 3-5 minute complete-workflow video remain the
  required deliverables. The official PR title remains
  `Track 3, Aegis Motion, GuardianSim`.
- Updated the root README, reproducibility guide, technical-report source,
  organizer PR draft, submission working-set README, and official-package
  README to separate:
  - the 30-scenario Gate 3.2 safety result;
  - the raw 1/16/64/256-world physics-throughput curve;
  - the formal 18 × 256 = 4,608 candidate-world decision workload.
- Rebuilt the final technical report as a seven-page A4 PDF. All pages were
  rendered and visually inspected; no clipping, overlap, orphan reference
  page, or draft marking remained. Final PDF SHA-256:
  `4028372be15ca2fba2a0cd7f1ddd7e51c8d9cd012521e4be80cc40a523500ef3`.
- Added compact Safety Swarm V2 summary and strict validation receipts to the
  organizer package. Recursive package checksum manifest SHA-256:
  `b55bd15e4c9bc7649e126bfd8c5a7229cecc735849871ec163090073395a0143`.
- Preserved the approved 4:41 workflow video and 80-second Radeon preview
  byte-for-byte. They predate the formal 4,608-pair run and are not relabeled
  as footage of that workload.
- Published the exact static showcase build to the public `gh-pages` branch at
  commit `c649178c638fcd8302d01a2e7ec7af7e705d54c4`. Online checks loaded
  `assets/index-DZNAy0i7.js`, found the `4,608 futures` payload, measured zero
  page-level horizontal overflow, and found no console warnings or errors.
- Source and package preparation commit:
  `a8a8ec0615ed4ccc806fee252ade9ff7077e56aa`.
- At the end of package preparation, the V3 tag and organizer PR update
  remained explicit publication gates. They were completed in the separate
  release step recorded below.

## Public V3 organizer release — 2026-07-30

- After explicit owner authorization, created annotated tag
  `hackathon-2026-submission-v3`. The tag peels to source commit
  `5f7e3f7c8f984fd378f8c147038d84fb2e4983b3`.
- Synchronized the prepared organizer package to the existing fork branch
  `submission/track3-aegis-motion-guardiansim` at commit
  `2657aa23e84c9f75e4f55b8cdec49bba985a8870`. No new pull request was opened.
- Updated existing organizer PR #39 in place. Verified title:
  `Track 3, Aegis Motion, GuardianSim`; state `OPEN`; non-draft; GitHub
  mergeability `MERGEABLE`; head commit `2657aa23e84c9f75e4f55b8cdec49bba985a8870`.
  The organizer repository reports no configured status checks for this
  branch; this is not a failed check.
- A fresh clone of the fork branch passed every entry in the ten-file package
  checksum manifest. Manifest SHA-256:
  `b55bd15e4c9bc7649e126bfd8c5a7229cecc735849871ec163090073395a0143`.
- Unsigned HTTP checks returned 200 for the immutable V3 tag, reproducibility
  guide, approved 4:41 workflow video, public GitHub Pages showcase, and
  organizer-package PDF.
- The public PR remains unmerged for organizer review. The Radeon Cloud
  instance, frozen protocols, preserved evidence, and unrelated untracked
  local media were not changed during release.

## Radeon Scale V2 direction frozen — 2026-07-31

- Reviewed the active Track 3 field and separated GuardianSim's position from
  locomotion-training and real-robot VLA entries. Chaal's strongest reusable
  practices are its one-line workload definition, large but correctly scoped
  environment-step count, physics-versus-training split, saturation reporting,
  robustness table, raw JSON, and checkpoint/demo receipts.
- Decided not to add PPO solely for a headline number. GuardianSim remains a
  policy-agnostic execution-time safety layer: PPO, VLA, or a scripted policy
  proposes a motion; Radeon evaluates physical futures; GuardianSim executes
  one eligible action or stops.
- Froze a separate Radeon Scale V2 workload:
  - 1, 16, 64, 256, 512, 1,024, 2,048, and 4,096 full Franka/table/four-YCB
    worlds;
  - 200 warmup steps and 12,288 measured steps per batch;
  - 50,331,648 measured environment steps at the largest batch;
  - 98,512,896 measured environment steps across the complete sweep.
- These counts are physics environment steps, not dataset rows, PPO training
  experience, safety trials, or physical-robot evidence. No V2 result may be
  added to the public PR, site, report, or video before strict Radeon
  validation.
- The protocol predeclares a separate capacity preflight. A 4,096-world
  out-of-memory result fails this V2 protocol rather than silently lowering the
  target after partial results.
- Added a no-overwrite, exact-source resumable runner and schema-2 validator.
  Existing V3 evidence and tag remain immutable. This stage stops before cloud
  launch for local verification and owner review.
- Local verification passed 111/111 Python tests, Ruff, Python compilation,
  showcase server/static tests, ESLint, and diff hygiene. Browser QA measured
  zero horizontal overflow at 1440 × 1000 and 390 × 844, a 32.77 px mobile
  gap between the hero actions and AMD evidence card, and no console warning
  or error.
- The local showcase now tells judges on the first screen:
  `policy proposes → Radeon simulates → hard gates verify → move or stop`.
  It still displays only previously verified V3 measurements; V2 target
  workload counts are not public-result claims.

## Radeon Scale V2 formal result verified — 2026-07-31

- Ran the separate capacity preflight from exact source commit
  `3d8021a237ca0dfca41c98df1b492b7b9a523b4f`. The declared
  `512/1024/2048/4096` capacities all passed. The preflight remains
  capacity-only and is not merged into performance evidence.
- Completed the frozen eight-batch formal suite at
  `1/16/64/256/512/1024/2048/4096` full headless
  Franka/table/four-YCB scenes. Every batch completed on its first attempt.
- Strict schema-2 validation passed. The 4,096-world batch measured
  `50,331,648` environment steps at
  `152,099.018 environment-steps/s`, a `1,028.069×` speedup over the
  one-world run and `25.099%` parallel efficiency.
- The 4,096-world trial recorded `98.651%` mean and `99%` peak GPU
  utilization with `6,706,667,520` peak VRAM bytes (`~6.25 GiB`).
  The complete sweep measured `98,512,896` environment steps.
- The scaling curve still rose at 4,096 worlds, while efficiency declined
  after 256. This is reported as saturation behavior rather than hidden.
- Claim boundary remains explicit: environment steps are physics throughput,
  not training examples, dataset rows, independent safety trials, or
  physical-robot evidence.
- Frozen protocol SHA-256:
  `bcb91e081b196a5b6274ce1efd461d2005f1c1505dbd7020e9fbbaab0bb536e8`.
  Canonical report SHA-256:
  `971769c6a051f6b2794982a02828601e91406320023a90bf85fc28103fa8b742`.
- Preserved preflight evidence under
  `docs/evidence/radeon-scale-v2-preflight-20260731` and formal evidence under
  `docs/evidence/radeon-scale-v2-formal-20260731`. Formal archive SHA-256:
  `71b7b0a2958444ec4d6b35831684223b38123291a54c8debbf25ed77a53d88de`.
- Updated the local judge-facing showcase and copy to lead with the verified
  Radeon receipt. This result has not yet been pushed to the public Pages site
  or organizer PR; owner review comes before that release.
- Local verification passed 108/108 Python unit tests, 5/5 server-rendered
  showcase tests, 3/3 static Pages tests, both showcase builds, ESLint, Python
  compilation, strict report validation, both evidence checksum manifests,
  and diff hygiene.
- Exact browser QA passed at 1,440 × 1,000 and 390 × 844 with zero page
  horizontal overflow and no runtime/log errors. The only child elements
  extending past the viewport are intentionally clipped scene-grid decoration
  and the heatmap canvas inside its horizontal scroll container.

## Scale V2 report and 80-second visual candidate — 2026-07-31

- Updated the technical-report source to replace the superseded
  1-to-256-world Scale V1 headline with the strictly validated eight-point
  Scale V2 result. The report keeps Scale V2 physics throughput, Safety Swarm
  candidate-world evidence, and Gate 3.2 safety executions as separate units.
- Built an eight-page local PDF candidate at
  `output/pdf/GuardianSim-Technical-Report.pdf`, SHA-256
  `42338e06481c4caa08b6e53ab61ed7d522de0216931dfa402314cbcbdd6e850e`.
  Rendered and inspected all eight pages; the scale and results tables, hashes,
  limitations, margins, and footers are legible with no clipped content.
- Built a new silent 80-second Scale V2 review candidate:
  `docs/submission/GuardianSim-Radeon-Parallel-Futures-review-v4.mp4`,
  SHA-256
  `32c8d1db019f38b0b4221171894cbc76be5ab4a67f249ef7dd93cd2581c8f724`.
- The V4 sequence is:
  `4,096-world Radeon hook → eight-point saturation curve → 4,608 → 5 → 1
  Safety Swarm funnel → accepted Seed 411 replay → frozen 30-scenario result
  → move-or-stop architecture`.
- Candidate cells A05/A07/A09/A11/A13 match the five qualifying indices in the
  preserved Safety Swarm V2 formal report. The replay remains the accepted
  original evidence video rather than a reconstructed animation.
- Strict V4 validation passed full 1920×1080, 20 FPS, 80.0-second decode, all
  evidence hashes, frozen metrics, chapter bounds, simulation-only boundaries,
  and explicit silent-audio state.
- Updated the narration builder and validator for a future narrated V5, but did
  not call the remote TTS service. Visual approval comes before narration
  generation.
- This checkpoint does not replace the released package PDF, public Pages
  build, organizer PR, or accepted earlier videos. It stops at the local
  release-candidate gate.

## Scale V2 narrated V5 candidate — 2026-07-31

- After owner approval of the silent V4 direction, generated a separate Qwen
  `Ethan` narrated candidate at
  `docs/submission/GuardianSim-Radeon-Parallel-Futures-narrated-v5.mp4`.
- Final V5 SHA-256:
  `d590a711950b17a096361e0b7ba39b9842a848c7b0cf7b78d2aff63b5eab8f8d`.
  The sidecar binds it to silent V4 SHA-256
  `32c8d1db019f38b0b4221171894cbc76be5ab4a67f249ef7dd93cd2581c8f724`.
- All six narration segments finish within their frozen chapter windows. Spare
  time is 1.440, 4.400, 4.160, 3.760, 2.080, and 4.320 seconds respectively.
  The close was shortened instead of accelerating speech after two slower
  natural-voice candidates correctly failed the timing guard.
- Final audio is 96 kHz mono AAC. The earlier accepted loudness process remains
  `-16 LUFS` target normalization; post-mux volume inspection recorded
  approximately `-18.4 dB` mean and `-1.1 dB` maximum sample level.
- Fixed captions were visually checked at all chapter positions and remain
  inside the 1,920 × 1,080 frame without covering headline metrics.
- Strict V5 validation passed full audio/video decode, narration and caption
  hashes, immutable visual identity, source hashes, locked metrics, and claim
  boundaries.
- The Qwen key remained in the ignored local environment and was not written
  to logs, metadata, sidecars, or tracked files.
- V5 remains a local review candidate. No commit, push, public package
  replacement, Pages deployment, or organizer PR update occurred.

## V4 local official-package candidate verified — 2026-08-01

- After owner approval of narrated V5, replaced the local official-package
  candidate with the eight-page Scale V2 technical report, the approved
  80-second narrated V5 preview, and the strict Scale V2 report and validation
  receipt. Historical Parallel Futures and Safety Swarm evidence remain in the
  package with explicit unit boundaries.
- Updated the package README to show the complete eight-point
  `1/16/64/256/512/1024/2048/4096` scale curve and the verified largest-batch
  result: `50,331,648` measured environment steps at
  `152,099.018 environment-steps/s`, `1,028.069x` speedup,
  `98.651%` mean / `99%` peak GPU utilization, and approximately `6.25 GiB`
  peak VRAM.
- Regenerated the package checksum manifest. `SHA256SUMS` SHA-256 is
  `f8a18439e1b1009ae807e79142f499df4a65de939c7f5e83729e0647afd8b0bd`.
- Copied the package into a clean temporary directory and verified all ten
  manifest entries, JSON/schema receipts, exact PDF/video/Scale V2 artifact
  identities, and a complete audio/video decode. The candidate contains ten
  payload files plus the manifest and totals `3,551,598` bytes.
- The package text contains no superseded Scale V1 headline. V3 figures remain
  only in labeled historical release records and preserved historical raw
  evidence.
- This is a local release candidate only. No commit, V4 tag, push, Pages
  deployment, organizer PR mutation, or public URL was created. The planned
  `hackathon-2026-submission-v4` tag must bind to the finally approved exact
  source commit and pass fresh public-link checks before release.
- Final local gate passed 108/108 Python tests, Python compilation, 5/5
  server-rendered showcase tests, 3/3 static Pages tests, both showcase builds,
  ESLint, strict silent-V4 and narrated-V5 media validation, strict Scale V2
  validation, package checksum verification, full packaged A/V decode, and
  `git diff --check`.

## Public V4 release completed — 2026-08-01

- Published source commit
  `0710dca1de8e7627c19a992164169c41e70ac338` from
  `agent/parallel-futures-showcase` and created annotated tag
  `hackathon-2026-submission-v4`. GitHub's tag object peels to that exact
  commit; V1–V3 tags were not moved.
- Published the tested Scale V2 Pages build to `gh-pages` commit
  `43af7d9578ff0f992fd1b3b242e59400123ede8f`. The live site serves
  `assets/index-DaWXZz3t.js` with the 4,096-world, 152,099 env-steps/s,
  98.51-million-step, and PPO/VLA-to-Radeon narrative.
- Synchronized only `submissions/Track3-Aegis-Motion-GuardianSim` in the
  contest fork and pushed commit
  `2dad3d4037b4cf7c3ed7dd6a8ea64df874dc7f62`.
- Updated existing organizer PR #39 in place; no new PR was opened. Verified
  title `Track 3, Aegis Motion, GuardianSim`, state `OPEN`, non-draft,
  `MERGEABLE`, and head commit `2dad3d4037b4cf7c3ed7dd6a8ea64df874dc7f62`.
- A fresh GitHub API archive of the organizer branch passed all ten package
  checksums and reproduced manifest SHA-256
  `f8a18439e1b1009ae807e79142f499df4a65de939c7f5e83729e0647afd8b0bd`.
- Anonymous HTTP checks returned 200 for the V4 tag, reproduction guide,
  workflow video, narrated V5 preview, source evidence, organizer PDF, PR, and
  Pages site. The PR remains unmerged for organizer review.
- Git transport had two transient connection failures during independent clone
  checks. The authenticated GitHub API archive provided the independent remote
  verification instead; no evidence or remote ref was altered by those
  failures.
- Unrelated local V1–V3 review artifacts, browser cache, historical PDF
  candidates, and Radeon Cloud instance state were left untouched.

## Post-release judge red-team audit — 2026-08-01

- Re-read the official Luma page, governing Rules & Conditions, and organizer
  README. The verified Track 3 scoring weights are robot capability `30`,
  Radeon/ROCm adoption `20`, innovation `20`, application value `20`, and
  upstream open-source contribution `10`.
- PR #39 remains open, non-draft, and mergeable. It has no comments, reviews,
  review decision, or status checks. Its package head remains
  `2dad3d4037b4cf7c3ed7dd6a8ea64df874dc7f62`.
- Six Track 3 submissions were open at inspection time. The material new
  entries are SmolVLA fruit sorting (#45) and Chaal (#49). Chaal has the
  strongest training/scale/upstream story; SmolVLA has a compact end-to-end
  LeRobot path and a genuine upstream compatibility issue.
- GuardianSim should not compare its environment-step throughput with Chaal's
  PPO training throughput as if the units were interchangeable. Its strongest
  category remains a policy-agnostic safety decision layer with full
  manipulation scenes, frozen safety outcomes, and auditable evidence.
- The highest-value post-release improvement is a 90-second judge path and an
  explicit official-criteria evidence map in PR #39. No new benchmark is
  justified before this navigation problem is solved.
- No external upstream patch is claimed. Do not manufacture one before the
  deadline. The honest score-path audit is stored in
  `docs/submission/JUDGE_RED_TEAM_2026-08-01.md`.
- The immutable V4 tag and all frozen reports, thresholds, and evidence remain
  unchanged.
- Published only the prepared PR-body navigation update to organizer PR #39.
  After the edit, the PR remained `OPEN`, non-draft, and `MERGEABLE`; its head
  remained `2dad3d4037b4cf7c3ed7dd6a8ea64df874dc7f62`, with zero comments,
  reviews, and checks. The normalized local and remote bodies matched at
  SHA-256 `f20b120aee0123fe122b6d1241984f051a87266a7bc326ab9000102bed6c5da1`.

## Final submission lock — 2026-08-01

- Owner chose submission hardening and monitoring instead of attempting a
  last-minute upstream contribution.
- Completed anonymous link checks for eleven judge-facing endpoints, fresh
  organizer-branch archive verification, all ten package checksums, strict
  Scale V2 validation, strict full-decode validation of both published videos,
  and all 108 Python unit tests.
- Fixed the only access-friction issue found: the technical report and
  organizer evidence directory in PR #39 are now direct links rather than
  backtick-only paths. Final normalized PR-body SHA-256 is
  `465d1d5c5bf4c6ce59bbc4cc5d945d1ee6cfb37bb45f410c7f64bcf874ce7b0c`.
- PR #39 remains `OPEN`, non-draft, and `MERGEABLE` at unchanged package head
  `2dad3d4037b4cf7c3ed7dd6a8ea64df874dc7f62`, with no comments, reviews, or
  checks.
- Source V4 remains fixed at
  `0710dca1de8e7627c19a992164169c41e70ac338`; package manifest remains
  `f8a18439e1b1009ae807e79142f499df4a65de939c7f5e83729e0647afd8b0bd`.
- Freeze policy and final identities are recorded in
  `docs/submission/FINAL_SUBMISSION_LOCK_2026-08-01.md`. From this point, make
  public changes only for organizer feedback, broken links, or material
  factual, licensing, security, or eligibility errors.
