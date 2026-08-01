# GuardianSim Reproducibility Guide

This is the evaluator-first path for GuardianSim, a Track 3 Physical AI
submission. It separates four kinds of evidence:

1. **source preflight** — tests the decision core and validates the preserved
   formal report; it does not require a GPU;
2. **Radeon GPU smoke** — builds a real Genesis scene, evaluates three
   counterfactual grasp candidates from one captured state, and validates the
   resulting machine-readable report;
3. **formal safety benchmark evidence** — validates the immutable 30-scenario
   Gate 3.2 report already recorded on AMD Radeon Cloud;
4. **formal decision-scale evidence** — validates the immutable Safety Swarm
   V2 run covering 18 candidate actions across 256 uncertainty worlds each.

The published metrics are simulation results. They are not claims of
physical-robot deployment or universal safety.

## 1. Supported environment

The shortest supported route is an AMD Radeon Cloud **Blank OpenCode
Workspace** with one visible Radeon GPU:

| Component | Formal run / supported value |
| --- | --- |
| Python | `3.12.3` (`3.12` required) |
| PyTorch | `2.9.1+gitff65f5b` |
| HIP runtime reported by PyTorch | `7.2.53211-e1a6bc5663` |
| ROCm wheel channel | `rocm-rel-7.2.1` |
| GPU | AMD Radeon Cloud device `0x744b`, `gfx1100` |
| Genesis | `1.2.3` |
| Dependency resolver | `uv 0.11.28` |
| Project dependencies | committed `uv.lock` |

The original cloud template did not expose an immutable public image digest.
For that reason, the native path pins the Python and ROCm package stack, and
the Docker path starts from `rocm/dev-ubuntu-24.04:7.2.1-complete`. The
formal-run environment record is preserved at
`docs/evidence/gate-3-2/formal-environment.txt`.

## 2. Native Radeon Cloud setup

Start from a fresh persistent workspace:

```bash
git clone https://github.com/nvm-star-max/GuardianSim.git
cd GuardianSim

scripts/install_system_deps.sh
uv python install 3.12
# Blank OpenCode provides its persistent ROCm environment here:
export UV_PROJECT_ENVIRONMENT=/opt/venv
uv sync --frozen --python 3.12
scripts/install_rocm_stack.sh
```

`install_rocm_stack.sh` downloads the exact PyTorch, torchvision, torchaudio,
and Triton ROCm wheels into `.cache/rocm-wheels`, replaces any CPU PyTorch
resolved by the base lock, and fails unless one Radeon GPU is visible through
HIP. The optional upstream LeRobot training stack is not required by the
GuardianSim evaluator; install it only when needed by setting
`GUARDIANSIM_INSTALL_LEROBOT=1`.

All evaluator commands use `uv run --no-sync` after this replacement. This is
intentional: another automatic `uv sync` could replace the official ROCm wheel
with the default package selected during platform-independent locking.

The Blank OpenCode image may not set `VIRTUAL_ENV`, even though its working
ROCm Python is `/opt/venv/bin/python`. The evaluator scripts automatically
reuse `/opt/venv` when it exists. Without this check, uv can create an empty
`.venv` and correctly report that PyTorch is missing. On another Linux image,
set `UV_PROJECT_ENVIRONMENT` to the intended environment before installation.

No API key, model token, training dataset, or external checkpoint is required
for the GuardianSim smoke or preserved benchmark validation. The Franka and
YCB simulation assets needed by these commands are bundled under `assets/`;
their provenance and licenses are documented in the root README and
`assets/robots/franka/README.md`.

## 3. Evaluator preflight

Run this before any real simulation:

```bash
./scripts/evaluator_preflight.sh
```

It writes an auditable bundle to `outputs/evaluator-preflight/` containing:

- source commit and dirty-state metadata;
- OS, Python, package, PyTorch/HIP, GPU, and `rocm-smi` facts;
- the complete unit-test log;
- a deterministic synthetic decision-loop smoke;
- strict validation output for the preserved Gate 3.2 report;
- `SHA256SUMS`.

Expected terminal ending:

```text
Evaluator preflight passed. Evidence: outputs/evaluator-preflight
```

On a non-GPU review machine, validate only source and preserved evidence:

```bash
./scripts/evaluator_preflight.sh --no-gpu
```

The non-GPU mode is not proof of ROCm execution and is labeled accordingly in
the captured environment JSON.

## 4. One-command Radeon GPU smoke

```bash
./scripts/run_evaluator_smoke.sh
```

This command:

1. runs the GPU-required preflight;
2. initializes Genesis with `gs.gpu`, builds the Franka fruit-picking scene,
   advances five steps, and saves world/wrist frames;
3. captures one banana scene state and evaluates yaw alternatives
   `-45°`, `0°`, and `+45°` from that same snapshot;
4. validates schema, candidate count, unique IDs, ordered ranks, finite
   physical metrics, finite risk/utility scores, and snapshot identity;
5. writes checksums for all outputs.

Expected terminal ending:

```text
Radeon GPU smoke passed. Evidence: outputs/evaluator-smoke
```

Key files:

- `outputs/evaluator-smoke/preflight/environment.json`
- `outputs/evaluator-smoke/genesis-probe/scene-probe.json`
- `outputs/evaluator-smoke/genesis-probe/world.png`
- `outputs/evaluator-smoke/genesis-probe/wrist.png`
- `outputs/evaluator-smoke/candidates.json`
- `outputs/evaluator-smoke/candidate-validation.json`
- `outputs/evaluator-smoke/SHA256SUMS`

This bounded three-candidate run proves the real counterfactual evaluation
path; it is not used for the 30-scenario performance claim.

## 5. Validate the formal result

The immutable schema-5 report is included in the repository. Re-run the strict
validator:

```bash
uv run --frozen --no-sync python scripts/validate_gate32_report.py \
  docs/evidence/gate-3-2/formal-report.json

cd docs/evidence/gate-3-2
sha256sum -c formal-sha256.txt
```

On macOS, use `shasum -a 256 -c formal-sha256.txt` instead.

The validator must report:

- `validated_episode_count: 30`;
- protocol SHA-256
  `8f23247001e05f39817225ed13f028321fbb9b9c694aaacd5b987fe61ee1fb3c`;
- baseline repeatable safe completion `18/30`;
- GuardianSim repeatable safe completion `30/30`;
- baseline/GuardianSim independent safe executions `58/90` and `90/90`;
- clutter contacts `30` and `0`.

The primary evidence narrative and exact metrics are in
`docs/evidence/gate-3-2/README.md`. Do not regenerate or edit that report to
obtain the published numbers.

### 5.1 Validate the 4,608-pair decision-scale result

The Safety Swarm V2 report is a second formal result with a different unit of
analysis. It measures candidate-by-uncertainty stress testing and must not be
added to the 30-scenario Gate 3.2 safety sample count.

```bash
uv run --frozen --no-sync python \
  scripts/validate_safety_swarm_v2_report.py --require-radeon \
  docs/evidence/safety-swarm-v2-formal-2026-07-30/formal-report.json

cd docs/evidence/safety-swarm-v2-formal-2026-07-30
sha256sum -c SHA256SUMS
```

On macOS, use `shasum -a 256 -c SHA256SUMS` instead.

The strict validator must report:

- `candidate_world_count: 4608`;
- `candidate_count: 18` and `world_count_per_candidate: 256`;
- five qualifying candidates;
- selected candidate
  `yaw_-45.0_retreat_+0.000_approach_+0.140`;
- selected result `256/256` safe with zero sampled clutter contacts;
- report SHA-256
  `a3e86baa03e84d75a81062fee5f9f22770a3753708c116168174ea291c7a93cf`.

The full search population contains 4,608 candidate-world pairs. It is an
engineering stress-test population, not 4,608 independent robot trials and
not a physical-robot safety guarantee.

## 6. Docker path

The repository includes a complete source-and-runtime Dockerfile:

```bash
docker build --platform=linux/amd64 \
  -f docker/Dockerfile \
  -t guardiansim:rocm7.2.1 .

docker run --rm -it \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  --group-add render \
  --security-opt seccomp=unconfined \
  --ipc=host \
  --shm-size=8g \
  guardiansim:rocm7.2.1
```

Inside the container:

```bash
./scripts/evaluator_preflight.sh
./scripts/run_evaluator_smoke.sh
```

The Dockerfile and dependency lock are pinned in the repository. A complete GPU
build/run still requires a Linux x86-64 host with ROCm-compatible device
passthrough; macOS Docker cannot validate `/dev/kfd`.

## 7. Troubleshooting

- **`PyTorch is not a ROCm build`** — run
  `scripts/install_rocm_stack.sh`; do not use the default PyPI CPU wheel.
- **PyTorch is installed in `/opt/venv` but uv reports it missing** — export
  `UV_PROJECT_ENVIRONMENT=/opt/venv`, or use the evaluator scripts, which
  detect the Blank OpenCode layout automatically.
- **Wrong Python version** — run
  `uv python install 3.12 && uv sync --frozen --python 3.12`.
- **No visible GPU or more than one GPU** — expose exactly one Radeon device.
  The frozen reports were generated with one visible GPU.
- **Headless rendering failure** — keep the system OpenGL/Vulkan packages from
  `scripts/install_system_deps.sh`; use the supported Blank OpenCode/Jupyter
  workspace or start an Xvfb display when using a different headless image.
- **`groups: cannot find name for group ID ...`** — this container warning is
  harmless if `rocm-smi` and `scripts/verify_rocm.py` pass.
- **Cross-process snapshot mismatch** — expected strict behavior. Genesis may
  rebuild a different base-scene fingerprint in a new process. Never append
  to an existing formal report unless the validator accepts the exact
  configuration and base snapshot; never use `--fresh` on preserved evidence.
- **Slow first run** — Genesis compiles kernels during the first scene build.
  The bounded smoke intentionally uses only three candidates.

## 8. Clean-room acceptance checklist

- [ ] Fresh clone completed without untracked manual assets.
- [ ] `uv sync --frozen` accepted `uv.lock`.
- [ ] Environment manifest reports Linux, Python 3.12, HIP, and one GPU.
- [ ] All unit tests pass.
- [ ] Real Genesis probe saves two camera frames.
- [ ] Three-candidate report passes strict smoke validation.
- [ ] Formal schema-5 report validates 30/30 and checksum verification passes.
- [ ] No published number is sourced from the synthetic smoke.
