#!/usr/bin/env bash
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
data="${1:-${SPADI_LOCAL:-/workspace/spadi}/rawdata/raris_ac_lgad_202603}"
scratch="$(mktemp -d)"; trap 'rm -r -- "$scratch"' EXIT
# A runtime ACLiC regression would invoke a compiler and fail this test.
mkdir "$scratch/no-compiler"
for name in cc c++ gcc g++ clang clang++; do
  printf '#!/bin/sh\necho "unexpected compiler invocation" >&2\nexit 99\n' > "$scratch/no-compiler/$name"
  chmod +x "$scratch/no-compiler/$name"
done
PATH="$scratch/no-compiler:$PATH" "$here/run.sh" offline "$scratch/offline.root" "$data"
export RARIS_OUTPUT="$scratch/offline.root"
root -l -b -q "$here/test-actual.C"
if [[ $# -ge 2 ]]; then "$here/compare.sh" "$scratch/offline.root" "$2"; fi
