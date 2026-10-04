#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"; source "${HERE}/config.sh"
TMUX=(tmux -L "${TMUX_SOCKET:-spadi}")
echo "Config:   ${CONFIG_NAME}"; echo "Raw data: ${RAWDATA_DIR}"; echo "STF:      ${STF_PLAYERS}"; echo "TFB:      ${TF_BUILDERS}"
if "${TMUX[@]}" has-session -t "${TMUX_SESSION}" 2>/dev/null; then echo "Run:      RUNNING (${TMUX_SESSION})"; "${TMUX[@]}" list-windows -t "${TMUX_SESSION}"; else echo "Run:      STOPPED"; fi
if command -v valkey-cli >/dev/null 2>&1 && valkey-cli -h "${VALKEY_HOST:-127.0.0.1}" -p "${VALKEY_PORT:-6379}" ping >/dev/null 2>&1; then echo "Valkey:   RUNNING"; else echo "Valkey:   STOPPED"; fi
