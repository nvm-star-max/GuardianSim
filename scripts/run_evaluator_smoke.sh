#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# Match evaluator_preflight.sh when this script is invoked directly.
if [[ -z "${UV_PROJECT_ENVIRONMENT:-}" && -z "${VIRTUAL_ENV:-}" && -x /opt/venv/bin/python ]]; then
  export UV_PROJECT_ENVIRONMENT=/opt/venv
fi

evidence_dir="${1:-outputs/evaluator-smoke}"
mkdir -p "$evidence_dir"

scripts/evaluator_preflight.sh "$evidence_dir/preflight"

uv run --frozen --no-sync python scripts/probe_genesis.py \
  --steps 5 \
  --save-frames \
  --output-dir "$evidence_dir/genesis-probe" \
  | tee "$evidence_dir/genesis-probe.log"

uv run --frozen --no-sync python scripts/run_candidate_dry_run.py \
  --pick 011_banana \
  --seed 41 \
  --yaws -45 0 45 \
  --offsets 0 \
  --output "$evidence_dir/candidates.json" \
  | tee "$evidence_dir/candidates.log"

uv run --frozen --no-sync python scripts/validate_candidate_report.py \
  "$evidence_dir/candidates.json" \
  | tee "$evidence_dir/candidate-validation.json"

uv run --frozen --no-sync python scripts/write_checksums.py "$evidence_dir"

echo "Radeon GPU smoke passed. Evidence: $evidence_dir"
