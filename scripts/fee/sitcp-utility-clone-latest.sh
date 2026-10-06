#!/bin/bash
set -euo pipefail
: "${SPADI_LOCAL:=/workspace/spadi}"
dst="${SPADI_LOCAL}/src/sitcp-sitcpxg-mpc-mpcx-ip-utility-first-trial"
if [[ -e "$dst" ]]; then
  echo "Refusing to overwrite existing $dst" >&2
  echo "Remove or rename it explicitly before cloning latest." >&2
  exit 1
fi
mkdir -p "${SPADI_LOCAL}/src"
git clone "https://github.com/nobukoba/sitcp-sitcpxg-mpc-mpcx-ip-utility-first-trial.git" "$dst"
