#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/config.sh"
TMUX=(tmux -L "$TMUX_SOCKET")
if "${TMUX[@]}" has-session -t "$TMUX_SESSION" 2>/dev/null; then
    echo 'Stop this NestDAQ session before applying FEE masks.' >&2
    exit 1
fi
fee="${SPADI_LOCAL:-/workspace/spadi}/scripts/fee/amaneq-lrtdc-1ch/setup.sh"
[[ -r "$fee" ]] || fee="${SPADI_ROOT:-/opt/spadi}/scripts/fee/amaneq-lrtdc-1ch/setup.sh"
exec bash "$fee" "$AMANEQ_IP"
