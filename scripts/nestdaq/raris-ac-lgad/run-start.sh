#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export NESTDAQ_CONFIG="${HERE}/config.sh"
source "${NESTDAQ_CONFIG}"
for ((i=0;i<STF_PLAYERS;i++)); do
  if declare -p STF_INPUT_FILES >/dev/null 2>&1 && [[ -n "${STF_INPUT_FILES[$i]:-}" ]]; then rel="${STF_INPUT_FILES[$i]}"; else printf -v subdir '%02d' "$i"; rel="${subdir}/${RUN_FILE}"; fi
  file="${RAWDATA_DIR}/${rel}"
  [[ -r "$file" ]] || { echo "Raw data not found: $file" >&2; echo "Run ./rawdata-download.sh first." >&2; exit 1; }
done
start-valkey.sh "${NESTDAQ_CONFIG}"
apply-parameters.sh "${NESTDAQ_CONFIG}"
apply-topology.sh "${NESTDAQ_CONFIG}"
tmux-start.sh "${NESTDAQ_CONFIG}"
echo; echo "Use ./run-attach.sh to view the tmux session."
