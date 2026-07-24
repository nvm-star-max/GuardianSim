#!/usr/bin/env bash
set -euo pipefail

# Save a compact end-of-session record before destroying the cloud instance.

evidence_dir="${GUARDIANSIM_EVIDENCE_DIR:-outputs/evidence}"
mkdir -p "$evidence_dir"

date -u +%Y-%m-%dT%H:%M:%SZ | tee "$evidence_dir/session-ended-at.txt"
git status --short | tee "$evidence_dir/git-status-at-end.txt"

if command -v rocm-smi >/dev/null 2>&1; then
  rocm-smi | tee "$evidence_dir/rocm-smi-at-end.txt"
fi

echo
echo "Checkpoint code, datasets, models, and evidence now."
echo "Then destroy the Radeon Cloud instance in Profile; closing the browser is not enough."
