#!/usr/bin/env bash
set -euo pipefail

# Install the exact ROCm/PyTorch stack used by the AMD Track 3 reference demo.
# Run this once from a Persistent (PVC) workspace. Downloaded wheels are cached
# under the repository so instance recreation does not spend GPU time downloading.

if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: uv is required. Install it before starting a billed GPU session." >&2
  exit 1
fi

python_version="$(uv run --frozen python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [[ "$python_version" != "3.12" ]]; then
  echo "ERROR: expected the project environment to use Python 3.12, found $python_version." >&2
  echo "Run: uv python install 3.12 && uv sync --python 3.12" >&2
  exit 2
fi

wheel_dir="${GUARDIANSIM_WHEEL_CACHE:-$PWD/.cache/rocm-wheels}"
mkdir -p "$wheel_dir"

base_url="https://repo.radeon.com/rocm/manylinux/rocm-rel-7.2.1"
wheels=(
  "torch-2.9.1%2Brocm7.2.1.lw.gitff65f5bc-cp312-cp312-linux_x86_64.whl"
  "torchvision-0.24.0%2Brocm7.2.1.gitb919bd0c-cp312-cp312-linux_x86_64.whl"
  "torchaudio-2.9.0%2Brocm7.2.1.gite3c6ee2b-cp312-cp312-linux_x86_64.whl"
  "triton-3.5.1%2Brocm7.2.1.gita272dfa8-cp312-cp312-linux_x86_64.whl"
)

for encoded_name in "${wheels[@]}"; do
  local_name="${encoded_name//%2B/+}"
  target="$wheel_dir/$local_name"
  if [[ ! -s "$target" ]]; then
    echo "Downloading $local_name"
    curl --fail --location --retry 3 --output "$target" "$base_url/$encoded_name"
  else
    echo "Using cached $local_name"
  fi
done

uv pip uninstall torch torchvision torchaudio triton pytorch-triton pytorch-triton-rocm || true
uv pip install "$wheel_dir"/*.whl

if [[ "${GUARDIANSIM_INSTALL_LEROBOT:-0}" == "1" ]]; then
  uv pip install "lerobot[training,smolvla]==0.6.0"
fi

uv run --frozen --no-sync python scripts/verify_rocm.py
