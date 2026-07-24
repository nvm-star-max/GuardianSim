#!/usr/bin/env bash
set -euo pipefail

# System packages required by the AMD reference Dockerfile for headless Genesis
# rendering and video export. Run once per fresh container image.

if command -v sudo >/dev/null 2>&1; then
  apt_prefix=(sudo)
elif [[ "$(id -u)" -eq 0 ]]; then
  apt_prefix=()
else
  echo "ERROR: system package installation requires root or sudo." >&2
  exit 1
fi

"${apt_prefix[@]}" apt-get update
"${apt_prefix[@]}" apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  ffmpeg \
  git \
  libegl1 \
  libgl1 \
  libgles2 \
  libglib2.0-0 \
  libglu1-mesa \
  libglvnd0 \
  libosmesa6 \
  libsm6 \
  libvulkan1 \
  libx11-6 \
  libxcursor1 \
  libxext6 \
  libxfixes3 \
  libxi6 \
  libxinerama1 \
  libxrandr2 \
  libxrender1 \
  mesa-vulkan-drivers \
  vulkan-tools \
  wget \
  xvfb

"${apt_prefix[@]}" rm -rf /var/lib/apt/lists/*
