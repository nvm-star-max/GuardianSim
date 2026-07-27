# =============================================================================
# GuardianSim — AMD ROCm evaluator environment
# -----------------------------------------------------------------------------
# Reproduces the exact host setup this repo is developed/tested on:
#   - Ubuntu 24.04  (=> system Python 3.12, matching the ROCm cp312 wheels)
#   - ROCm 7.2.1 runtime + dev libraries
#   - Prebuilt ROCm 7.2.1 torch/vision/audio/triton wheels (repo.radeon.com)
#   - genesis-world + GuardianSim evaluator deps resolved from uv.lock
#   - Vulkan / OpenGL runtime so Genesis can render camera images headless
#
# The formal benchmark was recorded on an AMD Radeon Cloud gfx1100 device.
#
# The image contains the source, bundled simulation assets, and Python
# environment in /opt/venv. A bind mount is optional for development:
#
#   docker build -f docker/Dockerfile -t guardiansim:rocm7.2.1 .
#   docker run --rm -it --network=host \
#       --device=/dev/kfd --device=/dev/dri \
#       --group-add video --group-add render \
#       --security-opt seccomp=unconfined \
#       --cap-add=SYS_PTRACE \
#       --ipc=host --shm-size=8g \
#       -v "$PWD":/workspace/GuardianSim \
#       -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix \
#       guardiansim:rocm7.2.1
# =============================================================================
FROM rocm/dev-ubuntu-24.04:7.2.1-complete

ENV DEBIAN_FRONTEND=noninteractive

# --- System runtime deps -----------------------------------------------------
# OpenGL/Vulkan/X libs are required by Genesis' rasterizer + OpenCV image I/O;
# xvfb lets the GLX renderer run on a headless host; ffmpeg backs video export.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl wget git \
        libgl1 libglu1-mesa libegl1 libgles2 libglvnd0 libosmesa6 \
        libglib2.0-0 libsm6 libxext6 libxrender1 libx11-6 \
        libxi6 libxrandr2 libxcursor1 libxinerama1 libxfixes3 \
        libvulkan1 vulkan-tools mesa-vulkan-drivers \
        xvfb ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Make the AMD GPU reachable for the root user inside the container.
RUN groupadd -f render && usermod -aG render,video root

# --- uv (pinned to the version used on the host) -----------------------------
COPY --from=ghcr.io/astral-sh/uv:0.11.28 /uv /usr/local/bin/uv

# Put the project virtualenv at a fixed path outside the (mounted) source tree
# so a bind-mount of the repo never shadows the installed environment.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON=python3.12 \
    UV_LINK_MODE=copy \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

WORKDIR /workspace/GuardianSim

# --- Base dependencies (genesis-world, numpy, trimesh, opencv, ...) -----------
# Resolved reproducibly from uv.lock; --no-install-project skips building the
# local package (its scripts add themselves to sys.path, so no install needed).
COPY pyproject.toml uv.lock ./
RUN uv sync --no-install-project --frozen

# --- ROCm 7.2.1 torch stack (replaces whatever torch uv resolved) ------------
ARG TORCH_WHL=torch-2.9.1+rocm7.2.1.lw.gitff65f5bc-cp312-cp312-linux_x86_64.whl
ARG VISION_WHL=torchvision-0.24.0+rocm7.2.1.gitb919bd0c-cp312-cp312-linux_x86_64.whl
ARG AUDIO_WHL=torchaudio-2.9.0+rocm7.2.1.gite3c6ee2b-cp312-cp312-linux_x86_64.whl
ARG TRITON_WHL=triton-3.5.1+rocm7.2.1.gita272dfa8-cp312-cp312-linux_x86_64.whl
ARG ROCM_WHL_BASE=https://repo.radeon.com/rocm/manylinux/rocm-rel-7.2.1

RUN set -eux; \
    mkdir -p /tmp/wheels && cd /tmp/wheels; \
    for w in "$TORCH_WHL" "$VISION_WHL" "$AUDIO_WHL" "$TRITON_WHL"; do \
        url="${ROCM_WHL_BASE}/$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$w")"; \
        wget -q -O "$w" "$url"; \
    done; \
    uv pip uninstall torch torchvision torchaudio triton pytorch-triton pytorch-triton-rocm || true; \
    uv pip install "$TORCH_WHL" "$VISION_WHL" "$AUDIO_WHL" "$TRITON_WHL"; \
    cd / && rm -rf /tmp/wheels

# --- GuardianSim source and bundled assets ---------------------------------
COPY README.md REPRODUCIBILITY.md ./
COPY guardian_sim ./guardian_sim
COPY franka_fruit_pick ./franka_fruit_pick
COPY scripts ./scripts
COPY tests ./tests
COPY assets ./assets
RUN uv pip install --no-deps -e .

# --- Runtime environment -----------------------------------------------------
# Genesis renders through GLX on this stack (matches the host dev setup).
# The supported Radeon Cloud stack does not require an HSA architecture
# override. Do not add one unless the evaluator's own hardware requires it.
ENV PYOPENGL_PLATFORM=glx \
    HSA_ENABLE_SDMA=0

# --- Build-time sanity check -------------------------------------------------
RUN python -c "import torch, torchvision, torchaudio; \
print('torch', torch.__version__, 'hip', torch.version.hip); \
assert torch.version.hip is not None, 'torch is not a ROCm build!'" \
 && python -c "import genesis; print('genesis', genesis.__version__)" \
 && python -m unittest discover -s tests

CMD ["/bin/bash"]
