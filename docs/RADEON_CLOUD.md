# Radeon Cloud Runbook

Use the same email address as the approved Luma and AMD Developer Program registrations.

## Create the workspace

1. Open Radeon Cloud and go to **Profile → My Templates → Add Template**.
2. Select an Ubuntu 24.04 / ROCm 7.2.1 development image when available.
3. Select **Persistent (PVC)** storage.
4. Enable **SSH Access**.
5. Launch the template and enter through JupyterLab or SSH.

Never paste an SSH private key, password, API key, or verification code into the repository.

## Clone and verify

```bash
git clone https://github.com/nvm-star-max/GuardianSim.git
cd GuardianSim
scripts/install_system_deps.sh
uv python install 3.12
uv sync --python 3.12
scripts/install_rocm_stack.sh
```

Expected conditions:

- Python 3.12
- ROCm/HIP is present
- Exactly one AMD Radeon GPU is visible

## Install the upstream environment

Follow the pinned ROCm-wheel installation in the root README. Session A is a
single command after installation:

```bash
scripts/start_gpu_session.sh
```

It records the commit, ROCm/PyTorch device information, tests, a labeled
synthetic pipeline smoke test, and a real Genesis GPU scene probe with world and
wrist frames. If only the non-GPU setup is being prepared, set
`GUARDIANSIM_SKIP_SCENE_PROBE=1`.

## Session B / Gate 2.5 diagnostic run

Do not launch the diagnostic until local tests pass and the intended commit is
pushed. By default the command evaluates 15 candidates: five yaw angles crossed
with lateral offsets `-0.02, 0.00, +0.02 m`, all from one captured episode
state:

```bash
git pull --ff-only
/opt/venv/bin/python -m unittest discover -s tests -v
PYTHONUNBUFFERED=1 /opt/venv/bin/python scripts/run_candidate_dry_run.py \
  --pick 011_banana \
  --seed 41 \
  --output outputs/guardian_dry_run/candidates.json \
  2>&1 | tee outputs/guardian_dry_run/run.log
```

Required Gate 2.5 exit checks:

- JSON contains 15 ranked candidates.
- Every candidate was evaluated against the same `snapshot_fingerprint`.
- At least one candidate is reachable.
- Retained lift, path length, and clearance are finite.
- Every candidate contains a clearance diagnostic naming the responsible
  sample, robot link, obstacle, strict-overlap state, and overlap depth.
- The run log contains no unhandled exception.

Copy `outputs/guardian_dry_run/` into durable evidence. Do not expand to the
20-episode benchmark until the zero-clearance source has been explained and the
safety metric is demonstrably non-degenerate.

## Evidence to save

```bash
mkdir -p outputs/evidence
python3 scripts/verify_rocm.py | tee outputs/evidence/rocm.json
rocm-smi | tee outputs/evidence/rocm-smi.txt
git rev-parse HEAD | tee outputs/evidence/git-commit.txt
```

Use the Persistent PVC for datasets, checkpoints, videos, and evidence. Push source changes
to GitHub frequently. Destroy the active instance when work stops because it continues to
consume credits.

The full ten-credit allocation is planned in [`GPU_BUDGET.md`](GPU_BUDGET.md).
