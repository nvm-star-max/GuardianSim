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

## 2026-07-27 — Gate 3.3 multi-factor breadth protocol implemented

- Owner judged the improved visual replay understandable but still visually
  and technically simple, and authorized the next development stage.
- Audited the Gate 3.2 architecture and preserved its frozen report,
  thresholds, protocol hash, and matrix hash.
- Implemented a new 24-scenario engineering-only matrix on seeds `501–524`,
  balanced across:
  - target XY/yaw shifts;
  - tighter/wider clutter gaps and ±35° obstacle-bearing changes;
  - friction and target-mass extremes;
  - deterministic target/obstacle perception bias.
- Separated true physical positions from perceived planning positions.
- Added a conservative risk certificate that subtracts the declared
  target-plus-obstacle position-error bound from measured clearance and records
  explicit failed safety gates.
- Added a Genesis smoke runner, schema-6 strict validator, per-stratum stop
  rules, and seven focused unit tests.
- Protocol SHA-256:
  `5f9497c363c32f8bbabb62e395d5814958e273d3b6d235fb46a7a5f23be6b130`.
- Scenario-matrix SHA-256:
  `c934f3427a937f2cc8594a1408e97d1ed9bf3692fa41af066f2fb8652435e983`.
- Focused Gate 3.3 tests passed 7/7, the full local suite passed 47/47, and all
  new Python files compiled.
- No Gate 3.3 cloud outcome has been inspected. Cloud execution is paused for
  the agreed major-stage route review.

## 2026-07-27 — Gate 3.3 first cloud launch exposed write-boundary defect

- Owner approved the two-scenario engineering smoke.
- Radeon Cloud preflight confirmed:
  - instance `u-13907-735d71cb` remained ready;
  - AMD Radeon GPU was visible;
  - cloud repository had no local changes.
- Switched the detached cloud checkout from `c9d3cd1` to frozen Gate 3.3
  commit `2edd268`.
- Cloud tests passed 47/47 before launch.
- The first process completed the physical work for scenario 501 but exited
  before the first atomic report write:
  `ValueError: Gate 3.3 episode 0 has malformed pose evidence`.
- Root cause: the strict validator accepted only JSON-round-tripped
  list/native-float poses, while the writer validates the equivalent in-memory
  tuple/NumPy-real representation before serialization.
- No report or outcome claim was produced. The raw `smoke.log` is retained on
  the cloud instance.
- Added a pre-serialization regression assertion and normalized equivalent
  tuple/list containers during validation. The fix changes no scenario,
  threshold, selector, protocol payload, or matrix.
- Local tests passed 47/47 after the fix.
- Protocol and matrix hashes remained exactly unchanged.

- The first fix was deployed as commit `27e6970`; cloud tests again passed
  47/47.
- A second physical launch reached certificate normalization but stopped before
  report writing with:
  `TypeError: Object of type bool is not JSON serializable`.
- The value was a NumPy boolean inside the raw clearance diagnostic. The
  project already had a tested NumPy-aware `json_default` adapter, but the new
  validator's internal canonical comparison had not used it.
- Added a NumPy-style boolean regression fixture and routed all internal
  certificate normalization through `json_default`.
- Both failed launches remain non-results and their logs are preserved
  separately. No scenario, threshold, policy, or protocol payload changed.

## 2026-07-27 — Gate 3.3 two-scenario cloud smoke complete

- Deployed commit `5ec31f3` after preserving both failed-launch logs.
- Cloud tests passed 47/47 for the third time.
- Ran only frozen seeds 501–502 with `--max-new-scenarios 2`.
- Both atomic checkpoints passed pre-write schema-6 validation.
- Independent partial validator exited `0` after completion.
- Verified engineering outcomes:
  - baseline safe completion: `2/2`;
  - GuardianSim safe completion: `2/2`;
  - clutter contacts: zero for both;
  - safe stops: zero;
  - mean clearance: baseline `0.062413 m`, GuardianSim `0.090384 m`;
  - mean stability: baseline `0.881576`, GuardianSim `0.879571`;
  - both GuardianSim decisions were `higher_margin_alternative`;
  - selected certified clearances were `0.090467 m` and `0.087469 m` after
    the frozen 4 mm relative-position uncertainty deduction;
  - planning wall time was `246.96 s` and `292.70 s`;
  - no frozen stop condition triggered.
- Downloaded the 17.2 KB cloud evidence archive through Jupyter.
- Archive SHA-256 matched cloud and local:
  `f2040a53f4fbf2172a94df1003feac1137bcf4684bc9281d60f8991780da83ea`.
- All nine files in the cloud-generated manifest passed locally.
- Local partial schema-6 validation reproduced the exact cloud summary,
  protocol hash, matrix hash, completed count, and empty stop-reason list.
- Evidence:
  [`evidence/gate-3-3-smoke/README.md`](evidence/gate-3-3-smoke/README.md).
- This remains engineering smoke evidence and is excluded from formal
  performance claims.

## 2026-07-27 — Gate 3.3 complete pose-shift stratum

- Owner approved the next major stage after reviewing the two-scenario smoke.
- Synchronized Radeon Cloud instance `u-13907-735d71cb` to commit `dac822a`.
- Started a new independent report rather than resuming the two-scenario
  process across a changed Genesis base-snapshot fingerprint.
- Ran the first complete frozen stratum, seeds 501–506, in one process:
  three objects × two clutter layouts.
- The process completed normally and wrote six atomic schema-6 episodes.
- Cloud and local strict partial validators both passed 6/6.
- Frozen protocol and matrix hashes matched the declaration exactly.
- Frozen stop-reason list was empty.
- Verified engineering outcomes:
  - baseline safe completion: `4/6`;
  - GuardianSim safe completion: `6/6`;
  - baseline clutter contacts: `2/6`, both in lateral-clutter scenes;
  - GuardianSim clutter contacts: `0/6`;
  - GuardianSim safe stops: `0/6`;
  - mean clearance: baseline `0.026178 m`, GuardianSim `0.042806 m`;
  - mean stability: baseline `0.908395`, GuardianSim `0.905240`;
  - mean planning wall time: `230.48 s`.
- The selector replaced the unsafe nominal action for lateral lemon seed 503
  and lateral plum seed 505, converting both baseline contacts into safe task
  completions.
- Automatic browser download did not create a local file. Transferred the
  31,184-byte archive as 14 bounded base64 chunks and reconstructed it locally.
- Cloud and local archive SHA-256 matched:
  `fba1e73b1bce8da0079547a312b90389f14ce3f41ee631e99b3571f4ceae780c`.
- Every file in the cloud manifest passed local SHA-256 verification.
- Evidence:
  [`evidence/gate-3-3-pose-shift-stratum/README.md`](evidence/gate-3-3-pose-shift-stratum/README.md).
- Stop before seeds 507–524 for the agreed major-stage direction review.

## 2026-07-27 — Official submission requirements and countdown recorded

- Reviewed the organizer group announcement and screenshot:
  - hackathon is officially open;
  - announced deadline is 2026-08-06 23:59;
  - participants were told to read the Luma Rules & Conditions carefully;
  - organizers emphasized that evaluators must be able to reproduce the work;
  - a technical Q&A was provisionally announced for Friday at 19:00.
- Verified the official contest repository's Track 3 submission requirements:
  - English technical report with application, architecture, dataset,
    AMD-GPU usage, innovation, deliverables, and team contributions;
  - dedicated source repository;
  - detailed environment, dependency, usage, and step-by-step reproduction
    instructions;
  - complete Docker image preferred;
  - 3–5 minute video of the complete command-line/GUI workflow and results;
  - English fork/pull-request submission to the official repository.
- Clarified the environment requirement: the live Radeon Cloud instance is not
  submitted, but the exact configuration and reproducible setup must be.
- Added [`HACKATHON_SUBMISSION_PLAN.md`](HACKATHON_SUBMISSION_PLAN.md) with:
  - source-of-truth hierarchy;
  - current readiness matrix;
  - winning MVP workflow;
  - P0/P1/P2 priorities;
  - daily milestones through August 6;
  - stop/go rules and final acceptance checklist.
- Set internal code/evidence freeze to August 5 at 23:59 GMT+8 and target final
  submission by August 6 at 18:00 GMT+8, subject to manual Luma confirmation.
- The current 12-scenario Gate 3.3 two-strata run remains authorized and
  unchanged. After preservation, no additional benchmark automatically starts;
  clean-room reproduction, English report, and full demo video become P0.
- Luma and the Feishu cloud guide were not programmatically readable. The owner
  must manually review the full Luma text and record any additional condition
  before submission.

## 2026-07-27 — Gate 3.3 two-strata run complete and archived

- Reconnected to the existing Radeon Cloud Jupyter session without destroying
  instance `u-13907-735d71cb`.
- The independent 12-scenario process had completed normally:
  - report count `12/12`;
  - process no longer running;
  - one continuous report covering seeds 501–512;
  - no `--fresh`, report splicing, protocol change, threshold change, or
    scenario-order change.
- Ran the cloud schema-6 validator with `--allow-partial`; exit status was `0`
  and all 12 episodes passed.
- Frozen identities matched:
  - protocol
    `5f9497c363c32f8bbabb62e395d5814958e273d3b6d235fb46a7a5f23be6b130`;
  - matrix
    `c934f3427a937f2cc8594a1408e97d1ed9bf3692fa41af066f2fb8652435e983`.
- Verified overall engineering outcomes:
  - baseline: 7 safe completions, 4 clutter contacts, 1 clearance violation;
  - GuardianSim: 10 safe physical executions, 2 safe stops, zero contacts and
    zero clearance-violating executions;
  - mean clearance: `0.019033 m` baseline versus `0.043547 m` GuardianSim;
  - mean stability: `0.913322` baseline versus `0.916772` GuardianSim;
  - mean planning wall time: `221.53 s`.
- `pose_shift` reproduced the positive 6/6 GuardianSim result.
- `gap_bearing` exposed the main limitation:
  - GuardianSim completed all four actions it executed safely;
  - lateral lemon and plum had no hard-safe action and safe-stopped;
  - baseline had two contacts and one clearance violation in the stratum.
- Strict stored `stop_reasons` remained empty because the frozen implementation
  evaluates cumulative-prefix rates: 2/12 task noncompletions and 2/12 safe
  stops are each 16.67%. The isolated `gap_bearing` rates are 2/6 = 33.33% and
  are preserved as an action-space coverage warning, without changing the
  frozen report.
- Packaged preflight, report, log, PID, validation, final check, checksums,
  boundary note, and both rejected Seed 503 replay attempts.
- The two replay attempts reproduced baseline contact but not the formal
  GuardianSim clearance, so the hard check rejected both. They are diagnostics,
  not presentation videos or performance results.
- Transferred the 59,479-byte archive as seven bounded base64 chunks.
- Cloud and local archive SHA-256 matched:
  `49ce9196de91f997f7233a4f4533e94292d0b502e8b2cc85fdbeac6173694595`.
- All 14 cloud-manifest files passed local checksum verification, and the local
  schema-6 validator reproduced the cloud result.
- Evidence:
  [`evidence/gate-3-3-two-strata/README.md`](evidence/gate-3-3-two-strata/README.md).
- Major-stage decision: stop before the remaining two strata. Move to
  reproducibility, English technical report, and complete 3–5 minute video.

## 2026-07-27 — P0 evaluator reproduction path implemented

- Audited the repository's evaluator setup before changing it.
- Found a blocking Docker reproducibility defect: `docker/Dockerfile` copied
  `uv.lock`, but no lock file existed in the repository.
- Generated `uv.lock` with `uv 0.11.28`; `uv lock --check` resolved 132
  packages successfully.
- Added:
  - root English `REPRODUCIBILITY.md`;
  - `docs/ENVIRONMENT.md`;
  - portable JSON environment capture;
  - GPU-required and explicit non-GPU evaluator preflight;
  - bounded three-candidate Radeon/Genesis smoke;
  - candidate-report validator;
  - deterministic recursive SHA-256 manifest writer.
- Updated the Docker path to use GuardianSim naming, copy the complete
  evaluator source plus bundled assets, install the package, and run tests at
  image build time.
- Identified and fixed a ROCm-environment drift risk: post-install `uv run`
  could re-synchronize the default locked PyTorch over the exact Radeon wheel.
  All GPU/evaluator run commands now use `--frozen --no-sync`.
- Updated the root README, Radeon Cloud runbook, and submission readiness
  matrix to route new evaluators through the concise commands.
- Local acceptance:
  - shell syntax passed;
  - Python compilation passed;
  - tests passed `54/54`;
  - `./scripts/evaluator_preflight.sh --no-gpu` passed;
  - strict Gate 3.2 schema-5 validation passed 30/30;
  - generated local preflight checksums verified;
  - all eight preserved Gate 3.2 checksum entries verified.
- Repeated the acceptance path after committing from a new `git clone
  --no-local` directory:
  - `uv sync --frozen --python 3.12` created the environment from the lock;
  - 80 dependency packages plus GuardianSim installed;
  - source metadata reported `git_dirty: false`;
  - tests passed 54/54;
  - strict formal validation and generated checksum verification passed.
- The Mac environment correctly recorded no ROCm GPU. Docker Desktop's CLI was
  installed but its daemon was not running, and macOS cannot provide
  `/dev/kfd`; full Docker/GPU validation is intentionally still pending on
  Radeon Linux.
- No cloud instance was stopped, destroyed, or modified, and no new benchmark
  was launched during this batch.

## 2026-07-27 — Radeon evaluator acceptance and submission V1

- Reused the retained Radeon Cloud Blank OpenCode instance
  `u-13907-735d71cb`; did not stop or destroy it.
- Fetched and checked out exact source commit
  `58a76d407a255f11d57bc401dcecb2604eafaca8` in a clean detached cloud
  checkout.
- Diagnosed the template-specific environment:
  - ROCm PyTorch and uv live in `/opt/venv`;
  - `VIRTUAL_ENV` was unset;
  - an unqualified `uv run --no-sync` created an empty local `.venv` and
    correctly reported missing PyTorch.
- Ran the GPU-required evaluator preflight with
  `UV_PROJECT_ENVIRONMENT=/opt/venv`:
  - Python 3.12.3;
  - PyTorch `2.9.1+gitff65f5b`;
  - HIP `7.2.53211-e1a6bc5663`;
  - one visible AMD Radeon GPU;
  - 54/54 tests from the deployed commit;
  - strict Gate 3.2 validation and checksum checks passed.
- Ran the bounded real Genesis counterfactual smoke:
  - Genesis selected `gs.amdgpu` and reported approximately 47.98 GB device
    memory;
  - the scene built and rendered successfully;
  - one snapshot fed three yaw candidates;
  - candidate validation returned `validated: true`;
  - snapshot fingerprint was
    `8a3692e8f016af7602ecb54e6f4db1cde765ce232138c9e72f8939ca2c8e2ee2`;
  - all 15 files passed `SHA256SUMS`.
- Prepared cloud archive
  `outputs/evaluator-smoke-58a76d4/evaluator-smoke-58a76d4.tar.gz`
  (approximately 253 KB). Automated browser download was blocked by an
  explicit security policy, so the archive awaits normal manual download from
  the Jupyter file browser before local evidence preservation.
- Added automatic Blank OpenCode `/opt/venv` detection to both evaluator shell
  entry points, documentation, and a regression test.
- Drafted the official-section-aligned English technical report and a
  4:00–4:30 demo script. The script requires path overlays, a contact
  freeze-frame, explicit left/right color semantics, millimeter clearance, and
  a top-down inset so the prior visually ambiguous comparison is not reused.
- Re-checked the official contest repository on 2026-07-27. It still requires
  an English Track 3 technical report, dedicated source repository,
  reproducibility README, and 3–5 minute complete-workflow demo; a complete
  Docker image is preferable. Luma's complete legal/rules text remains a
  mandatory manual owner review.
- Added a deterministic ReportLab builder and generated
  `output/pdf/GuardianSim-Technical-Report-DRAFT.pdf`.
- Rendered the PDF to PNG after each meaningful layout revision. The accepted
  review draft is six A4 pages with a cover, architecture figure, formal result
  table, limitations, references, page numbers, and an explicit draft/team
  attribution notice. All six pages passed visual inspection without clipping,
  overlap, unreadable headers, or broken list wrapping.
- Final local checks passed:
  - shell syntax for both evaluator entry points;
  - `uv lock --check` with 132 packages;
  - 55/55 unit tests;
  - PDF generation, extraction, required-metric, and placeholder checks;
  - Python compilation, `git diff --check`, and targeted secret/personal-email
    scan.

## 2026-07-27 — Evaluator smoke archive downloaded and verified

- The owner downloaded `evaluator-smoke-58a76d4.tar.gz` through the normal
  Jupyter file-browser action.
- The local archive was 253 KB and matched SHA-256
  `6457a20c7a1740eba2df5e62334a3f0c0bce55c4de4fface2675c9cd9861249c`.
- Audited the tar path list before extraction; no absolute or parent-traversal
  paths were present.
- Extracted to an isolated temporary directory and verified every file against
  the root `SHA256SUMS`; all 16 entries passed.
- Rechecked the raw evidence:
  - exact clean source commit
    `58a76d407a255f11d57bc401dcecb2604eafaca8`;
  - Ubuntu 24.04.4, Python 3.12.3, one gfx1100 Radeon GPU;
  - PyTorch `2.9.1+gitff65f5b`, HIP `7.2.53211-e1a6bc5663`, Genesis 1.2.3;
  - `gpu_ready: true`;
  - scene probe `passed`;
  - strict Gate 3.2 validation covered 30 episodes;
  - three candidates shared snapshot fingerprint
    `8a3692e8f016af7602ecb54e6f4db1cde765ce232138c9e72f8939ca2c8e2ee2`;
  - candidate validation returned `true`.
- Preserved the original archive, outer checksum, expanded raw JSON/log/image
  evidence, and claim-boundary README under
  `docs/evidence/evaluator-smoke-58a76d4`.

## 2026-07-27 — Aegis Motion identity and official-submission scan

- Recorded the owner's selected solo-team name: **Aegis Motion**.
- Updated the report, video close, submission plan, and PDF builder to use
  `Aegis Motion` and the verified public contributor identity
  `@nvm-star-max`; no legal identity was invented.
- Queried all 37 pull requests in the official contest repository. At the
  inspection time, 29 were open and 8 were closed. Four declared Track 3:
  NaviSense AI, 1bit.systems real-time NPU inference, G1D-Organize-Table, and
  the withdrawn-as-premature VisionPilot PR.
- Added a dated competitor scan with direct official PR links, visible
  strengths, limitations, and the resulting GuardianSim award strategy.
- Fixed the public category: GuardianSim is a policy-agnostic
  counterfactual-safety assurance layer, not another VLA, robot policy, or
  inference engine.
- Kept the verified `264.95 s/scenario` Gate 3.2 planning time as an explicit
  limitation. The next P0 is a visually unambiguous accepted formal replay and
  final 3–5 minute video, not a larger benchmark.
- Drafted the English official-repository PR title and body. It remains
  intentionally unopened until immutable release URLs, final video, final
  report, and manual Luma rules sign-off exist.
- Rebuilt the six-page A4 review PDF with Aegis Motion metadata and rendered
  every page for visual inspection. Identity, tables, wrapping, clipping,
  required metrics, claim boundaries, and page numbering passed. The cover
  now lists only the real remaining draft blockers: Luma sign-off and the
  final video.
- Local acceptance passed `uv lock --check`, 55/55 standard-library unit
  tests, PDF text/metadata assertions, Python compilation, whitespace checks,
  and a targeted credential/personal-email scan.

## 2026-07-27 — Strict Gate 3.2 replay validation and Aegis Motion hero clip

- Audited the preserved Seed 411 visual replay before consuming new GPU time.
- Added a pure claim-boundary validator and standalone CLI that require:
  - complete Gate 3.2 schema-5 validation;
  - the frozen protocol SHA-256;
  - exact scenario and formal candidate identities;
  - three formal baseline contacts and three formal GuardianSim safe
    executions;
  - replayed contact-to-safe classifications;
  - measured primary-obstacle overlap and at least 10 mm safe clearance;
  - source and presentation SHA-256 identity plus decodable video metadata.
- Strict validation accepted the existing source:
  - scenario `014_lemon-lateral_clutter-r01-s411`;
  - baseline candidate `yaw_+00.0_offset_+0.000`;
  - Guardian candidate
    `yaw_+67.5_retreat_+0.000_approach_+0.140`;
  - baseline overlap `1.419 mm`;
  - Guardian clearance `17.094 mm`;
  - formal baseline `0/3` safe and GuardianSim `3/3` safe.
- Generated the 1920×1080, 20 FPS, 17.55-second
  `gate-3-2-seed-411-aegis-showcase-v3.mp4`.
- Visually inspected six representative frames: branded title, plan-view
  action geometry, initial state, contact pause, retained lift, and final
  formal result card. Text, contrast, circles/arrows, numeric values, and
  claim boundaries were legible without clipping.
- Strictly revalidated the generated MP4 and sidecar. Showcase SHA-256:
  `38e9adfb2a3f2d90719b60449d092e4caca53afaa2b2f71fe1ade136357dff86`.
- No formal report, protocol, threshold, cloud instance, or GPU process was
  changed. No new statistical trial was added.
- Local tests passed `58/58`.

## 2026-07-27 — Narrated 4:15 Aegis Motion submission-video review cut

- Audited the four-minute production script and available immutable evidence
  before generating any new visual.
- Added `scripts/build_submission_video.py`, which:
  - asserts the expected Gate 3.2, Gate 3.3, evaluator-smoke, and hero-replay
    identities before rendering;
  - synthesizes eight English narration chapters locally with the macOS
    Samantha voice;
  - renders 1920×1080 presentation frames at 20 FPS;
  - embeds the accepted real Genesis Seed 411 replay;
  - renders the preserved Radeon environment and evaluator evidence as
    explicitly archived evidence, not a false live capture;
  - labels Gate 3.3 as separate engineering breadth evidence;
  - produces an H.264/AAC MP4, preview sheet, and machine-readable source
    sidecar.
- The first narration attempt used compressed AIFF that Python's standard
  reader could not parse. Changed the deterministic local narration format to
  PCM WAV; no evidence or visual claim changed.
- Generated the 4:15.4 review video with SHA-256
  `5abebe2ce3727a5404df70b814765b5d6978dea47b6b265816eb982ad6d0d262`.
- Added `scripts/validate_submission_video.py`. It strictly checked:
  - the 3–5 minute duration rule;
  - 1920×1080 dimensions and 20 FPS;
  - complete video and audio decode;
  - seven distributed frame decodes;
  - source-report, smoke, and hero-video hashes;
  - frozen formal metrics and separate engineering-evidence labeling;
  - the no-rerun and simulation-only claim boundary.
- Audio level inspection measured mean `-15.6 dB` and maximum `-1.2 dB`.
- The compressed-video closing QR code decoded successfully to
  `https://github.com/nvm-star-max/GuardianSim`.
- Inspected the contact sheet and full-resolution architecture, smoke,
  physical-replay, result, safe-stop, and closing frames.
- The first review found that bottom captions obscured the replay's exact
  overlap and clearance line. Moved captions to the upper information region
  for the hook and physical-proof chapters, rebuilt the video, and repeated
  strict validation.
- No cloud command, protocol, threshold, report, or statistical trial changed.
  Instance `u-13907-735d71cb` was not destroyed or modified.

## 2026-07-28 — Qwen narration and fixed-caption V2 review cut

- Reproduced the owner's two presentation issues:
  - the long subtitle sentence changed word-by-word/sentence-by-sentence and
    distracted from the evidence;
  - the local Samantha narration sounded mechanical.
- Compared current official Qwen TTS options and generated short `Ethan`,
  `Eldric Sage`, and `Serena` Qwen3-TTS Instruct samples. Selected `Ethan` as
  the default technical-demo voice while keeping the voice as a one-parameter
  replacement.
- Stored the provided Qwen credential only in the ignored `.env.local`, set
  file mode `600`, and verified `git check-ignore`. No secret was printed or
  added to tracked files.
- Added `scripts/qwen_tts.py` with:
  - official DashScope HTTP synthesis;
  - English instruction control and instruction optimization;
  - 520-character sentence-aware splitting;
  - content-addressed cache keys;
  - deterministic WAV concatenation and inter-chunk pauses;
  - safe environment/local-secret loading.
- Updated `scripts/build_submission_video.py`:
  - V2 output paths preserve V1;
  - fixed evidence captions change only once per chapter;
  - Qwen narration metadata and per-segment audio hashes are recorded;
  - local macOS TTS remains an explicit fallback;
  - EBU-style loudness normalization targets `-16 LUFS`, `-1.5 dB` true peak.
- Added three unit tests for narration splitting and WAV concatenation.
- Generated the final V2 owner-review artifact:
  - `281.5` seconds, inside the required 3–5 minute range;
  - 1920×1080, 20 FPS, H.264/AAC;
  - mean volume `-17.5 dB`, maximum `-1.2 dB`;
  - output SHA-256
    `e235a315cf4370ccd10cce5f50d317a7ec3376725940235482b530a641804888`.
- Extended the strict validator to support both V1 and V2 while requiring the
  exact V2 provider, model, voice, fixed-caption policy, and segment hashes.
- Strict validation passed full A/V decode, seven distributed frame samples,
  evidence hashes, formal metrics, duration, and claim boundaries.
- The closing QR code decoded successfully to
  `https://github.com/nvm-star-max/GuardianSim`.
- Local tests passed `61/61`.
- No Radeon Cloud action, Genesis execution, formal benchmark, threshold, or
  immutable report changed.

## 2026-07-28 — Owner approval and video freeze

- The owner reviewed the Qwen-narrated fixed-caption V2 and approved it with
  “就这个版本吧.”
- Froze
  `docs/submission/GuardianSim-Aegis-Motion-demo-review-v2.mp4` as the
  submission-video artifact:
  - SHA-256
    `e235a315cf4370ccd10cce5f50d317a7ec3376725940235482b530a641804888`;
  - 281.5 seconds, 1920×1080, 20 FPS;
  - Qwen3-TTS Instruct `Ethan`;
  - fixed per-chapter captions;
  - strict validation already passed.
- No media bytes, narration, captions, evidence, metrics, or cloud state
  changed in this approval step. Uploading to the organizer remains a separate
  external action.

## 2026-07-28 — Final report and organizer-package assembly

- Reconciled the project against the current official Track 3 submission
  contract: English report, dedicated source repository, detailed
  reproducibility instructions, preferred Docker packaging, a 3–5 minute
  complete-workflow video, and an English pull request from a fork of the
  official contest repository.
- Converted `scripts/build_technical_report_pdf.py` into a final/draft-aware
  builder and generated the final six-page English A4 PDF.
- Rendered all six pages to images and inspected the complete contact sheet
  plus the dense final page at full resolution. No clipping, overlap, missing
  glyph, draft marker, or unreadable footer was found.
- Final report SHA-256:
  `d4d5596645c4f971280f779eb585d0e675b62695d5f114db72dbbbf398054a66`.
- Tightened report wording so it does not imply a learned-policy statistical
  holdout or claim that strict report validation re-executes 30 physics
  episodes.
- Prepared
  `docs/submission/official-package/Track3-Aegis-Motion-GuardianSim` with an
  English submission README, the final PDF, and package checksums.
- Replaced placeholder links in `OFFICIAL_PR_DRAFT.md` with immutable source,
  video, evidence, Docker, and reproduction links.
- Verified both the source tree and frozen V2 video URLs at
  `25e27aced13237b5af93fd91697d7abb12101a30` return HTTP 200.
- Verified all package and top-level submission checksums.
- Re-ran local acceptance:
  - `ruff` passed for the report and video tooling;
  - the full suite passed `61/61`;
  - strict V2 validation reproduced the frozen video SHA-256 and decoded all
    required audio/video samples;
  - the PDF has six A4 pages, no draft marker, and all required Track 3 report
    sections in extracted text;
  - tracked-file secret-pattern scanning found zero hits.
- Confirmed `origin/main` can fast-forward to the feature branch. The official
  contest fork is still missing, so no public organizer pull request was
  opened.
- The Docker daemon was unavailable on this Mac; no unverified ROCm container
  result was added. The supported native Radeon Cloud route remains the
  reproduced path.

## 2026-07-28 — Governing rules retrieved and reconciled

- Opened the current Luma event and followed its official Rules and Conditions
  link to the governing Google document.
- Exported and read all 15 pages. Preserved only a source-linked summary and
  SHA-256 identity, not the external legal document itself.
- Confirmed the 2026-08-06 23:59 UTC+8 deadline, official-fork pull-request
  submission method, English-material rule, and Track 3 deliverables.
- Confirmed GuardianSim's single-Radeon/ROCm Genesis simulation path and
  mandatory artifacts comply with the technical requirements. A Docker image
  is preferred rather than mandatory; supplementary Track 3 material is
  optional.
- Confirmed that the legal name is required in private registration, not the
  public report. Kept public attribution as Aegis Motion / `@nvm-star-max`.
- Recorded owner-only eligibility and legal checks: legal-name/team-name
  registration consistency, valid Discord ID, age and exclusion provisions,
  broad AMD entry license, publicity/release terms, winner forms, withholding,
  and China CNY conversion.
- No organizer pull request was opened in this step because it is the final
  competition-entry action and carries the legal effects above.

## 2026-07-28 — Public release and official-fork branch prepared

- Fast-forwarded the GuardianSim default branch from its earlier baseline to
  the validated submission payload and pushed public `main`.
- Created annotated release tag `hackathon-2026-submission-v1` at payload
  commit `1059d0d5af402a20fe01ea190951d3abb27faef8`.
- Created `nvm-star-max/Radeon-hackathon-2026-07` as a fork of the official AMD
  contest repository.
- Added the self-contained package under the established
  `submissions/Track3-Aegis-Motion-GuardianSim` convention on branch
  `submission/track3-aegis-motion-guardiansim`.
- Verified the copied README and report against `SHA256SUMS`.
- Added a path-scoped binary attribute for the report PDF, changing the
  organizer comparison from an incorrect text diff to a 19,435-byte binary
  artifact.
- Pushed organizer-fork branch commit
  `abd0cfd72056eefe94298f513449e4f48842620b`.
- Confirmed no pull request exists for this head branch. The final organizer
  PR remains intentionally unsubmitted pending the owner's legal and personal
  eligibility confirmation.
