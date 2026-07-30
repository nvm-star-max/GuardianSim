#!/usr/bin/env bash
set -eu
cd /workspace/persistent/GuardianSim-safety-swarm-v2
exec env PYTHONUNBUFFERED=1 /opt/venv/bin/python scripts/run_safety_swarm_smoke.py \
  --v2-tier full-16 \
  --output outputs/safety-swarm-v2-full-16-2026-07-30/report.json \
  --preflight-output outputs/safety-swarm-v2-full-16-2026-07-30/preflight.json \
  --validation-output outputs/safety-swarm-v2-full-16-2026-07-30/validation.json
