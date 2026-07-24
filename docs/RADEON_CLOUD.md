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

## Session B dry run

Do not launch Session B until the local tests pass and the intended commit is
pushed. The first command evaluates exactly five yaw candidates from one
captured episode state:

```bash
git pull --ff-only
/opt/venv/bin/python -m unittest discover -s tests -v
PYTHONUNBUFFERED=1 /opt/venv/bin/python scripts/run_candidate_dry_run.py \
  --pick 011_banana \
  --seed 41 \
  --output outputs/guardian_dry_run/candidates.json \
  2>&1 | tee outputs/guardian_dry_run/run.log
```

Required exit checks:

- JSON contains five ranked candidates.
- Every candidate was evaluated against the same `snapshot_fingerprint`.
- At least one candidate is reachable.
- Retained lift, path length, and clearance are finite.
- The run log contains no unhandled exception.

Copy `outputs/guardian_dry_run/` off the instance before destroying it. Do not
expand to the 20-episode benchmark until these checks pass.

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
