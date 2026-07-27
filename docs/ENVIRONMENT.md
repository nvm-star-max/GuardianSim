# Environment and Dependency Record

## Formal Radeon Cloud run

The primary Gate 3.2 evidence was generated on 2026-07-26 in the AMD Radeon
Cloud **Blank OpenCode Workspace**, instance `u-13907-735d71cb`, from source
commit `67d3235c9e48f100d3785f78157ff9c31404b662`.

Facts captured before or with the formal run:

- Python `3.12.3`
- Genesis `1.2.3`
- PyTorch `2.9.1+gitff65f5b`
- HIP `7.2.53211-e1a6bc5663`
- one AMD Radeon GPU
- PCI device ID `0x744b`
- GFX architecture `gfx1100`

The cloud template name was recorded, but the provider did not expose a public
immutable image digest or a more specific marketing GPU name. GuardianSim does
not infer either value. The raw record is
[`evidence/gate-3-2/formal-environment.txt`](evidence/gate-3-2/formal-environment.txt).

## Reproduction target

- Native target: the same Radeon Cloud template with Python 3.12 and the
  exact ROCm wheels in `scripts/install_rocm_stack.sh`.
- Container target: `rocm/dev-ubuntu-24.04:7.2.1-complete`.
- Python dependency identity: `pyproject.toml` plus committed `uv.lock`.
- Evaluator manifest: `scripts/capture_environment.py`.

Capture a new machine-readable record:

```bash
RADEON_CLOUD_TEMPLATE="Blank OpenCode Workspace" \
RADEON_CLOUD_INSTANCE_ID="<instance-id>" \
uv run --frozen --no-sync python scripts/capture_environment.py \
  --require-gpu \
  --output outputs/evaluator-preflight/environment.json
```

The instance ID is provenance metadata, not a secret. Do not add credentials,
tokens, private keys, or personal information to the manifest.
