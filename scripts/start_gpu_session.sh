#!/usr/bin/env bash
set -euo pipefail

# Fast, repeatable start-of-session check. It records the exact hardware and
# source revision before any experiment consumes additional GPU time.

evidence_dir="${GUARDIANSIM_EVIDENCE_DIR:-outputs/evidence}"
mkdir -p "$evidence_dir"

started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf '%s\n' "$started_at" | tee "$evidence_dir/session-started-at.txt"
git rev-parse HEAD | tee "$evidence_dir/git-commit.txt"

uv run python scripts/verify_rocm.py | tee "$evidence_dir/rocm.json"

if command -v rocm-smi >/dev/null 2>&1; then
  rocm-smi | tee "$evidence_dir/rocm-smi.txt"
else
  echo "WARNING: rocm-smi is unavailable; PyTorch ROCm verification still passed." | tee "$evidence_dir/rocm-smi.txt"
fi

uv run python -m unittest discover -s tests -v
uv run python -m guardian_sim.cli | tee "$evidence_dir/planner-smoke.json"

echo
echo "GPU session checks passed."
echo "Set a timer for the planned session length and destroy the instance when finished."
