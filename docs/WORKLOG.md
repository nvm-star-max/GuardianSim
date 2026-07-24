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
