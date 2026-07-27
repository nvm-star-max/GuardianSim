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
export UV_PROJECT_ENVIRONMENT=/opt/venv
uv sync --frozen --python 3.12
scripts/install_rocm_stack.sh
```

Expected conditions:

- Python 3.12
- ROCm/HIP is present
- Exactly one AMD Radeon GPU is visible

## Evaluator path

Run the concise evaluator preflight and bounded real Genesis smoke:

```bash
scripts/evaluator_preflight.sh
scripts/run_evaluator_smoke.sh
```

The first command records the commit, full environment, tests, a labeled
synthetic decision-loop smoke, and strict formal-report validation. The second
adds a real Genesis GPU scene probe and a validated three-candidate
counterfactual run. See the root [`REPRODUCIBILITY.md`](../REPRODUCIBILITY.md)
for expected outputs and the Docker alternative.

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
- Support-surface contact appears only in `support_contact_diagnostic` and does
  not determine `collision_margin_m`.
- The run log contains no unhandled exception.

Copy `outputs/guardian_dry_run/` into durable evidence. Do not expand to the
20-episode benchmark until the zero-clearance source has been explained and the
safety metric is demonstrably non-degenerate.

## Fixed-seed real execution benchmark

After Gate 2.6 passes, run a two-episode smoke test before the full benchmark:

```bash
PYTHONUNBUFFERED=1 /opt/venv/bin/python scripts/run_fixed_seed_benchmark.py \
  --episodes 2 \
  --seed-start 101 \
  --output outputs/fixed_seed_benchmark/smoke.json
```

The full run uses 20 deterministic object-layout perturbations. Each episode:

1. restores a fixed-seed jittered scene snapshot;
2. evaluates all 15 counterfactual candidates;
3. independently re-executes the nominal baseline candidate;
4. independently re-executes GuardianSim's top-ranked candidate;
5. writes progress after the episode, so an interrupted run retains evidence.

If the process is restarted with the same command, it resumes the contiguous
completed seed prefix only when the run configuration and rebuilt base snapshot
fingerprint match. Pass `--fresh` only when intentionally replacing an existing
report.

```bash
PYTHONUNBUFFERED=1 /opt/venv/bin/python scripts/run_fixed_seed_benchmark.py \
  --episodes 20 \
  --seed-start 101 \
  --output outputs/fixed_seed_benchmark/report.json
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

## Gate 2.8 robust-selection validation

Gate 2.8 policy is fixed before cloud outcomes are inspected:

- initial rollout for all 15 candidates;
- top-three shortlist plus nominal;
- two additional confirmation rollouts per shortlisted candidate;
- conservative aggregation uses minimum reachability, alignment, stability,
  and clearance plus maximum path length and uncertainty;
- candidates require worst-observed stability of at least `0.60`;
- an alternative must exceed nominal robust success by at least `0.02`;
- otherwise the planner executes nominal.

First rerun the three Gate 2.7 failure seeds independently:

```bash
for seed in 104 107 120; do
  PYTHONUNBUFFERED=1 /opt/venv/bin/python scripts/run_fixed_seed_benchmark.py \
    --episodes 1 \
    --seed-start "$seed" \
    --output "outputs/gate-2-8/failure-seed-${seed}.json" \
    2>&1 | tee "outputs/gate-2-8/failure-seed-${seed}.log"
done
```

Do not begin a full rerun unless all three reports complete, GuardianSim
independent execution succeeds, and confirmation evidence is present.
