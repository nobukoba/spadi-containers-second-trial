#!/usr/bin/env bash
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
[[ $# -ge 2 && $# -le 3 ]] || { echo "Usage: $0 offline|online OUTPUT.root [data-directory|endpoint]" >&2; exit 2; }
mode="$1"; output="$(realpath -m "$2")"; arg="${3:-}"
case "$mode" in
  offline) arg="${arg:-${SPADI_LOCAL:-/workspace/spadi}/rawdata/raris_ac_lgad_202603}" ;;
  online) arg="${arg:-tcp://127.0.0.1:5501}" ;;
  *) echo "Expected offline or online" >&2; exit 2 ;;
esac
scratch="$(mktemp -d)"; trap 'rm -r -- "$scratch"' EXIT
cp "$here/RarisProcessor.C" "$scratch/RarisProcessor.C"
export RARIS_SOURCE="$scratch/RarisProcessor.C" RARIS_STEERING="$scratch/steering.yaml" RARIS_MODE="$mode" RARIS_ARG="$arg" RARIS_OUTPUT="$output"
python3 - <<'PY'
import json, os
p={'OutputFile':os.environ['RARIS_OUTPUT']}
if os.environ['RARIS_MODE']=='offline':
 from pathlib import Path
 root=Path(os.environ['RARIS_ARG']); p['InputFiles']=[str(root/f'{i:02}'/'run000020.dat') for i in range(3)]
else:
 p['Endpoint']=os.environ['RARIS_ARG']; p['TimeoutMs']=int(os.environ.get('RARIS_TIMEOUT_MS','30000'))
with open(os.environ['RARIS_STEERING'],'w') as f: json.dump({'Processor':[{'name':'analysis','type':'RarisProcessor','parameter':p}]}, f)
PY
artemis -l -b -q "$here/run.C"

root -l -b -q "$here/verify.C"
