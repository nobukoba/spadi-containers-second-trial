#!/usr/bin/env bash
set -euo pipefail
[[ $# == 2 ]] || { echo "Usage: $0 OFFLINE.root ONLINE.root" >&2; exit 2; }
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export RARIS_OFFLINE="$1" RARIS_ONLINE="$2"
root -l -b -q "$here/compare.C"
