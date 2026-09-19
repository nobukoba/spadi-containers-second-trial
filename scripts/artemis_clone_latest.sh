#!/bin/bash
set -euo pipefail
: "${SPADI_LOCAL:=/workspace/spadi}"
dst="${SPADI_LOCAL}/src/artemis"
[[ ! -e "$dst" ]] || { echo "Refusing to overwrite existing $dst" >&2; exit 1; }
mkdir -p "${SPADI_LOCAL}/src"
git clone https://github.com/artemis-dev/artemis.git "$dst"
