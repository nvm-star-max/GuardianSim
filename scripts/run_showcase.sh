#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repository_root}/showcase"

if [[ ! -d node_modules ]]; then
  npm install
fi

npm run dev
