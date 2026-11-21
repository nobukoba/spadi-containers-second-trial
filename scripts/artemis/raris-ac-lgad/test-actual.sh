#!/usr/bin/env bash
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
data="${1:-${SPADI_LOCAL:-/workspace/spadi}/rawdata/raris_ac_lgad_202603}"
scratch="$(mktemp -d)"; trap 'rm -r -- "$scratch"' EXIT
"$here/run.sh" offline "$scratch/offline.root" "$data"
export RARIS_OUTPUT="$scratch/offline.root"
root -l -b -q "$here/test-actual.C"
if [[ $# -ge 2 ]]; then "$here/compare.sh" "$scratch/offline.root" "$2"; fi
