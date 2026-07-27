#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# Radeon Cloud's Blank OpenCode template ships its working ROCm environment at
# /opt/venv but may leave VIRTUAL_ENV unset. Reuse it instead of letting uv
# create an empty project-local environment.
if [[ -z "${UV_PROJECT_ENVIRONMENT:-}" && -z "${VIRTUAL_ENV:-}" && -x /opt/venv/bin/python ]]; then
  export UV_PROJECT_ENVIRONMENT=/opt/venv
fi

require_gpu=1
if [[ "${1:-}" == "--no-gpu" ]]; then
  require_gpu=0
  shift
fi
evidence_dir="${1:-outputs/evaluator-preflight}"
mkdir -p "$evidence_dir"

git rev-parse HEAD | tee "$evidence_dir/git-commit.txt"

capture_args=(--output "$evidence_dir/environment.json")
if [[ "$require_gpu" -eq 1 ]]; then
  capture_args+=(--require-gpu)
fi
uv run --frozen --no-sync python scripts/capture_environment.py "${capture_args[@]}" \
  | tee "$evidence_dir/environment.stdout.json"

if [[ "$require_gpu" -eq 1 ]]; then
  uv run --frozen --no-sync python scripts/verify_rocm.py | tee "$evidence_dir/rocm.json"
  rocm-smi | tee "$evidence_dir/rocm-smi.txt"
fi

uv run --frozen --no-sync python -m unittest discover -s tests -v \
  2>&1 | tee "$evidence_dir/unit-tests.log"
uv run --frozen --no-sync python -m guardian_sim.cli \
  | tee "$evidence_dir/synthetic-planner-smoke.json"
uv run --frozen --no-sync python scripts/validate_gate32_report.py \
  docs/evidence/gate-3-2/formal-report.json \
  --compact \
  | tee "$evidence_dir/gate-3-2-validation.json"

uv run --frozen --no-sync python scripts/write_checksums.py "$evidence_dir"

echo "Evaluator preflight passed. Evidence: $evidence_dir"
