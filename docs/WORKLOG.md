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

## 2026-07-28 — Official hackathon entry submitted

- Received the owner's explicit confirmation of the registration,
  eligibility, entry-license, publicity/release, winner-form, and tax terms.
- Opened
  <https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/39>
  with the required title `Track 3, Aegis Motion, GuardianSim`.
- Verified:
  - state `OPEN`, non-draft, and `MERGEABLE`;
  - base `main`;
  - head `nvm-star-max:submission/track3-aegis-motion-guardiansim`;
  - head commit `abd0cfd72056eefe94298f513449e4f48842620b`;
  - exactly four intended files in the comparison;
  - all external source, video, evidence, and reproduction links returned
    HTTP 200;
  - no required status checks were reported at submission time.
- Added a durable non-private final submission record. No credentials, legal
  names, private contact details, or payment information were recorded.

## 2026-07-28 — P0 Parallel Futures interactive showcase

- Replaced the static evidence landing experience with **GuardianSim:
  Parallel Futures**, a judge-facing safety time machine.
- Added three evidence-bound challenges:
  - Seed 411 collision trap;
  - Seed 401 clearance decoy;
  - Seed 509 impossible-gap safe stop.
- Added interactive future selection, reveal animation, explicit
  accepted/rejected/safe-stop verdicts, downloadable JSON evidence receipts,
  immutable audit links, the preserved Seed 411 replay, and the frozen Gate
  3.2 aggregate proof panel.
- Generated a single project-bound social card for the new concept and added
  local preview/video assets. No experimental result or frozen report was
  modified.
- Programmatically cross-checked every displayed scenario value against the
  preserved schema-5 and schema-6 reports.
- Verified the showcase with rendered-HTML tests, lint, and a production
  build; the full repository regression passed `58/58`.
- Committed the exact validated source on
  `agent/parallel-futures-showcase` at
  `e566b69848a4ffc79168ac39087d6c86c9ac897b`.
- Preserved the `showcase/` subtree as Sites source commit
  `a8bf2af3b7a367c0e5b07960028b9ee58e9156f3`, saved version 3, and deployed it
  successfully to
  <https://guardiansim-proof.dghcdtddgh.chatgpt.site>.
- Kept the deployment owner-only; changing it to public requires a separate
  access-control decision.

## 2026-07-28 — Evidence-scale audit and Gate 4 local draft

- Paused merge/publication at the owner's request.
- Added a programmatic evidence-scale auditor that counts unique initial
  rollouts, non-duplicated confirmation rollouts, and final executions from
  the preserved schema-5 and schema-6 reports.
- Verified:
  - 42 scene units;
  - 1,185 counterfactual rollouts;
  - 202 final executions;
  - 1,387 total simulated action traces.
- Added local showcase copy and tests that present those counts with the
  explicit warning that nested traces are not independent scenes.
- Audited the public Track 3 PRs and recorded why training steps and inference
  throughput are not directly comparable with evaluation episodes.
- Implemented and tested the outcome-blind 240-scenario Gate 4 matrix,
  adaptive bounded candidate family, workload accounting, and exact McNemar
  helper.
- New targeted tests passed `8/8`. Ruff was not available in the current uv
  environment, so style verification remains pending before any commit.
- No branch push, site deployment, official PR edit, or Radeon run was made.

## 2026-07-29 — Radeon parallel-physics benchmark implemented locally

- Audited the Genesis scene integration:
  - `build_scene(n_envs=...)` uses Genesis batched environments;
  - formal GuardianSim benchmark runners remain single-environment;
  - several grasp helpers flatten or select the first batch element.
- Defined an honest presentation split between safety effectiveness and GPU
  physics throughput.
- Added:
  - `guardian_sim/radeon_scale.py`;
  - isolated trial and suite runners;
  - a strict report validator;
  - ROCm utilization/VRAM sampling;
  - protocol documentation and synthetic validator tests.
- Default cloud matrix: `1 / 16 / 64 / 256` worlds, `100` warmup steps and
  `1,000` timed steps per process, totaling `337,000` timed environment steps.
- Added a local-only 256-world scale-wall section to the showcase. It contains
  no fabricated performance result and remains marked pending.
- No cloud run, commit, push, deployment, or official submission edit was made
  in this stage.

## 2026-07-29 — Safety Critic and 54-way parallel futures implemented locally

- Converted the preserved Gate 3.2/Gate 3.3 rollout evidence into a
  scene-held-out surrogate dataset without double-counting repeated initial
  observations.
- Verified dataset accounting:
  - 1,185 candidate rollouts;
  - 42 scene units;
  - 34 training scenes and 8 held-out test scenes;
  - 571 hard-safe positive rows.
- Added a pre-trained-at-submission Safety Critic workflow with held-out
  quality gates, ROCm inference batches through 4,096 candidates, latency and
  throughput measurements, and GPU telemetry.
- Kept the learned model explicitly subordinate to the deterministic physics
  verifier.
- Added a 54-environment engineering runner for 18 candidates × 3 repeats,
  using batched IK, batched controls, vectorized clearance sampling, a frozen
  preflight protocol, and strict AMD/HIP report validation.
- Added portable tests for assignment coverage, pose expansion, report
  arithmetic, hard-safety label derivation, and tamper rejection.
- Full local regression passed `82/82`; targeted Ruff and `git diff --check`
  passed.
- The current connected Chrome session does not expose the Radeon Cloud
  Jupyter tab, so no cloud result was fabricated or inserted into the
  showcase. The next action is a real cloud run after that existing instance
  is opened manually.
- No commit, push, site deployment, official PR edit, frozen benchmark change,
  or instance destruction occurred.

## 2026-07-29 — Radeon P0 scale, 54-future run, and evidence preservation

- Relaunched the Radeon Cloud Blank OpenCode workspace and restored
  GuardianSim under `/workspace/persistent/GuardianSim`.
- Verified ROCm/HIP PyTorch, one AMD Radeon GPU, Python, Git, and `uv`.
- Preserved the initial failed scale logs from the missing-Genesis environment,
  installed the project into `/opt/venv`, and reverified PyTorch/HIP identity.
- Passed cloud targeted tests `16/16`.
- Completed and strictly validated the frozen `1 / 16 / 64 / 256` parallel
  physics matrix:
  - `154.1 / 2,383.7 / 9,354.3 / 35,166.1 env-steps/s`;
  - maximum measured speedup `228.16×`;
  - 256-world parallel efficiency `89.1%`;
  - 256-world mean/peak GPU use `85.5% / 96%`;
  - `337,000` timed environment steps.
- Completed and strictly validated the 54-way Parallel Futures engineering run:
  - `12.839 s`, `4.206 futures/s`;
  - `32` hard-safe, `22` rejected;
  - mean/peak GPU use `71.8% / 95%`.
- Ran the fixed Safety Critic experiment once. The report is structurally valid
  but `showcase_ready=false`: F1 `0.789` and unsafe precision `0.791` missed
  their predeclared `0.80` and `0.90` gates. No threshold was changed and the
  model is excluded from the judge-facing claim.
- Downloaded the evidence archive directly from the Jupyter file endpoint.
  Cloud and local SHA-256 matched:
  `35c1110711c96a7271fe723ffd2dd8160e179e63cd46864df4e5198f518fa46d`.
- Preserved reports, preflight, telemetry, raw logs, validators, chart,
  checkpoint, diagnostic failures, and checksums under
  `docs/evidence/radeon-p0-2026-07-29`.
- Updated the local showcase with strictly validated metrics only.
- Final local regression passed `82/82`; `npm test` rebuilt the showcase and
  passed all `3/3` rendered-HTML checks; `git diff --check` passed.
- No commit, push, deployment, official PR edit, or instance destruction.

## 2026-07-29 — Scale-first page and 80-second visual review cut

- Promoted the measured Radeon compute result to the first judge-facing
  screen: `256 robot worlds. One safe move.`
- Added the complete measured progression
  `154 / 2,384 / 9,354 / 35,166 env-steps/s` for
  `1 / 16 / 64 / 256` worlds and retained the `228.16×`, `89.1%`, GPU
  telemetry, and statistical-boundary labels.
- Added an animated 54-world Parallel Futures funnel with the strictly
  validated `32` hard-safe and `22` rejected result.
- Ran the showcase production build and rendered-HTML tests: `3/3` passed.
- Inspected the desktop full page, hero, Radeon section, and 390-pixel mobile
  layout using Playwright. Browser console: zero errors and zero warnings.
- Built
  `docs/submission/GuardianSim-Radeon-Parallel-Futures-review-v1.mp4`:
  - 80.0 seconds;
  - 1920×1080 at 20 FPS;
  - silent visual review;
  - preserved Seed 411 replay embedded without physics re-execution.
- Strictly validated output decode, source hashes, report-bound metrics, and
  claim boundaries. Output SHA-256:
  `76948ac89f3026cf6d0b845d6d009ab63cff27975b62ba952858355b4cb5073f`.
- Kept the existing approved Qwen V2 video unchanged. Natural Qwen narration
  for the new scale-first edit remains gated on owner visual approval.
- No commit, push, deployment, official PR edit, frozen-report mutation, cloud
  run, or instance destruction.

## 2026-07-29 — 80-second Qwen narrated review candidate

- Kept the validated silent cut unchanged and generated a separate narrated
  artifact from it.
- Used Qwen3-TTS Instruct
  `qwen3-tts-instruct-flash-2026-01-26` with the `Ethan` voice and a
  conversational robotics-engineer instruction.
- Added six fixed chapter captions plus an original low-volume ambient bed and
  transition chimes.
- Built and strictly validated
  `docs/submission/GuardianSim-Radeon-Parallel-Futures-narrated-v2.mp4`:
  - 80.0 seconds, 1920×1080, 20 FPS;
  - full audio/video decode passed;
  - visual-source, narration-segment, caption, and evidence hashes passed;
  - verified metrics and claim boundaries remained locked;
  - SHA-256
    `b07d0c71e7aceea5f2ebe82cd87d94ea223a99c090c5a6e1f6e06ce06559a2c9`.
- Inspected representative frames from all evidence-heavy chapters. Captions
  were readable and did not obscure the central scale, filtering, replay, or
  proof comparisons.
- Measured final audio at approximately `-18.2 dB` mean and `-1.3 dB` peak.
- Final local regression passed `82/82`; the showcase production build and
  rendered-HTML tests passed `3/3`; Python compilation and `git diff --check`
  passed.
- Kept this artifact local for owner listening and visual approval; no commit,
  push, deployment, official PR edit, cloud execution, or instance
  destruction occurred.

## 2026-07-29 — Fixed card overflow and removed template-like copy

- Reproduced the fourth-card overflow on the frozen-result screen.
- Added measured-width font selection for all card titles, values, and detail
  lines instead of relying on fixed font sizes.
- Rewrote the 80-second visual and narration copy as a direct account of the
  experiment. Removed the “formal proof” wording and several slogan-like
  transitions without changing any evidence-backed metric.
- Added a durable human-writing rule to `docs/PROJECT_MEMORY.md` for future
  reports, site text, PR copy, and narration.
- Preserved the old V1/V2 artifacts and generated new versions:
  - silent visual source V2 SHA-256
    `5033b75ed91fd8883e70fd6ec7f4ce52c8a2ee8092822d8c89404b7894cb6edb`;
  - narrated V3 SHA-256
    `70c1bf9734b29c7e698dacc3a09e9a0602757c3be93a6917fbd17372530bb9c8`.
- Strict silent and narrated validators passed. V3 full A/V decode passed;
  audio measured approximately `-18.2 dB` mean and `-1.2 dB` peak.
- Inspected the opening, Parallel Futures, frozen-result, and closing frames;
  all text remained within its intended container.
- Final local regression passed `82/82`; the showcase production build and
  rendered-HTML tests passed `3/3`; Python compilation and `git diff --check`
  passed.
- No commit, push, deployment, official PR edit, cloud execution, or instance
  destruction occurred.

## 2026-07-29 — Replaced fixed anchors with optical centering

- Confirmed that V3 solved overflow but left the short `30 → 0` row visually
  spread across fixed anchor positions.
- Implemented measured whole-row centering with dynamic font fitting and
  a render-time symmetry assertion of at most one pixel.
- Centered each card title and detail line from its measured pixel width.
- Extracted and inspected the final encoded V4 proof frame.
- Built and validated:
  - `GuardianSim-Radeon-Parallel-Futures-review-v3.mp4`,
    SHA-256
    `4e2c6eddc1bb127818dcf0368c83e4eb30f4b3dcdfe754d8933d3ed36799c85d`;
  - `GuardianSim-Radeon-Parallel-Futures-narrated-v4.mp4`,
    SHA-256
    `2be66996eb0e3bb460148c5afc8060f69680f1d7e314e2e46cf2d363d53a923a`.
- Final local regression passed `82/82`; the showcase production build and
  rendered-HTML tests passed `3/3`; Python compilation and `git diff --check`
  passed.
- No commit, push, deployment, official PR edit, cloud execution, or instance
  destruction occurred.

## 2026-07-29 — Integrated the Radeon P0 evidence into the local submission package

- Verified the current organizer README: Track 3 asks for a technical report,
  reproducibility README, source repository, and a recommended 3-5 minute
  complete-workflow video; supplementary material is allowed.
- Kept the approved 4:41 V2 as the workflow video and accepted the 80-second
  optically centered V4 as a supplementary Radeon preview.
- Added measured 1/16/64/256-world throughput and the 54-world Parallel Futures
  run to:
  - `docs/submission/TECHNICAL_REPORT.md`;
  - the local official-package README;
  - `docs/submission/OFFICIAL_PR_DRAFT.md`.
- Kept Gate 3.2 safety metrics unchanged and explicitly separated environment
  steps/candidate futures from independent safety scenarios.
- Copied the V4 preview and the two raw reports plus validator outputs into
  `docs/submission/official-package/Track3-Aegis-Motion-GuardianSim`.
- Rebuilt `GuardianSim-Technical-Report.pdf` with ReportLab. The final report
  is seven pages and has SHA-256
  `6a735fe0a77c0c6ec3e9461051bac29ce371a3ca04d74246f0d39d6a64a3291c`.
- Rendered all seven PDF pages to PNG and inspected every page. No visual
  defect was found.
- Rebuilt and verified the recursive package checksum manifest.
- Package-manifest SHA-256:
  `392e624b5839e4af0799d59d321ae27d31b12a34cb225fe20d342bd4ceef0d94`.
- Passed `82/82` Python tests, `3/3` showcase HTML tests, production build,
  ESLint, both strict Radeon report validators, and the V4 full A/V validator.
- Stopped before the public release boundary. The next release must publish
  the P0 source/evidence and then update the immutable links in organizer PR
  #39; no push or PR edit was performed.

## 2026-07-29 — Published Radeon P0 release and updated organizer PR #39

- Confirmed GitHub CLI authentication and scanned the staged release for
  Qwen/OpenAI/GitHub credential patterns; no secret was staged.
- Excluded local video intermediates and Playwright screenshots from the
  public commit.
- Fixed the final Ruff findings: import ordering, unused render variables, and
  executable modes for shebang scripts.
- Re-ran all release checks successfully:
  - Python unit tests `82/82`;
  - Ruff;
  - strict scale and Parallel Futures validators;
  - silent V3 and narrated V4 full decode/claim validators;
  - both checksum manifests;
  - showcase production build, rendered-HTML tests `3/3`, and ESLint;
  - staged diff whitespace check.
- Published GuardianSim commit
  `830e4fc8e2467bc4a0eacbb9777b91351e20f924` and immutable tag
  `hackathon-2026-submission-v2`.
- Synced the official package to the contest fork and pushed commit
  `d73bad667db22d67d737ec50ceb8ff761b0c3816`.
- Updated PR #39's English body with measured scale, 54-world candidate
  screening, statistical boundaries, v2 release links, and limitations.
- Verified PR #39 is open, non-draft, cleanly mergeable, and points to the
  expected fork commit.
- Downloaded remote package artifacts and validated their recursive checksums.
- Did not merge the organizer PR and did not access or destroy the Radeon
  instance.

## 2026-07-29 — Published a no-sign-in judge showcase

- Audited organizer PR #39 after the P0 release. It had no comments, reviews,
  or checks requiring action and remained open and cleanly mergeable.
- Found that the repository's interactive-showcase URL returned HTTP 401 and
  required ChatGPT sign-in.
- After owner authorization, attempted to make the Sites deployment public.
  The workspace did not permit internet-public Sites access, so the existing
  deployment was left unchanged.
- Added an isolated Vite static build for the same React showcase without
  changing the evidence-backed interaction or metrics.
- Passed:
  - existing server-rendered showcase tests `3/3`;
  - static GitHub Pages tests `2/2`;
  - ESLint;
  - both submission checksum manifests;
  - `git diff --check`.
- Published the public page at
  <https://nvm-star-max.github.io/GuardianSim/>.
- Verified unauthenticated HTTP 200 responses for its HTML, JavaScript, CSS,
  replay video, and social-preview image.
- Added the public quick-start URL to the repository README, official package,
  and organizer PR body.
- Pushed official fork commit
  `289e4c09211974f12f74b8298e493ab93e78037f`; PR #39 remained open,
  non-draft, and `CLEAN`.
- Did not merge the organizer PR and did not access or destroy the Radeon
  instance.

## 2026-07-29 — Fixed arena evidence visibility and audited adjacent projects

- Replaced pre-evaluation clearance/stability dashes with the preserved
  measurements already bound to each Future card.
- Kept safety verdicts behind the interaction boundary and clarified the
  button/status copy so users understand that the next action applies frozen
  gates rather than generating missing measurements.
- Passed:
  - Python unit tests `82/82`;
  - showcase production build and rendered-HTML tests `3/3`;
  - static GitHub Pages build and tests `3/3`;
  - ESLint;
  - submission working-set checksum verification;
  - `git diff --check`.
- Used a headed browser against the static build to verify:
  - initial measurement visibility for Futures A/B/C;
  - Future C selection;
  - final collision/rejection/selection verdicts and decision receipt;
  - desktop layout without card overflow.
- Reviewed Genesis, cuRobo, ManiSkill, Isaac Lab, MoveIt 2, and
  Safety-Gymnasium from their official repositories/documentation.
- Recorded functional overlap, platform distinctions, AMD/ROCm status, and
  conservative claim language in
  `docs/submission/OPEN_SOURCE_OVERLAP_AUDIT_2026-07-29.md`.
- Pushed source commit
  `ea775906a4e40d38b976b21e3e1b97e27312173b`.
- Deployed GitHub Pages commit
  `ec824eeaa8a5d9959f7d0135c14f0ac609ab6aa8`; the Pages API reported
  `built`.
- Verified public HTTP 200 responses for HTML, compiled JavaScript,
  stylesheet, and Seed 411 replay. The deployed bundle contained the visible
  measurement copy, gate-action copy, `−1.42 mm`, and `0.936`.
- Did not move the immutable contest tag, edit or merge organizer PR #39, or
  publish local video/Playwright intermediates.
- Did not access or destroy the Radeon Cloud instance.

## 2026-07-29 — Closed the maintenance-backup gap and froze the next P0 direction

- Reused the existing Jupyter session for Radeon instance
  `u-13907-735d71cb`; did not restart or destroy it.
- Confirmed that the instance mount is `/workspace/persistent`, despite the
  organizer announcement using `/workspace/persistence`.
- Downloaded the raw Radeon P0 archive and checksum, verified archive contents,
  and matched SHA-256
  `35c1110711c96a7271fe723ffd2dd8160e179e63cd46864df4e5198f518fa46d`.
- Copied the archive and checksum into the actual NFS persistence mount and
  preserved a local Mac copy under
  `/Users/aolos/Downloads/GuardianSim-backups/2026-07-29/`.
- Added `guardian_sim.backup` and
  `scripts/backup_radeon_workspace.py`:
  - Git bundle for committed history and refs;
  - working-tree tarball for tracked and untracked files;
  - optional raw external artifacts;
  - recursive checksum manifest and restore metadata;
  - secret/cache exclusion policy.
- Added two unit tests covering restore artifacts, recursive checksums, raw
  artifact inclusion, secret exclusion, cache exclusion, and invalid source
  rejection.
- Read the current Track 3 PRs for NaviSense AI and 1bit.systems, then compared
  their delivery mechanisms with cuRobo, ManiSkill, Isaac Lab,
  Safety-Gymnasium, and Genesis.
- Defined **Radeon Safety Swarm** as the next P0 implementation gate:
  a frozen 256-world uncertainty stress test, 16×16 robustness wall, typed
  costs, visible AMD telemetry, execute-or-stop decision, and evidence receipt.
- Kept the failed Safety Critic out of the headline; it remains preserved
  negative evidence/P3 research.
- Passed `84/84` Python unit tests, Python compilation, and
  `git diff --check`.
- Committed and pushed the isolated backup/tooling scope as
  `b97fd7e9a08a9c0fc7fdf2c9232dac76fb998afd`; no video drafts, Playwright
  scratch data, immutable-tag movement, or organizer-PR edits were included.
- Executed the backup in the current Radeon Jupyter session. Result:
  `/persistent/GuardianSim-backups/20260729T035224Z-1481f51cd706`.
- Verified every `SHA256SUMS` payload, the Git bundle, and all 580 tar members.
  The manifest covers the Git bundle, working-tree archive, metadata,
  restore README, Git status, and both external raw P0 artifacts.
- The cloud working tree remains on `main@1481f51cd706`; no branch switch,
  restart, or instance destruction occurred.

## 2026-07-29 — Built the frozen Safety Swarm protocol and offline future wall

- Added `guardian_sim/safety_swarm.py` with:
  - the complete 256-world matrix;
  - typed cost vectors;
  - hard-safe classification and ordered stop reasons;
  - Wilson and percentile aggregation;
  - schema-1 report assembly and strict validation;
  - a deterministic UI-only fixture.
- Added CLI tools to build the fixture, validate any Safety Swarm report, and
  render the report as a standalone interactive HTML page.
- Added five unit tests covering:
  - matrix uniqueness, order, balance, and hash;
  - typed costs and multi-gate failure explanations;
  - formal AMD/HIP/ROCm report acceptance;
  - matrix, label, summary, and hash tamper rejection;
  - explicit separation between an offline fixture and Radeon evidence.
- Generated the fixture report and strict validation under the ignored
  `outputs/safety-swarm/` workspace.
- Opened the HTML in Chromium, inspected the accessibility snapshot containing
  all 256 cells, and captured a complete 1920×1450 review frame at
  `output/playwright/safety-swarm-offline-fixture.png`.
- Verified the full grid, decision card, metrics, hashes, legend, and claim
  boundary fit their containers. Cell-level hover data contains the exact
  physical perturbation, clearance, stability, and stop reason.
- The fixture result (`128/256`, `safe_stop`) is synthetic UI calibration and
  is not eligible for any submission metric or AMD performance statement.
- Stopped before the Genesis/Radeon execution gate. No cloud run, public-site
  change, push, organizer-PR edit, or instance destruction occurred.

## 2026-07-29 — Added the isolated Safety Swarm Genesis smoke executor

- Added a simulator-independent placement/timing adapter for per-environment:
  - target XY/yaw perturbation;
  - clutter gap/bearing perturbation;
  - end-effector XY bias;
  - action-start delay.
- Added fixed balanced 4-world and 16-world subsets that reference, but never
  mutate, the frozen 256-world matrix.
- Added a Radeon-only engineering-smoke schema with:
  - strict world reconstruction;
  - AMD/HIP/ROCm requirements;
  - recomputed labels, summaries, and report hash;
  - `showcase_ready=false`;
  - explicit prohibition on merging partial smoke evidence into the formal
    population.
- Added a Genesis GPU batched smoke runner with no-overwrite evidence paths,
  preflight protocol preservation, per-world IK targets, delayed control,
  sampled clearance/contact capture, retained-lift stability, and ROCm
  telemetry.
- Extended the validator CLI to auto-detect formal versus smoke reports.
- Local acceptance passed `92/92` Python tests, Python compilation, unchanged
  formal matrix/protocol hashes, and `git diff --check`.
- No Radeon workload has been run yet in this checkpoint.

## 2026-07-29 — Ran the Safety Swarm 4/16-world Radeon smoke gate

- Reused instance `u-13907-735d71cb` and kept the original cloud repository
  untouched. Created
  `/workspace/persistent/GuardianSim-safety-swarm` as a clean detached
  worktree for the smoke execution.
- Preserved a valid but failed first 4-world report after discovering that the
  runner had selected the retreat-`25 mm` candidate instead of the centered
  Gate 3.2 candidate. The failure was diagnosed from task completion and
  retained-lift measurements; no safety threshold was changed.
- Bound the runner to the verified centered candidate and reran the same
  predeclared four rows. Strict validation passed with `4/4` safe, zero
  contacts, `16.372 mm` worst clearance, `0.925` minimum stability,
  `239.806` environment steps/s, and `89%` peak AMD GPU use.
- Opened the predeclared 16-world gate. Strict report validation passed, but
  the acceptance result was `12/16`:
  - world `69` missed only the frozen clearance threshold at `9.680 mm`;
  - worlds `91`, `109`, and `209` contacted clutter and failed the task;
  - batch throughput was `747.843` environment steps/s with `94%` peak AMD
    GPU use.
- Stopped before the formal 256-world batch, as required by the frozen gate.
  Did not edit the matrix, threshold, row order, protocol hash, or any prior
  report.
- Collected the wrong-candidate 4-world run, corrected 4-world run, and
  balanced 16-world run with preflights, logs, PIDs, validation receipts,
  provenance, and recursive checksums under
  `docs/evidence/safety-swarm-smoke-2026-07-29` in cloud commit
  `599c04770aca17b32971ed417d678122dbe4c453`.
- Built cloud transfer package
  `/workspace/safety-swarm-smoke-evidence-2026-07-29.tar.gz`; verified package
  SHA-256 is
  `31a4c1c6923c793a501915260fa66eb5f8179dab8e728fc003d99b41687571c0`.
- Downloaded the package manually after automatic browser transfer was
  security-blocked. The local package hash matched, the 21-member archive had
  no unsafe paths or links, and all 16 inner `SHA256SUMS` payloads passed.
- Imported the raw evidence into
  `docs/evidence/safety-swarm-smoke-2026-07-29` and reran strict
  `--require-radeon` validation against all three reports. Each report's
  schema, protocol identity, full-matrix reference, measurements, derived
  labels, AMD/HIP/ROCm evidence, and report hash passed.

## 2026-07-29 — Froze and implemented Safety Swarm V2 locally

- Kept every Safety Swarm V1 protocol identity and evidence file unchanged.
  Added an independent V2 protocol for selecting one action only after
  evaluating the candidate across an uncertainty envelope.
- Froze the 18-action Gate 3.2 catalog and deterministic Cartesian execution
  order over the existing 256-world matrix:
  - 4,608 candidate-world pairs in the formal population;
  - candidate catalog SHA-256
    `9c3af60dfb812e6128f6e849d27cf2acd0d672cdcb3aa98191656e4009054e44`;
  - formal protocol SHA-256
    `7fedeeeea436f3b0fe04196e4ad5ec225ccfe7bf26ad60cd3af8a7a4f4da43ac`;
  - formal chunks contain at most 256 Genesis environments.
- Added frozen V2 cloud gates:
  - `triad-4`: 12 pairs,
    `4fad8ddaebbff6f2b328af83671465574a0482046a1361522ae8399c15fd574c`;
  - `full-4`: 72 pairs,
    `e6c24948ee708c20d6c6ea270ac4ff3fb5b503d18896508d7d66fa69536aa984`;
  - `full-16`: 288 pairs,
    `128a494aec03498c8ba6c807a3e26f8e733c87f61ec5e696371839270c3d9f44`;
  - formal: 4,608 pairs.
- Implemented strict all-world qualification, deterministic robust ranking,
  typed `safe_stop`, V2 report assembly and validation, AMD/HIP/ROCm checks,
  an offline fixture, and an adaptive candidate-by-world evidence renderer.
- Extended `scripts/run_safety_swarm_smoke.py` with `--v2-tier` while
  preserving the V1 interface. One tier is flattened into a single Genesis
  GPU scene with per-environment candidate and world assignment.
- Built and strictly validated the local 3×4 fixture. It selected the expected
  centered `+67.5°` candidate, but remains clearly labelled offline with
  `showcase_ready=false`; it is UI/execution-path calibration only.
- Local verification passed `98/98` unit tests, compilation, report
  validation, renderer inspection, and `git diff --check`.
- Stopped before the next major gate. No Radeon workload was launched and the
  cloud instance was not restarted or destroyed. Next action:
  `triad-4` on Radeon Cloud, followed by 72, 288, and 4,608 pairs only when
  each preceding frozen gate passes.

## 2026-07-30 — Passed and preserved Safety Swarm V2 Gate V2-A

- Reused Radeon Cloud instance `u-13907-735d71cb` without restarting or
  destroying it. Created a separate clean detached V2 worktree at
  `/workspace/persistent/GuardianSim-safety-swarm-v2` because the prior V1
  evidence commit was not an ancestor of V2 source commit
  `dd300f98320f39666f684c3aed1f3afa25884d20`.
- Executed the frozen `triad-4` tier as one Genesis GPU scene: 3 candidates ×
  4 worlds = 12 candidate-world pairs. Strict schema-1 validation passed.
- The deterministic result selected `yaw_+00.0_offset_+0.000`, the only
  candidate that passed 4/4 with zero contact. Its worst sampled clearance
  was `42.136 mm`, fifth-percentile clearance `42.985 mm`, and minimum
  stability `0.923`.
- Rejected the two `+67.5°` alternatives from execution:
  - centered approach: 2/4 safe and two clutter contacts;
  - `25 mm` retreat: 0/4 safe, one clutter contact, and three stability
    failures.
- Recorded 6 safe and 3 contact candidate-world pairs overall. This does not
  mean all 12 pairs passed; V2-A passed because one candidate survived every
  frozen world, exactly as predeclared.
- Measured `5,988` environment steps in `10.755 s`, or `556.783` steps/s.
  Radeon telemetry recorded `69%` mean and `94%` peak GPU utilization, about
  `1.049 GiB` maximum VRAM use, and no sampling errors.
- Preserved report, preflight, logs, process ID, before/after ROCm snapshots,
  validation receipts, source provenance, protocol, and recursive checksums
  under `docs/evidence/safety-swarm-v2-triad-4-2026-07-30`.
- Verified downloaded archive SHA-256
  `7280f59866980954ec52287fd4046069c487dfb23bca5f8c51d91c72568f877f`,
  rejected unsafe archive structures before extraction, passed all 13 inner
  checksums, and reran strict local `--require-radeon` validation.
- Left the offline fixture and all V1 evidence untouched. The fixture's
  different selected candidate is additional evidence that it was not used
  as a cloud result.
- No protocol or threshold changed. Stopped before Gate V2-B. The only next
  eligible scale step is the frozen 18×4 = 72-pair run; V2-C and the
  4,608-pair formal run remain closed.

## 2026-07-30 — Passed and preserved Safety Swarm V2 Gate V2-B

- Revalidated the clean Radeon worktree and V2-A evidence before launch, then
  reused instance `u-13907-735d71cb` without restart or destruction.
- Executed the frozen `full-4` tier from source commit
  `dd300f98320f39666f684c3aed1f3afa25884d20` as one Genesis AMD GPU scene:
  18 candidates × worlds `0, 85, 170, 255` = 72 candidate-world pairs.
- Strict schema-1 `--require-radeon` validation passed with the frozen
  `full-4` protocol SHA-256
  `e6c24948ee708c20d6c6ea270ac4ff3fb5b503d18896508d7d66fa69536aa984`
  and unchanged formal protocol SHA-256
  `7fedeeeea436f3b0fe04196e4ad5ec225ccfe7bf26ad60cd3af8a7a4f4da43ac`.
- The run produced eight qualifying candidates. Deterministic robust ranking
  selected `yaw_-22.5_retreat_+0.025_approach_+0.140`: 4/4 safe, zero
  contacts, `96.009 mm` worst-case sampled clearance, `96.857 mm`
  fifth-percentile clearance, and `0.847` minimum stability.
- Batch diagnostics were 41/72 safe candidate-world pairs and five sampled
  contact pairs. The result is an action-search result, not a claim that all
  alternatives were safe.
- Measured `35,928` environment steps in `15.098 s`, or `2,379.598` steps/s
  and `4.769` candidate-world pairs/s. Radeon telemetry recorded `76.378%`
  mean and `96%` peak utilization over 37 samples, about `1.162 GiB` maximum
  VRAM use, and no telemetry errors.
- Preserved the raw report, preflight, validation, launch command, logs,
  process ID, Git provenance, ROCm snapshots, protocol, acceptance receipt,
  and checksums. Corrected only an initially generated derivative summary
  that read nested protocol hashes from the wrong location; the original
  report and strict validation were never changed.
- Downloaded archive SHA-256
  `78e3df66673037cfde9ff04e19bd35ffd040c257b4468ac2268dd1e8c3a75359`
  matched the cloud receipt. Archive safety checks passed and all 17 inner
  checksums verified before import to
  `docs/evidence/safety-swarm-v2-full-4-2026-07-30`.
- No frozen protocol element changed. Gate V2-C is now eligible but was not
  launched. Gate V2-D and formal 4,608-pair claims remain closed.

## 2026-07-30 — Passed and preserved Safety Swarm V2 Gate V2-C

- Revalidated the frozen V2-B report and acceptance receipt, confirmed the
  cloud worktree remained clean at
  `dd300f98320f39666f684c3aed1f3afa25884d20`, and verified the V2-C output
  and archive paths were absent before launch.
- Reused instance `u-13907-735d71cb` without restart or destruction. Executed
  the frozen `full-16` tier as one Genesis AMD GPU scene: all 18 candidates ×
  16 predeclared worlds = 288 candidate-world pairs.
- Strict schema-1 `--require-radeon` validation passed with protocol SHA-256
  `128a494aec03498c8ba6c807a3e26f8e733c87f61ec5e696371839270c3d9f44`
  and unchanged formal protocol SHA-256
  `7fedeeeea436f3b0fe04196e4ad5ec225ccfe7bf26ad60cd3af8a7a4f4da43ac`.
- Five candidates qualified. Frozen robust ranking selected
  `yaw_-45.0_retreat_+0.000_approach_+0.140`: 16/16 safe, zero contacts,
  `66.339 mm` worst-case sampled clearance, `70.144 mm` fifth-percentile
  clearance, and `0.909` minimum stability.
- The four-world V2-B winner did not remain the winner under 16 worlds, and
  the qualifying set narrowed from eight to five. This supports the intended
  candidate-by-uncertainty selection story without changing policy after
  inspection.
- Batch diagnostics were 165/288 safe candidate-world pairs and 14 sampled
  contact pairs. Measured execution was `143,712` environment steps in
  `15.870 s`, or `9,055.573` steps/s and `18.147` candidate-world pairs/s.
  Radeon telemetry recorded `78.282%` mean and `96%` peak utilization over
  39 samples, about `1.414 GiB` maximum VRAM use, and no sampling errors.
- Preserved raw report, preflight, validation, launch command, logs, process
  ID, Git provenance, ROCm snapshots, protocol, acceptance receipt, and
  recursive checksums.
- Downloaded archive SHA-256
  `b5262da3769e41fb67838eb537b37357c99544902ee8d6fa9effb9890fe82fd5`
  matched the cloud receipt. Archive safety checks and all 17 inner checksums
  passed before import to
  `docs/evidence/safety-swarm-v2-full-16-2026-07-30`.
- No frozen protocol element changed. Gate V2-D is now eligible but was not
  launched. The 4,608-pair formal result and any formal robustness claim
  remain absent.

## 2026-07-30 — Implemented the resumable Gate V2-D formal path

- Confirmed that the frozen protocol declared Gate V2-D but the runner only
  implemented `triad-4`, `full-4`, and `full-16`; did not launch an
  unverifiable 4,608-pair run.
- Added exact formal chunk assignment, chunk report assembly, strict chunk
  validation, complete-report aggregation, and complete formal validation.
  The frozen candidate catalog, world matrix, gates, order, and formal
  protocol hash remain byte-for-byte unchanged.
- Extended the Genesis runner with `--v2-formal-chunk-index 0..17`. Each
  invocation runs one candidate across all 256 frozen worlds in a maximum
  256-environment AMD GPU batch.
- Added `scripts/run_safety_swarm_v2_formal.py`. It preserves numbered
  attempts, strictly validates completed chunks before resume, refuses
  ambiguous duplicate valid attempts, requires all 18 chunks in frozen order,
  and writes the final report and validation receipt without overwrite.
- Extended the report validator to identify smoke, formal-chunk, and complete
  formal reports. Added tests for exact chunk coverage, 4,608-pair
  reconstruction, deterministic selection, missing/reordered/mixed chunk
  rejection, label tampering, and telemetry aggregation.
- Verification: formal protocol hash remained
  `7fedeeeea436f3b0fe04196e4ad5ec225ccfe7bf26ad60cd3af8a7a4f4da43ac`;
  `101/101` unit tests passed; Python compilation, Ruff checks, and
  `git diff --check` passed.
- Stopped before cloud synchronization and launch. No Radeon formal result
  exists yet.

## 2026-07-30 — Passed and preserved Safety Swarm V2 Gate V2-D

- Pushed formal executor commit
  `4d0aaec1da077e333cbfdd9ee3f413d852c1cbec`, created a clean detached
  persistent worktree, revalidated the prior 288-pair V2-C report, and passed
  all nine targeted V2 tests on Radeon Cloud before launch.
- The cloud-wide 101-test suite had one unrelated Gate 4 draft hash failure
  caused by Python-micro-version random-float drift. The frozen V2 protocol
  hash and all V2 tests passed; no Gate 4 source or V2 threshold was changed.
- Launched the formal orchestrator once and completed chunks `00..17` in
  frozen candidate-major order. Every chunk completed in `attempt-001`;
  there were no partial retries, mixed commits, or overwritten reports.
- Strict complete-report validation reconstructed all 4,608 labels,
  candidate envelopes, qualification, ranking, source/device identity,
  timing, telemetry, and hashes. It passed with report SHA-256
  `a3e86baa03e84d75a81062fee5f9f22770a3753708c116168174ea291c7a93cf`.
- Five candidates passed all 256 worlds. The selector executed
  `yaw_-45.0_retreat_+0.000_approach_+0.140`: 256/256 safe, zero contacts,
  `66.249 mm` worst sampled clearance, `66.304 mm` fifth-percentile
  clearance, and `0.907` minimum stability.
- Population diagnostics were 2,614 safe pairs and 270 sampled contact pairs
  out of 4,608. Measured execution was 2,299,392 environment steps in
  226.676 s: 10,143.979 steps/s and 20.329 candidate-world pairs/s.
- AMD telemetry recorded 73.406% mean and 97% peak GPU utilization over 588
  samples, about 1.381 GiB maximum VRAM use, and no sampling errors.
- The first post-run validation command accidentally referenced
  `report.json`; formal output is `formal-report.json`. Preserved the empty
  failed receipt, reran against the correct path, and required a passing
  strict result before packaging.
- Downloaded archive SHA-256
  `0450857c2d50446ba76c1358bdf622c7e5cc4f43dbcc6dd48abb2e855b48e9ee`
  matched the cloud receipt. Safe extraction passed, all 90 inner checksums
  matched, and local `--require-radeon` validation passed.
- Imported 92 raw evidence files under
  `docs/evidence/safety-swarm-v2-formal-2026-07-30`. No prior V1/V2 evidence,
  frozen protocol identity, cloud instance, or unrelated local submission
  media was modified.

## 2026-07-30 — Built and calibrated the 4,608-pair judge showcase

- Replaced the website's small 54-future engineering vignette as the main
  scale story with the completed Safety Swarm V2 formal result:
  18 candidates × 256 uncertainty worlds = 4,608 measured pairs.
- Added a deterministic generator from the preserved formal JSON to a compact
  TypeScript dataset and a test that reconciles row lengths, safe/contact
  counts, qualification count, selected count, report hash, physics-step
  count, and GPU peak against the original report.
- Implemented the exact 18 × 256 result matrix, `4,608 → 5 → 1` funnel,
  selected-action receipt, rejection histogram, AMD execution card, and
  immutable evidence links.
- Updated the hero and metadata to lead with the formal workload while keeping
  the 256-world throughput benchmark explicitly separate. Kept the claim
  boundary visible next to the formal data.
- Browser-calibrated the site at 1440 × 1000 and 390 × 844. Corrected a mobile
  hero overlap; final measurements showed no page/card overflow and no browser
  console warnings or errors.
- Rejected two generated share-card drafts because they visually overstated
  the number of all-world qualifiers. Did not copy either image into the
  project and removed stale OG-image references.
- Verification passed:
  `npm --prefix showcase test`,
  `npm --prefix showcase run test:pages`, and
  `npm --prefix showcase run lint`.
- Preserved all unrelated untracked submission videos, previews, PDF output,
  and browser artifacts. The Radeon Cloud instance was not restarted,
  destroyed, or used during this website-only stage.

## 2026-07-30 — Published the calibrated showcase as Sites version 4

- Pushed exact source commit
  `f5b9ed061e9483027f367ebfd1d950ee76ed7312` to the existing Sites `main`
  branch.
- Packaged the `showcase` build from that commit and saved version `4`;
  archive content hash:
  `sha256:91c98971aa4498571b257676b098633ddf70b1d36d45cf50fe11d81ce1916eba`.
- Deployed the saved version to
  `https://guardiansim-proof.dghcdtddgh.chatgpt.site`; Sites deployment
  `appgdep_6a6b1cfe6b608191a0bd8509f0cccae2` completed with status
  `succeeded`.
- Kept the existing owner-only access configuration unchanged. Browser
  navigation reached the expected sign-in gate, so protected production DOM
  inspection was not substituted for the already completed exact-commit
  local QA.
- No Radeon instance, formal evidence, frozen protocol, thresholds, or
  unrelated untracked submission artifacts changed during deployment.

## 2026-07-30 — Prepared the V3 submission package and updated public Pages

- Rechecked the official Track 3 repository instructions and retained the
  required English report, source/reproducibility guide, and 3-5 minute
  complete-workflow video structure.
- Rewrote the submission front door so the 30-scenario safety benchmark and
  the 4,608 candidate-world decision workload use distinct denominators and
  claims.
- Rebuilt and rendered the technical report. The first V3 render exposed a
  one-reference orphan page; shortened the delivery section, rebuilt to seven
  pages, and visually verified the corrected final page.
- Copied the byte-identical final PDF into the working submission set and
  organizer package. Added compact Safety Swarm V2 summary/validation files
  and regenerated both checksum manifests.
- Passed showcase server tests (4/4), public static tests (3/3), ESLint, PDF
  text checks, recursive package checksums, and working-set checksums.
- Committed and pushed V3 package preparation as `a8a8ec0`.
- Published the tested `pages-dist` payload to `gh-pages` commit `c649178`.
  The public CDN initially served the prior asset for four checks, then served
  `assets/index-DZNAy0i7.js`; browser QA confirmed the 4,608 payload, zero
  horizontal overflow, and no console warnings or errors.
- At this preparation checkpoint, the planned V3 tag and organizer PR update
  remained owner-authorized release actions. Their later completion is
  recorded below.

## 2026-07-30 — Released V3 to the existing organizer PR

- Received explicit authorization to create the V3 release tag and update
  existing organizer PR #39 without opening a new PR.
- Confirmed tracked source state was clean, the branch matched its remote, no
  local or remote V3 tag existed, and PR #39 was open, non-draft, and
  mergeable.
- Created and pushed annotated tag `hackathon-2026-submission-v3`, peeled
  source commit `5f7e3f7c8f984fd378f8c147038d84fb2e4983b3`.
- Re-cloned the organizer fork branch, synchronized only
  `submissions/Track3-Aegis-Motion-GuardianSim`, reviewed the scoped diff,
  passed recursive package checksums, and pushed commit
  `2657aa23e84c9f75e4f55b8cdec49bba985a8870`.
- Updated PR #39 title/body in place to lead with the public showcase,
  separated Gate 3.2 safety evidence from the 4,608-pair decision workload,
  and linked immutable V3 source, video, evidence, and reproduction paths.
- GitHub's app connector could read but not mutate the organizer-owned
  repository (`403 Resource not accessible by integration`), so the already
  authenticated owner CLI performed the authorized metadata update. A
  subsequent independent read verified the exact body and head commit.
- Fresh-clone verification passed all ten package files; package-manifest
  SHA-256:
  `b55bd15e4c9bc7649e126bfd8c5a7229cecc735849871ec163090073395a0143`.
  V3 source, reproduction guide, full video, showcase, and organizer PDF all
  returned HTTP 200.
- Final PR state at verification: `OPEN`, non-draft, `MERGEABLE`, head
  `2657aa23e84c9f75e4f55b8cdec49bba985a8870`. No CI/status checks are
  configured on the submission branch. The PR was not merged.

## 2026-07-31 — Froze the Radeon Scale V2 implementation protocol

- Reviewed six active Track 3 competitors and Chaal's public benchmark
  artifacts. Recorded transferable practices without importing competitor
  claims or presenting unlike workloads as directly comparable.
- Defined GuardianSim's AMD-facing role as a parallel physical-simulation
  safety co-processor downstream of PPO, VLA, or scripted action proposals.
- Froze the V2 scale ladder at
  `1/16/64/256/512/1024/2048/4096` full manipulation worlds, 200 warmup
  steps, and 12,288 measured steps per batch.
- The declared largest batch contains 50,331,648 environment steps; the full
  sweep contains 98,512,896. Both remain target workload counts until a
  complete strict Radeon report exists.
- Added schema-2 protocol, raw-trial, report-hash, AMD/HIP, telemetry, derived
  metric, and exact-formal-workload validation.
- Added immutable per-batch output, numbered failure logs, exact-source resume,
  Git/ROCm/command receipts, final checksum generation, and a standalone
  strict validator.
- Updated the local organizer-PR record with the plain-language architecture:
  a policy proposes; Radeon simulates; GuardianSim executes one eligible
  action or stops. The public organizer PR was not changed at this stage.
- Added the same architecture to the local showcase hero without adding any
  unverified V2 performance result. Server/static render tests and ESLint
  passed.
- Full local verification passed 111/111 Python tests, Ruff, compilation, and
  `git diff --check`.
- Browser QA passed at 1440 × 1000 and 390 × 844 with zero page overflow,
  zero hero-content overflow, a 32.77 px mobile action-to-card gap, and no
  console warning or error.

## 2026-07-31 — Completed and preserved Radeon Scale V2

- Launched the capacity-only preflight from source commit
  `3d8021a237ca0dfca41c98df1b492b7b9a523b4f`; all declared capacities
  through 4,096 worlds passed.
- Ran the frozen formal ladder once at
  `1/16/64/256/512/1024/2048/4096` worlds. No formal trial failed or retried.
- Strict schema-2 validation passed against protocol
  `bcb91e081b196a5b6274ce1efd461d2005f1c1505dbd7020e9fbbaab0bb536e8`.
- Verified largest-batch measurements:
  - `4,096` full headless manipulation scenes;
  - `50,331,648` measured environment steps;
  - `152,099.018 environment-steps/s`;
  - `1,028.069×` speedup and `25.099%` parallel efficiency;
  - `98.651%` mean / `99%` peak GPU utilization;
  - `6.25 GiB` peak VRAM.
- Verified `98,512,896` total measured environment steps across the complete
  eight-batch sweep. The evidence keeps the falling post-256 parallel
  efficiency visible as the saturation curve.
- Downloaded and preserved the raw preflight and formal outputs, trial logs,
  source/launch/ROCm receipts, validation files, checksums, and archives under
  `docs/evidence/radeon-scale-v2-*`.
- Added a plain-language result note and updated the local competition
  positioning, PR addendum, README, showcase, and render assertions. No public
  push or organizer PR update was made at this checkpoint.
- Re-ran strict validation and both raw checksum manifests, then passed
  108/108 Python unit tests, Python compilation, `git diff --check`, 5/5
  server-rendered showcase tests, 3/3 static Pages tests, both builds, and
  ESLint.
- Used exact 1,440 × 1,000 and 390 × 844 browser emulation to inspect the hero,
  four representative scale cards, the 4,096-world tile map, and the compute
  receipt. Page width matched viewport width in both sizes and no runtime or
  browser-log error was recorded.
- A repository-wide run with the current latest Ruff reported 68 existing
  findings across upstream `franka_fruit_pick`, historical scripts, tests, and
  older GuardianSim modules. This V2 result stage changes no Python source and
  did not rewrite unrelated lint debt.

## 2026-07-31 — Rebuilt the report and silent preview around Scale V2

- Replaced the old Scale V1 section in `TECHNICAL_REPORT.md` with the frozen
  eight-batch Scale V2 protocol, complete measurement table, saturation note,
  4,096-world GPU/VRAM receipt, and explicit non-training claim boundary.
- Built `output/pdf/GuardianSim-Technical-Report.pdf` with the bundled
  ReportLab runtime. `pdfinfo` reported eight A4 pages and no encryption,
  forms, JavaScript, or suspect objects.
- Rendered all eight PDF pages to PNG at 140 DPI. Reviewed the contact sheet
  and full-resolution pages 5–7, which contain the new scale table, Safety
  Swarm section, results table, deliverables, and limitations. No clipping,
  table overflow, or footer collision was found.
- Extracted PDF text and confirmed the new `4,096`, `152,099`,
  `98,512,896`, `4,608`, and `30/30` claims are present; superseded
  `35,166`, `228.16`, and `337,000` Scale V1 claims are absent.
- Revised the supplementary visual builder to use immutable Scale V2,
  Safety Swarm V2, Gate 3.2, and Seed 411 sources. Preserved all prior V3/V4
  media under their original filenames.
- Generated `GuardianSim-Radeon-Parallel-Futures-review-v4.mp4` and its
  sidecar, preview, and validation receipt. The visual now leads with 4,096
  full parallel scenes and 152,099 environment-steps/s, then shows the
  eight-point curve and `4,608 → 5 → 1` decision funnel.
- Corrected the visual qualifying-candidate cells to the report-backed
  A05/A07/A09/A11/A13 indices before final encoding.
- Strict video validation passed 80.0 seconds, 1920×1080, 20 FPS, eight sampled
  decodes, complete video decode, all source hashes, locked metrics, chapter
  bounds, and simulation-only claim boundaries.
- Reviewed seven frames decoded from the completed MP4 across all six chapters.
  Titles, cards, graph labels, candidate cells, replay overlays, proof metrics,
  and closing architecture remain within their frames.
- Prepared narrated V5 script and validator inputs but did not call Qwen TTS.
  No public upload, package replacement, commit, push, Pages deployment, or
  organizer PR update occurred in this stage.

## 2026-07-31 — Generated the Scale V2 narrated V5 review candidate

- Received owner approval for the silent V4 visual direction and generated six
  English segments with Qwen3-TTS Instruct Flash, `Ethan` voice, using the
  existing ignored local credential path.
- Kept the already accepted direct, engineer-to-engineer delivery instruction;
  no key or authentication value was printed or stored in artifact metadata.
- Two alternate closing lines synthesized too slowly for the fixed eight-second
  chapter and were rejected by the timing guard. Shortened the line rather
  than speeding up the voice. The accepted close is 3.680 seconds and leaves
  4.320 seconds of breathing room.
- Built `GuardianSim-Radeon-Parallel-Futures-narrated-v5.mp4`, SHA-256
  `d590a711950b17a096361e0b7ba39b9842a848c7b0cf7b78d2aff63b5eab8f8d`.
- Verified all segment windows. The tightest is the six-second compute hook,
  which still leaves 1.440 seconds after its narration.
- Strict V5 validation passed 80.0 seconds, 1920×1080, 20 FPS, full A/V decode,
  eight sampled decodes, visual-source identity, six narration hashes, fixed
  caption hash, evidence-source hashes, metrics, and claim boundaries.
- Post-mux audio inspection reported 96 kHz mono AAC, approximately -18.4 dB
  mean volume and -1.1 dB maximum sample level after the -16 LUFS target
  normalization pipeline.
- Reviewed chapter frames with burned captions. Captions remain centered inside
  the safe lower margin and do not obscure the scale cards, Safety Swarm
  funnel, replay labels, proof cards, or closing architecture.
- V5 remains a local review candidate; no source commit, push, public release,
  package replacement, Pages deployment, or organizer PR mutation occurred.

## 2026-08-01 — Assembled and rehearsed the local V4 official package

- Replaced only the local official-package candidate artifacts: copied the
  inspected eight-page Scale V2 PDF, the owner-approved narrated V5 preview,
  and the strict Scale V2 report and validator receipt into
  `docs/submission/official-package/Track3-Aegis-Motion-GuardianSim`.
- Rewrote the package and evidence READMEs around the eight-point Scale V2
  curve. Kept the historical 54-world Parallel Futures smoke and Safety Swarm
  formal evidence, while explicitly separating physics throughput,
  candidate-world pairs, independent safety executions, and physical-robot
  claims.
- Regenerated `SHA256SUMS`; its SHA-256 is
  `f8a18439e1b1009ae807e79142f499df4a65de939c7f5e83729e0647afd8b0bd`.
- Rehearsed the package from a clean temporary directory. All ten manifest
  entries matched, strict Scale V2 validation passed, package JSON receipts
  parsed, and FFmpeg decoded the complete narrated preview with both streams.
  The candidate totals `3,551,598` bytes across ten payload files plus the
  manifest.
- Audited for old Scale V1 headline text. None remains in the candidate
  package; older figures are confined to labeled V3 history and historical raw
  evidence.
- Updated the local PR/release notes with the pending V4 replacement and
  manifest identity. Did not commit, tag, push, deploy Pages, edit organizer
  PR #39, or claim that planned V4 URLs already exist.
- Final release-candidate checks passed: 108/108 Python tests and compilation;
  5/5 server-rendered and 3/3 static Pages tests; both front-end builds and
  ESLint; strict Scale V2, silent V4, and narrated V5 validators; all package
  checksums; full packaged audio/video decode; and `git diff --check`.

## 2026-08-01 — Released V4 to the existing organizer PR

- Received owner authorization and committed the exact reviewed source/package
  set as `0710dca1de8e7627c19a992164169c41e70ac338` with message
  `Publish Radeon Scale V2 submission`.
- Created and pushed annotated tag `hackathon-2026-submission-v4`; GitHub's tag
  object peels to the exact release commit. Existing V1–V3 tags were unchanged.
- Published the tested static showcase to `gh-pages` commit
  `43af7d9578ff0f992fd1b3b242e59400123ede8f`.
- Re-cloned the contest fork branch, replaced only
  `submissions/Track3-Aegis-Motion-GuardianSim`, passed all ten package
  checksums and diff hygiene, and pushed commit
  `2dad3d4037b4cf7c3ed7dd6a8ea64df874dc7f62`.
- Updated organizer PR #39 in place with the Scale V2 metrics, immutable V4
  links, owner-approved narrated preview, and policy-to-Radeon architecture.
  Verified `OPEN`, non-draft, `MERGEABLE`, and exact head `2dad3d4`; no new PR
  was opened and the organizer PR was not merged.
- Two independent Git clones encountered transient GitHub transport failures.
  Downloaded a fresh branch archive through the authenticated GitHub API and
  verified all ten package entries and manifest SHA-256
  `f8a18439e1b1009ae807e79142f499df4a65de939c7f5e83729e0647afd8b0bd`.
- Anonymous HTTP checks returned 200 for the V4 tag, reproduction guide,
  workflow video, narrated V5 preview, evidence directory, organizer PDF, PR,
  and Pages site. The live asset `assets/index-DaWXZz3t.js` contains the
  verified Scale V2 and PPO/VLA-to-Radeon messaging.
- Preserved all unrelated untracked review media and historical PDF/browser
  artifacts. Did not access or destroy the Radeon Cloud instance.

## 2026-08-01 — Audited the submission from the judge's view

- Verified organizer PR #39 is still open, non-draft, mergeable, and unchanged
  at package commit `2dad3d4`; it has no comments, reviews, or checks.
- Re-read the official Luma event, the exported governing Rules & Conditions,
  and the organizer repository README. Confirmed the Track 3 weights are
  `30/20/20/20/10` and the submission deadline remains August 6 at 23:59
  UTC+8.
- Updated the time-stamped competitor scan from four to six open Track 3
  entries. Added SmolVLA (#45) and Chaal (#49), preserving distinctions among
  PPO training samples, Genesis environment steps, candidate-world pairs, and
  independent safety executions.
- Added `docs/submission/JUDGE_RED_TEAM_2026-08-01.md` with the official
  score-path audit, current field comparison, risks, and the decision not to
  start another broad benchmark.
- Prepared a local PR-body refinement with a 90-second judge path and a
  criterion-by-criterion evidence table. It states the simulation boundary and
  explicitly makes no external upstream-patch claim.
- Did not move V4, alter frozen evidence, edit the organizer PR, push, or touch
  the Radeon Cloud instance in this audit step.

## 2026-08-01 — Published the judge-navigation refinement

- Committed and pushed the judge red-team audit and prepared PR record as
  source commit `35e3390` on `agent/parallel-futures-showcase`.
- Updated only the body of organizer PR #39. Added the 90-second path and the
  five-row official judging map; did not alter the package branch, V4 tag,
  Pages, source evidence, video, report, or Radeon Cloud instance.
- Verified the remote body matches the local prepared body after trailing
  newline normalization, SHA-256
  `f20b120aee0123fe122b6d1241984f051a87266a7bc326ab9000102bed6c5da1`.
- Re-verified PR #39 is `OPEN`, non-draft, and `MERGEABLE` at organizer head
  `2dad3d4037b4cf7c3ed7dd6a8ea64df874dc7f62`, with no comments, reviews, or
  checks.

## 2026-08-01 — Locked the final submission

- Chose deadline hardening instead of a last-minute upstream patch.
- Re-verified the V4 annotated tag and exact source commit, current organizer
  package head, PR state, Pages identity, and public judge paths.
- Anonymous HTTP range requests passed for eleven public endpoints. GitHub and
  Raw GitHub showed intermittent local TLS/EOF errors, but all affected reads
  succeeded on retry.
- Downloaded a fresh organizer branch archive through the GitHub API. All ten
  package files passed the manifest; total package size remains `3,551,598`
  bytes including `SHA256SUMS`.
- Passed strict Scale V2 schema-2 validation, strict full audio/video and
  source-identity validation for the 4:41.5 workflow video and 80-second Scale
  V2 preview, and 108/108 Python unit tests.
- Changed only PR #39's body to make the technical report and organizer
  evidence paths directly clickable. The package head, V4, Pages, code,
  reports, media, metrics, and Radeon instance remained unchanged.
- Final PR-body SHA-256 is
  `465d1d5c5bf4c6ce59bbc4cc5d945d1ee6cfb37bb45f410c7f64bcf874ce7b0c`.
- Added `docs/submission/FINAL_SUBMISSION_LOCK_2026-08-01.md` as the controlling
  pre-deadline freeze and monitoring record.

## 2026-08-03 — Completed and preserved Radeon Scale V3

- Ran the frozen Scale V3 suite from clean cloud worktree
  `/workspace/persistent/GuardianSim-scale-v3-formal` at commit `64ca781`.
- Completed 15/15 independent-process measurements: five repeats each at
  4,096, 8,192, and 16,384 complete Genesis robot worlds. The formal workload
  contains 293,601,280 measured environment steps.
- Strict schema-3 validation and the sealed `SHA256SUMS` both passed. The
  16,384-world formal aggregate is `278,051.244 env-steps/s` P50,
  `278,660.488 env-steps/s` P95, and `274,989.939–278,671.733 env-steps/s`
  min–max.
- Recorded `98.330%` weighted mean GPU utilization across the full suite,
  `100%` peak utilization, and `23,677,100,032 bytes` peak VRAM use.
- Downloaded the 19.6 KB evidence archive, verified archive SHA-256
  `b5adc496eadf9257cbcedf52104b2864ced3c459a2ca4fd2eb74909a549e3b0a`,
  and rechecked all sealed payload hashes on the local machine.
- Preserved the raw report, all 15 trial JSON files and logs, before/after
  ROCm receipts, launch and process records, strict validation receipts,
  checksums, and the original archive under
  `docs/evidence/radeon-scale-v3-formal-2026-08-03`.
- Kept the public V4 release, Pages deployment, organizer package, and PR #39
  unchanged. Scale V3 remains an isolated experiment until the owner approves
  how the new Radeon-first numbers should replace or supplement the released
  narrative.

## 2026-08-03 — Built the local Scale V3 judge-facing candidate

- Created isolated worktree
  `/Users/aolos/Downloads/stitch_/GuardianSim-scale-v3-showcase` on branch
  `agent/radeon-scale-v3-showcase`, based on verified Scale V3 evidence commit
  `7b59ebc`. Preserved the dirty released-V4 worktree unchanged.
- Selectively integrated the existing showcase architecture and replaced the
  Scale V2 presentation with the three-batch Scale V3 endurance evidence.
  Added source-backed rendering tests for schema-3 metrics and immutable
  evidence links.
- Put `16,384`, `293.6M`, `278,051`, and `98.33% / 100% peak` in the first
  desktop viewport. Added the three formal batches, five-repeat P50/P95/range,
  GPU utilization, VRAM, and capacity-preflight exclusion to the scale section.
- Preserved the explicit unit boundary between environment steps,
  candidate-world pairs, simulated safety executions, and physical-robot
  claims. Replaced ambiguous “physical executions” wording with “independent
  Genesis simulations” in the website, report, and video.
- Updated `TECHNICAL_REPORT.md` and built
  `output/pdf/GuardianSim-Technical-Report-Scale-V3-Candidate.pdf`. `pdfinfo`
  reported eight unencrypted A4 pages, no JavaScript, forms, or suspect flags.
  Rendered every page; visually checked the dense abstract, Scale V3 table,
  result table, references, headers, and footers. Final SHA-256 is
  `dc0f38bf47544187eec274d876d5f72cbecbf686d1c9f548227eb5e3beb9dcef`.
- Added a separate historical-safe V3 video generator and validator rather
  than overwriting the V2 scripts. Generated the silent
  `GuardianSim-Radeon-Scale-V3-review-v1.mp4`, 80.0 seconds at 1920×1080 and
  20 FPS. Full decode and source/metric validation passed; final video SHA-256
  is `b10515d7f880345a6db840f00d7236c1ae6f05da0b20ba7edf3a405434a7035f`
  and sidecar SHA-256 is
  `ccdeedccc34a8f5368218cfd86b2c72831cec191da346f6f58e69bdeef28f678`.
- Inspected title, all three scale stages, Safety Swarm funnel, accepted Seed
  411 replay, full four-card proof frame, and close. No text overflow, card
  escape, or metric collision was observed.
- Rebuilt and inspected the static site at 1440×1050 and 390×844. Both reported
  `scrollWidth == clientWidth`, and the updated Genesis-simulation wording was
  present. Full-page desktop and mobile screenshots were inspected.
- Verification passed: 116 Python tests, Python compilation, Vite Pages build,
  Vinext build, ESLint, 5 server-rendered tests, 3 static Pages tests, strict
  video validation, PDF text/structure checks, and `git diff --check`.
- Fixed clean-checkout reproducibility by explicitly tracking
  `showcase/build/sites-vite-plugin.ts`, which had been hidden by the generic
  `build/` ignore rule. A detached worktree at the candidate checkpoint rebuilt
  Vite Pages and Vinext and passed the 5/5 + 3/3 presentation tests.
- Wrote
  `docs/submission/RADEON_SCALE_V3_PRESENTATION_CANDIDATE_2026-08-03.md` as
  the local review record. Did not push, deploy Pages, replace the organizer
  package, move a tag, edit PR #39, or access/destroy the Radeon Cloud instance.
