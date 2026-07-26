# GuardianSim Worklog

This is an append-only record of implementation and experiment activity. Keep
claims factual and link to durable evidence.

## 2026-07-24 — Repository bootstrap and Gate 1

### Local implementation

- Forked the retained AMD competition reference pipeline into GuardianSim.
- Added candidate generation, risk scoring, failure diagnosis, bounded recovery,
  a Genesis evaluator protocol, and baseline-vs-GuardianSim report export.
- Added seven unit tests covering candidate generation, state restoration,
  scoring, failure handling, recovery, and benchmark behavior.
- Added Radeon Cloud setup, verification, session, and GPU-budget scripts.

Commits:

- `2119d0d` — `feat: add Genesis evaluation and benchmark pipeline`
- `2283818` — `fix: pin Genesis-compatible NumPy image stack`

### Radeon Cloud Session A

Approximate active work window: 17:16–18:00 China Standard Time.

Environment checks:

```text
Python 3.12.3
PyTorch 2.9.1+gitff65f5b
HIP 7.2.53211-e1a6bc5663
GPU available: True
GPU: AMD Radeon Graphics
```

Installation:

```bash
uv pip install --python /opt/venv/bin/python -e .
```

Two dependency problems were discovered and resolved:

1. `scikit-image==0.22.0` was incompatible with the installed NumPy 2 ABI.
2. Upgrading without an upper bound selected NumPy 2.5.1, which Numba rejected.

The resulting project constraints are:

```text
numpy>=1.26.4,<2.3
scikit-image>=0.25.2
```

Verification results:

- GuardianSim tests: 7/7 passed.
- Genesis GPU probe: passed for 20 steps.
- World and wrist frames: captured and visually inspected.
- Reference task: `011_banana -> 024_bowl`.
- Reference result: `success = True`.
- Reference frames: 8.

Commands:

```bash
/opt/venv/bin/python scripts/probe_genesis.py \
  --steps 20 \
  --save-frames \
  --output-dir outputs/evidence/genesis-probe

PYTHONUNBUFFERED=1 /opt/venv/bin/python \
  franka_fruit_pick/grasp_demo.py \
  --pick 011_banana \
  --place 024_bowl \
  --save-frames
```

Durable evidence:

- [`evidence/session-a/README.md`](evidence/session-a/README.md)
- [`evidence/session-a/world.png`](evidence/session-a/world.png)
- [`evidence/session-a/wrist.png`](evidence/session-a/wrist.png)
- [`evidence/session-a/baseline-banana.gif`](evidence/session-a/baseline-banana.gif)
- Commit `64991a7` — `docs: add Radeon Cloud session A evidence`

Session exit:

- `scripts/end_gpu_session.sh` completed.
- GPU was idle at the final check.
- Code and critical evidence were copied off the instance and pushed.
- Final cloud-instance destruction remained pending explicit owner confirmation.

### Gate decision

Gate 1 is complete. Gate 2 must begin with local implementation of a concrete,
snapshot-safe Genesis rollout backend. No additional GPU session should be
launched until the five-candidate dry-run command and expected outputs are
defined and locally tested.

## 2026-07-24 — Gate 2 local implementation

### Cloud access and Session A shutdown

- Created a dedicated ED25519 key for GuardianSim Radeon Cloud access.
- Saved only the public key to the Radeon Cloud profile.
- Verified the profile displayed `SSH public key saved` and `Key on file`.
- Key fingerprint:
  `SHA256:8VLTCjgZI8Ufo+CTDck01Zv8WUJMgPw9zTFa/FPF83Q`.
- Requested destruction of instance `u-13907-735d71cb`.
- The platform changed its status to `Shutting down`, reset runtime to
  `0 minutes`, and continued to display 10 available credits / 0 consumed at
  that moment.
- A later profile refresh confirmed `No active instance`; the account still
  displayed 10 available credits and the SSH key remained on file.

The key does not create an SSH endpoint by itself. A future launch must use an
SSH-enabled template and expose a hostname and port.

### Counterfactual rollout implementation

- Added a stable, canonical SHA-256 fingerprint for each initial episode state.
- Added capture/restore of Franka qpos and all YCB object poses.
- State restoration uses Genesis setters with `zero_velocity=True`.
- Added physical rollout trace conversion:
  - distal-link/non-target AABB clearance;
  - reachability;
  - relative grasp alignment;
  - retained object lift;
  - sampled end-effector path length;
  - explicit perception-uncertainty prior.
- Added candidate-relative grasp pose geometry.
- Added a real Genesis grasp-and-lift candidate executor using the retained
  Franka motion primitives.
- Added `scripts/run_candidate_dry_run.py` for an exact five-candidate,
  fixed-snapshot Session B run.
- Local result: 13/13 unit tests passed and all Python files compiled.
- Milestone commit: `c658a39` —
  `feat: add snapshot-safe Genesis candidate rollouts`.

The local implementation is not competition evidence until the dry run executes
successfully on Radeon Cloud.

## 2026-07-25 — Radeon Cloud Session B

### Five-candidate dry run

- Launched `Blank OpenCode Workspace` instance `u-13907-735d71cb`.
- Verified PyTorch/HIP and Genesis on one AMD Radeon GPU.
- Genesis reported backend `gs.amdgpu`, version `1.2.3`, and 47.98 GB device
  memory.
- Pulled the Gate 2 implementation and ran all tests.
- The first five-candidate simulation completed its rollouts but failed during
  JSON export because simulator numeric values included `float32` scalars.

### Serialization fix

- Added `guardian_sim.serialization.json_default`.
- Added conversion for scalar values exposing `.item()` and array-like values
  exposing `.tolist()`.
- Added a regression test.
- Local verification: 14/14 tests passed, `compileall` passed, and
  `git diff --check` passed.
- Commit: `004e47c` — `fix: serialize simulator numeric values`.

### Successful fixed-seed rerun

Command:

```bash
PYTHONUNBUFFERED=1 /opt/venv/bin/python \
  scripts/run_candidate_dry_run.py \
  --pick 011_banana \
  --seed 41 \
  --output outputs/guardian_dry_run/candidates.json
```

Verified result:

- Cloud tests: 14/14 passed.
- Exit code: `0`.
- Five candidates ranked from one restored snapshot.
- Best candidate: `yaw_+00.0_offset_+0.000`.
- Best predicted success: `0.46479433192676345`.
- Best utility: `0.7509158463377993`.
- Exact evidence:
  [`evidence/session-b/candidates.json`](evidence/session-b/candidates.json).

Stage-gate finding:

- All candidates reported `collision_margin_m = 0.0`.
- The ranking still discriminates yaw using alignment, retained-lift stability,
  and path length, but the safety score is not yet calibrated.
- The agreed next decision point is metric diagnostics plus lateral-offset
  candidates, not an immediate 20-episode expansion.

Instance state:

- The owner explicitly requested that Session B remain running.
- The profile continued to show 10 available credits and 0 consumed after an
  extended runtime.

## 2026-07-25 — Gate 2.5 local clearance diagnostics

- Added structured clearance diagnostics to every Genesis rollout:
  - sample index and simulator step;
  - responsible Franka link and named obstacle;
  - support-surface flag;
  - exact AABB contact versus strict overlap;
  - strict-overlap depth.
- Critical-pair selection keeps the minimum separation and, when several pairs
  have zero separation, retains the pair with the deepest overlap.
- Expanded the diagnostic command's default candidate matrix from five
  zero-offset yaw candidates to 15 actions:
  five yaw angles crossed with lateral offsets `-0.02, 0.00, +0.02 m`.
- Bumped the diagnostic evidence schema from version 1 to version 2.
- Local verification: 16/16 tests passed, all Python modules compiled, and
  `git diff --check` passed.

Gate constraint:

- Only one fixed-snapshot 15-candidate cloud diagnostic is authorized next.
- Do not begin the 20-episode benchmark until the responsible clearance pairs
  and overlap depths have been reviewed.

## 2026-07-25 — Gate 2.5 Radeon Cloud diagnostic

- Pulled commit `e6bfe2f` on active instance `u-13907-735d71cb`.
- Cloud verification: 16/16 tests passed.
- Ran the default 15-candidate matrix for `011_banana`, seed `41`.
- Process exit code: `0`.
- Exact evidence:
  [`evidence/gate-2-5/candidates.json`](evidence/gate-2-5/candidates.json).

Decisive result:

- All 15 critical pairs were `right_finger -> table_top`.
- Every pair was a strict AABB overlap against a support surface.
- Overlap depths ranged from approximately 1.1 to 1.6 mm.
- The zero-clearance metric is dominated by intentional grasp/support contact,
  so it cannot currently represent clutter-collision safety.

Candidate result:

- Rank 1: `yaw_+00.0_offset_+0.000`, success estimate `0.4648455`.
- Rank 2: `yaw_+00.0_offset_+0.020`, success estimate `0.4640648`.
- All five `offset_-0.020` candidates retained zero requested lift and ranked
  11–15.
- Lateral offsets materially distinguish grasp outcomes and remain in scope.

Gate decision:

- Do not run the 20-episode benchmark yet.
- Proposed Gate 2.6 separates support-contact depth from clutter clearance,
  then performs one final fixed-snapshot 15-candidate validation.
- The cloud instance remains running per owner instruction.

## 2026-07-25 — Gate 2.6 two-channel safety implementation

- Split the rollout recorder into two independent critical-pair channels:
  - non-support clutter clearance, which feeds `collision_margin_m`;
  - support contact, which remains diagnostic-only.
- Added `support_contact_diagnostic` to raw Genesis measurements and normalized
  candidate metrics.
- Kept named sample, link, obstacle, overlap state, and depth in both channels.
- Bumped diagnostic evidence schema to version 3.
- Added a regression test proving support-contact depth does not change the
  collision-risk score when clutter clearance is unchanged.
- Local verification: 17/17 tests passed, Python compilation passed, and
  `git diff --check` passed.

## 2026-07-25 — Gate 2.6 Radeon Cloud validation

- Pulled commit `98624d6` on active instance `u-13907-735d71cb`.
- Cloud verification: 17/17 tests passed.
- Ran the fixed-snapshot 15-candidate matrix for `011_banana`, seed `41`.
- Process exit code: `0`; evidence schema version: `3`.
- All candidates shared snapshot fingerprint
  `347dfaf0e99c698474afbf06091886915fabf91fafe61581e8c6762685b2bc8b`.
- Non-support clutter clearance ranged from `0.0353657 m` to `0.0806255 m`;
  no clutter critical pair overlapped.
- The critical clutter obstacle was `018_plum`, measured against `hand` for
  12 candidates and `left_finger` for three.
- Intentional `right_finger -> table_top` overlap remained visible in the
  support-only channel for all 15 candidates.
- Best candidate changed to `yaw_-22.5_offset_+0.000`, with estimated success
  `0.7326756`, clearance `0.0744362 m`, and stability `0.8996660`.
- Gate 2.6 exit criteria passed. The safety metric is non-degenerate and the
  fixed-seed independent-execution benchmark is now authorized.

## 2026-07-25 — Fixed-seed real benchmark implementation

- Added deterministic fixed-seed XY perturbations while preserving robot state
  and object orientation.
- Added a real-execution classifier requiring reachability, retained-lift
  stability of at least `0.60`, and no non-support clutter overlap.
- Added a resumable JSON benchmark command that writes after every episode.
- Every episode evaluates all 15 counterfactual candidates and then independently
  re-executes both the nominal baseline and GuardianSim's selected candidate.
- Episode snapshots record the actual episode seed in their fingerprints.
- Added aggregate success-rate, stability, clutter-clearance, candidate-selection,
  and absolute-lift summaries.
- Added validated continuation from a completed seed prefix. Resume is rejected
  if the configuration, seed sequence, or rebuilt base-snapshot fingerprint
  differs; `--fresh` is required to overwrite incompatible evidence.
- Local verification: 21/21 tests passed, Python compilation passed, and
  `git diff --check` passed.

## 2026-07-25 — Gate 2.7 twenty-episode Radeon Cloud benchmark

- Ran commit `f0cc4e3` on instance `u-13907-735d71cb`.
- Completed all 20 paired episodes for seeds `101–120`.
- Verified 20 unique episode snapshot fingerprints and normal Genesis exit.
- Baseline: 20/20 success, mean clearance `0.04399 m`, mean stability `0.90413`.
- GuardianSim: 17/20 success, mean clearance `0.07438 m`, mean stability
  `0.76416`.
- GuardianSim increased clearance in every episode by a mean `0.03038 m`, but
  reduced success by 15 percentage points and stability by a mean `0.13996`.
- Failures were seeds 104, 107, and 120. All selected
  `yaw_-22.5_offset_-0.020`; counterfactual success estimates were
  `0.70665–0.85040`, but independent stability was `0.0`.
- Decision: one-shot counterfactual ranking is not repeatable enough. Gate 2.7
  is preserved as negative evidence. Next revision requires repeated
  confirmation, conservative aggregation, and a nominal stability fallback.
- Raw evidence:
  [`evidence/gate-2-7/README.md`](evidence/gate-2-7/README.md).

## 2026-07-25 — Gate 2.8 robust-selection policy declared

- Added repeatability-aware candidate selection as a separate decision module.
- Initial scoring still covers all 15 candidates.
- The top-three shortlist plus nominal receives two additional confirmation
  rollouts per candidate.
- Repeated metrics are aggregated pessimistically: minimum reachability,
  alignment, stability, and clearance; maximum path length and uncertainty.
- Alternatives require worst-observed stability `>= 0.60` and robust predicted
  success at least `0.02` above nominal; otherwise the planner falls back.
- Evidence schema 3 records all confirmation observations and fallback state.
- TDD behavior coverage proves:
  - a lucky high-clearance candidate cannot beat a repeatably stable action;
  - marginal improvements fall back to nominal;
  - a repeatably superior alternative can still be selected.
- Local verification: 24/24 tests passed, compilation and whitespace checks
  passed.
- Cloud gate: rerun seeds 104, 107, and 120 independently before authorizing
  another 20-seed benchmark.

## 2026-07-25 — Gate 2.8 Radeon Cloud benchmark

- Pulled commit `3c63236` on instance `u-13907-735d71cb`.
- Cloud verification passed 24/24 tests.
- Authorized one-episode smoke reruns for seeds 104, 107, and 120 all completed
  successfully with full confirmation evidence.
- Because all three smoke gates passed, ran the predeclared robust-selection
  policy on seeds `101–120` without changing thresholds.
- Process exit code: `0`; evidence schema version: `3`.
- Verified 20 completed episodes, contiguous seeds, and 20 unique episode
  snapshot fingerprints.
- The report contains 240 confirmation observations: four candidates per
  episode with one initial and two additional rollouts each.
- Baseline: 20/20 success, mean clutter clearance `0.04399 m`, mean stability
  `0.90338`.
- GuardianSim: 20/20 success, mean clutter clearance `0.07212 m`, mean
  stability `0.89731`.
- GuardianSim therefore preserved baseline success while increasing mean
  clutter clearance by `0.02813 m` (`+63.93%`); mean stability was lower by
  `0.00607`.
- Compared with Gate 2.7, GuardianSim success improved by 15 percentage points
  and mean stability improved by `0.13315`; mean GuardianSim clearance decreased
  by `0.00226 m`.
- Nominal fallback activated once, on seed 113, and succeeded.
- The prior failure seeds 104, 107, and 120 all succeeded in the full run.
- Raw evidence:
  [`evidence/gate-2-8/README.md`](evidence/gate-2-8/README.md).
- Evidence and resume-showcase commit: `2b3ffe1`.

## 2026-07-25 — Gate 3 judge-facing evidence showcase

- Built a standalone interactive presentation from frozen Gate 2.7 and Gate 2.8
  evidence; the site does not rerun Genesis or consume cloud GPU time.
- The first viewport leads with verified 20/20 paired success, `+63.93%` mean
  clutter clearance, and 240 confirmation observations.
- Added an interactive failure → policy → proof narrative, benchmark comparison,
  candidate-selection distribution, recovered failure-seed table, and system
  architecture.
- Added a 90-second presenter mode and direct downloads for the schema-3 report
  and cloud exit screenshot.
- Added an explicit simulation-only claim boundary throughout the site.
- Generated and validated a project-specific social preview card.
- Production build passed; rendered-content and evidence-integrity tests passed
  2/2.
- Local launch command: `./scripts/run_showcase.sh`.
- Sites version 1 deployed successfully with owner-only access:
  <https://guardiansim-proof.dghcdtddgh.chatgpt.site>.
- Public access was not enabled without explicit owner approval.

## 2026-07-25 — Gate 3.1 adversarial protocol declared locally

- Reviewed the official Track 3 scoring rubric and the two currently public
  Track 3 submissions. The largest GuardianSim evidence gaps are difficult-task
  capability, measured AMD performance, and upstream contribution.
- Declared a balanced 30-episode Genesis challenge before inspecting any cloud
  outcome:
  - three pick objects: banana, lemon, and plum;
  - lateral and radial close-clutter layouts;
  - five repetitions per object/layout cell;
  - contiguous seeds `301–330`.
- Protocol SHA-256:
  `472bb6ea13984dff02124c091ac8d94c67154bbe68858bb782aed8014d2afbba`.
- Exact scenario-matrix SHA-256:
  `b3ba08b367a0c634f66ddbba8670311c9b449aaa4ad7ee55d418bca7c2147936`.
- Added deterministic target XY/yaw, shared friction, and target-mass
  perturbations.
- Close clutter uses conservative mesh footprint radii plus a fixed `0.012 m`
  initial gap. Non-participating entities are parked away from the challenge
  pair to avoid initial-overlap artifacts.
- Split outcomes into:
  - ordinary task success;
  - margin-aware safe completion with a predeclared `0.010 m` minimum clutter
    clearance;
  - actual clutter contact and failure taxonomy.
- Retained the Gate 2.8 selection policy without threshold changes.
- Added schema-4 report generation, per-phase wall timing, resumable smoke
  prefixes, and a validator that rejects protocol drift, scenario reordering,
  duplicate fingerprints, missing independent evidence, and summary mismatch.
- Local verification: 30/30 unit tests passed; compilation and whitespace
  checks passed.
- No Gate 3.1 Radeon Cloud result has been run or inspected.
- Protocol:
  [`GATE_3_1_PROTOCOL.md`](GATE_3_1_PROTOCOL.md).

## 2026-07-25 — Gate 3.1 two-episode Radeon Cloud smoke gate

- Ran the first two frozen scenarios on Radeon Cloud instance
  `u-13907-735d71cb` without changing any protocol value or selection
  threshold.
- Cloud verification after deployment: 30/30 unit tests passed.
- Found and fixed a validator-only JSON representation defect:
  `dataclasses.asdict` retained a tuple in memory while persisted JSON restored
  it as a list. Canonical scenario serialization now makes validation stable
  across a JSON round trip; the scenario values and protocol hashes are
  unchanged.
- Partial schema-4 validation passed for `2/30` episodes after the fix.
- Preliminary smoke outcomes, not a formal performance claim:
  - task success: baseline `2/2`, GuardianSim `2/2`;
  - safe completion: baseline `1/2`, GuardianSim `2/2`;
  - the baseline miss was a `clearance_violation`, not clutter contact;
  - mean clutter clearance: baseline `0.03207 m`, GuardianSim `0.08251 m`;
  - mean stability: baseline `0.90082`, GuardianSim `0.89674`;
  - planning wall time: `176.53 s` and `172.81 s`.
- Raw report and cloud log:
  [`evidence/gate-3-1-smoke/README.md`](evidence/gate-3-1-smoke/README.md).
- Validator fix commit: `e68753a`.
- Major-stage decision boundary reached: do not start the remaining 28 episodes
  until the owner reviews smoke quality, runtime, and the formal-run route.

## 2026-07-26 — Gate 3.1 formal 30-episode Radeon Cloud benchmark

- Resumed the validated schema-4 report at `2/30` and completed the frozen
  seeds `301–330` without changing protocol values, policy thresholds, scenario
  order, or prior evidence.
- Full protocol validator exited `0`; cloud tests passed 30/30; the downloaded
  report passed a second full local validation.
- Primary endpoint was negative:
  - baseline safe completion: `19/30` (`63.33%`);
  - GuardianSim safe completion: `18/30` (`60.00%`);
  - paired absolute difference: `-3.33` percentage points.
- Secondary outcomes:
  - ordinary task success: baseline `20/30`, GuardianSim `18/30`;
  - clutter contact: both `10/30`;
  - mean clutter clearance: baseline `0.02157 m`, GuardianSim `0.03099 m`
    (`+43.67%`);
  - mean stability: baseline `0.90845`, GuardianSim `0.85091`.
- Paired safe outcomes: both safe 17, both unsafe 10, GuardianSim-only safe 1,
  baseline-only safe 2.
- The current candidate family failed structurally in lemon/lateral and
  plum/lateral: both strategies contacted clutter in all five episodes of each
  cell.
- GuardianSim had two additional unstable lifts:
  lemon/radial seed 318 and plum/radial seed 326.
- Nominal fallback activated in 19/30 episodes.
- Mean planning time was `184.84 s` per episode; baseline and GuardianSim
  independent execution averaged `8.68 s` and `8.56 s`.
- Interpretation: higher average clearance did not generalize into higher safe
  completion. Preserve this result and redesign the action space before any
  later gate; do not retune Gate 3.1.
- Raw evidence:
  [`evidence/gate-3-1/README.md`](evidence/gate-3-1/README.md).

## 2026-07-26 — Gate 3.2 protocol and implementation frozen locally

- Diagnosed Gate 3.1 from raw episode evidence before designing a new gate:
  - some lemon/lateral alternatives were collision-free, but the old selector
    could still fall back to an overlapping nominal candidate;
  - the confirmed plum/lateral shortlist contained no safe candidate;
  - two GuardianSim-only unstable final executions occurred despite stable
    counterfactual observations.
- Declared a fresh 30-scenario matrix on unseen seeds `401–430`; Gate 3.1 seeds
  are not reused for the formal result.
- Added an 18-action obstacle-aware family:
  - nine yaws from `-90°` to `90°`;
  - centered and `0.025 m` global obstacle-retreating targets;
  - `0.14 m` non-nominal approach height.
- Added a safety-first selector:
  - hard safety filter before ranking;
  - top-five plus nominal, with three confirmation rollouts;
  - stability floor `0.70`, clearance floor `0.010 m`;
  - unsafe nominal must be replaced by a safe alternative or produce
    `safe_stop`.
- Added three independent final executions per strategy. Repeatable safe
  completion requires 3/3 safe executions; safe-stop is recorded as neither
  task success nor safe completion.
- Added schema-5 resumable runner, summary, and validator with full initial,
  confirmation, execution, safe-stop, timing, and fingerprint evidence.
- Every resumable checkpoint is validated before write. Validation rejects
  incomplete 18-candidate initial evidence, missing four-observation
  confirmations, duplicate execution-repeat indices, decision/action
  contradictions, and aggregate or summary drift.
- Protocol SHA-256:
  `8f23247001e05f39817225ed13f028321fbb9b9c694aaacd5b987fe61ee1fb3c`.
- Scenario-matrix SHA-256:
  `69f87994b87f2def788cd944ad75210cdeddeafcaa3d0a3844fef04efca9cb03`.
- Local verification: 39/39 tests passed; compilation and whitespace checks
  passed.
- No Gate 3.2 cloud outcome has been inspected.
- Protocol:
  [`GATE_3_2_PROTOCOL.md`](GATE_3_2_PROTOCOL.md).

## 2026-07-26 — Gate 3.2 Radeon Cloud engineering smoke complete

- Pulled frozen implementation commit `67d3235` on Radeon Cloud instance
  `u-13907-735d71cb`.
- Cloud unit tests passed 39/39.
- Ran only the predeclared prefix seeds `401–402` with
  `--max-new-scenarios 2 --fresh`.
- Both resumable checkpoints passed the schema-5 partial validator.
- Evidence completeness:
  - 18/18 initial candidate metrics per episode;
  - five or six confirmed candidates, each with four observations;
  - three final executions for both baseline and GuardianSim;
  - protocol identity, scenario order, timing, fingerprints, aggregates, and
    stored summary all validated.
- Engineering smoke outcomes, not formal performance claims:
  - baseline repeatable safe completion: `2/2`;
  - GuardianSim repeatable safe completion: `2/2`;
  - clutter contacts: zero for both;
  - mean clearance: baseline `0.0479732 m`, GuardianSim `0.0927164 m`;
  - mean stability: baseline `0.902032`, GuardianSim `0.860738`;
  - both decisions were `higher_margin_alternative`;
  - selected actions were centered yaw `-45°` and yaw `-22.5°` with
    `0.025 m` obstacle retreat;
  - planning wall time: `269.55 s` and `266.57 s`.
- Genesis emitted intermittent RRTConnect planning-failed/retrying messages,
  but both episodes completed, reports were written, and validation exited
  successfully.
- Cloud archive created at
  `outputs/gate-3-2/gate-3-2-smoke-evidence.tar.gz`, containing the raw report,
  log, validation output, cloud test log, and SHA-256 manifest.
- Automatic browser download was blocked by browser security policy. The
  archive remains visible in the Jupyter file browser for one manual owner
  download; no formal run has started.

## 2026-07-26 — Gate 3.2 smoke evidence retrieved and verified locally

- Downloaded the 14 KB cloud archive through the owner-controlled Jupyter UI.
- Archive SHA-256:
  `f2545cfe89708e2626976d357eb7aabab0b68c0b45913005a23675878b2a61dd`.
- All four raw files passed the cloud-generated SHA-256 manifest locally.
- The local schema-5 validator reproduced the cloud protocol SHA, completed
  episode count `2`, and complete stored summary exactly.
- Local tests passed 39/39.
- Raw and local validation evidence:
  [`evidence/gate-3-2-smoke/README.md`](evidence/gate-3-2-smoke/README.md).
- No formal Gate 3.2 scenario beyond the two engineering smoke seeds has run.

## 2026-07-26 — Gate 3.2 formal Radeon Cloud benchmark complete

- The owner approved the formal run after reviewing the two-scenario
  engineering smoke.
- The original `smoke-report.json` remained unchanged at 2/30 with SHA-256
  `8ec01ff4b2bc19ee5512796f1609fb8e86b6df082dade728713c1560b2f9ac23`.
- Two attempts to append the smoke prefix from a new Genesis process were
  rejected by the frozen strict resume validator because the captured
  base-scene snapshot fingerprint differed. Both rejection logs were
  preserved; no `--fresh` flag was used.
- To avoid combining evidence from different base snapshots, launched
  `formal-report.json` as a separate output and ran all 30 frozen scenarios in
  one process on the AMD Radeon GPU.
- Protocol and scenario order were not changed:
  - protocol SHA-256:
    `8f23247001e05f39817225ed13f028321fbb9b9c694aaacd5b987fe61ee1fb3c`;
  - scenario-matrix SHA-256:
    `69f87994b87f2def788cd944ad75210cdeddeafcaa3d0a3844fef04efca9cb03`.
- Strict complete schema-5 validation passed 30/30 episodes.
- Verified primary endpoint:
  - baseline repeatable safe completion: `18/30` (`60%`);
  - GuardianSim repeatable safe completion: `30/30` (`100%`);
  - paired absolute lift: `+40.00` percentage points.
- Verified secondary outcomes:
  - independent safe executions: baseline `58/90`, GuardianSim `90/90`;
  - clutter-contact executions: baseline `30`, GuardianSim `0`;
  - mean clearance: baseline `0.023191 m`, GuardianSim `0.046003 m`;
  - mean stability: baseline `0.892762`, GuardianSim `0.905099`;
  - GuardianSim decisions: 11 `higher_margin_alternative`, 10
    `unsafe_nominal_replaced`, and 9 `eligible_nominal_fallback`;
  - mean planning wall time: `264.95 s` per scenario;
  - mean independent execution wall time: baseline `9.08 s`, GuardianSim
    `8.94 s`.
- Cloud evidence was validated, archived, downloaded through the Jupyter
  Download action, and rehashed locally.
- Evidence archive SHA-256:
  `57b53cda9d4352cb2d99ae9da01e1051840705725002a9e32e4076493b7b84ad`.
- Raw report, logs, validator output, environment record, manifests, failed
  resume audit trail, and smoke/formal separation rationale:
  [`evidence/gate-3-2/README.md`](evidence/gate-3-2/README.md).
- The Radeon Cloud instance remains running per the owner's instruction.

## 2026-07-26 — Gate 3.2 judge showcase and resume package

- Reworked the existing judge-facing site from the earlier Gate 2.7/2.8 story
  to the final Gate 3.1 failure → Gate 3.2 frozen fix → formal proof narrative.
- The first viewport now leads with only verified claims:
  - repeatable safe completion `18/30` → `30/30`;
  - absolute lift `+40.00` percentage points;
  - clutter-contact executions `30` → `0`;
  - mean clearance `+98.36%`.
- Updated the interactive 90-second presenter mode, decision taxonomy,
  adversarial-cell recovery table, architecture explanation, immutable raw
  evidence links, and explicit simulation-only claim boundary.
- Replaced the social preview with a project-specific 1200×630 card containing
  the verified Gate 3.2 metrics.
- Rewrote `RESUME_SHOWCASE_ZH.md` with one-line, three-bullet, 30-second,
  90-second, technical architecture, interview Q&A, and claim-boundary
  variants.
- Updated the repository landing page to make Gate 3.2 the current result while
  preserving Gate 3.1 as negative evidence.
- Showcase production build, two rendered-HTML tests, and ESLint all passed.
- Saved and privately deployed Sites production version 2:
  <https://guardiansim-proof.dghcdtddgh.chatgpt.site>.

## 2026-07-26 — Gate 3.2 visual replay and validation-scale review

- Reviewed external evaluation scales before proposing more GPU work:
  - LIBERO implementations commonly use 50 rollouts per task;
  - RoboCasa evaluates each task across 50 trials;
  - 20-run results appear in focused real-robot demonstrations, but do not
    establish broad benchmark generalization.
- Recorded the statistical boundary of Gate 3.2:
  - 30 paired scenarios are the primary sample, while the 90 executions per
    strategy are nested repeatability checks;
  - paired discordance is 12 improvements and 0 regressions;
  - exact two-sided McNemar p-value is `0.000488`;
  - the 30/30 Wilson 95% interval is approximately `88.65%–100%`.
- Added [`VALIDATION_SCALE_PLAN.md`](VALIDATION_SCALE_PLAN.md) with staged
  visual proof, 24-scenario breadth smoke, 120-scenario robustness gate,
  public-benchmark adapter, and real-robot validation route.
- Added a frame callback that does not change default formal-run behavior and a
  side-by-side visual-replay recorder.
- The first replay attempt exposed an interface mismatch between raw Genesis
  measurements and normalized candidate metrics. Preserved the cloud failure
  log, extracted the shared normalization function, and added a regression
  test.
- Local tests passed 40/40 after the fix.
- Replayed Gate 3.2 seed 411 on Radeon Cloud without modifying the formal
  report:
  - nominal baseline: clutter contact, `0.000000 m` clearance, `0.936245`
    stability;
  - GuardianSim: safe completion, `0.017094 m` clearance, `0.948657`
    stability.
- Downloaded the generated MP4 through the browser's native video control and
  verified its local SHA-256 matched the cloud value:
  `a6b8fa20b924268955c7c40e002faf3b048f5de534f3c19a2ba071f0c7a4e3be`.
- Preserved video, sidecar, preview, and claim boundary under
  [`demo/README.md`](demo/README.md).
- No new formal benchmark was started; the Radeon Cloud instance remains
  running.

## 2026-07-27 — Judge-readable replay revision

- Owner review correctly found that the first five-second replay made the
  physical difference too difficult to see:
  - labels were too small;
  - the plum obstacle was not identified;
  - the contact event was not paused;
  - both strategies lifted the lemon, masking the safety distinction.
- Tested a fresh high-frame-density rerender. It was rejected as presentation
  evidence because the Guardian action produced a `0.004260 m` clearance
  violation in that new process, versus `0.017094 m` in the verified source
  replay. This diagnostic confirms that a new visual rerun must not silently
  replace the preserved replay.
- Implemented presentation-only post-processing of the verified source MP4:
  - no Genesis initialization or physics execution;
  - no additional statistical trial;
  - source MP4 SHA-256 remains
    `a6b8fa20b924268955c7c40e002faf3b048f5de534f3c19a2ba071f0c7a4e3be`;
  - output is 2560×1080, 10 FPS, and 18.1 seconds.
- Added large left/right labels, red/green borders, a projected plum-obstacle
  marker, action descriptions, phase labels, a two-second contact-frame pause,
  and a three-second result card.
- Verified the output in the browser and downloaded it locally.
- Explained MP4 SHA-256:
  `2092b9604fa7d37ab9a67bfc9299258e74eb8d2362e9132e38b4e5d65573b6d7`.
- Recommended presentation asset:
  [`demo/gate-3-2-seed-411-explained-v2.mp4`](demo/gate-3-2-seed-411-explained-v2.mp4).
- Gate 3.2 formal results and thresholds remain unchanged.
