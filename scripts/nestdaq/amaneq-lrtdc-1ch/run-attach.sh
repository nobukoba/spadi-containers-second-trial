#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/config.sh"
exec tmux -L "$TMUX_SOCKET" attach-session -t "$TMUX_SESSION"
