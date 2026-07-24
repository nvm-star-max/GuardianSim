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
git clone <YOUR_GUARDIANSIM_REPOSITORY_URL>
cd GuardianSim
uv python install 3.12
uv sync --python 3.12
scripts/install_rocm_stack.sh
```

Expected conditions:

- Python 3.12
- ROCm/HIP is present
- Exactly one AMD Radeon GPU is visible

## Install the upstream environment

Follow the pinned ROCm-wheel installation in the root README. Then run:

```bash
uv run python franka_fruit_pick/setup_assets.py
uv run python franka_fruit_pick/build_scene.py --steps 50 --save-frames
scripts/start_gpu_session.sh
```

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
