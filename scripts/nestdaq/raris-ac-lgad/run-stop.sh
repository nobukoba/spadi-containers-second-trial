#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"; source "${HERE}/config.sh"
TMUX=(tmux -L "${TMUX_SOCKET:-spadi}")
if "${TMUX[@]}" has-session -t "${TMUX_SESSION}" 2>/dev/null; then "${TMUX[@]}" kill-session -t "${TMUX_SESSION}"; echo "Stopped: ${TMUX_SESSION}"; else echo "Not running: ${TMUX_SESSION}"; fi
