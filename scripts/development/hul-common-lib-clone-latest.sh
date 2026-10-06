#!/bin/bash
set -euo pipefail
: "${SPADI_LOCAL:=/workspace/spadi}"
dst="${SPADI_LOCAL}/src/hul-common-lib"
if [[ -e "$dst" ]]; then
  echo "Refusing to overwrite existing $dst" >&2
  echo "Remove or rename it explicitly before cloning latest." >&2
  exit 1
fi
mkdir -p "${SPADI_LOCAL}/src"
git clone "https://github.com/spadi-alliance/hul-common-lib.git" "$dst"
