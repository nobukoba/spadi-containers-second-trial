#!/usr/bin/env bash
# Remove this recipe's tmux session after browser End; never kill live devices.
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/../common/control-common.sh"
nestdaq_load_config "${HERE}/config.sh"
if ! tmux -L "$TMUX_SOCKET" has-session -t "$TMUX_SESSION" 2>/dev/null; then
    echo "Session already closed: $TMUX_SESSION"
    exit 0
fi
deadline=$((SECONDS + CONTROL_TIMEOUT))
while (( SECONDS < deadline )); do
    finished=true
    for service in AmQStrTdcSampler STFBuilder TimeFrameBuilder FileSink; do
        state="$(nestdaq_state "$service")"
        [[ -z "$state" || "${state^^}" == EXITING ]] || finished=false
    done
    if "$finished"; then
        tmux -L "$TMUX_SOCKET" kill-session -t "$TMUX_SESSION"
        echo "Closed tmux session: $TMUX_SESSION. Valkey remains available."
        exit 0
    fi
    sleep 0.2
done
echo 'Devices have not exited. Use browser Stop / End; tmux retained for inspection.' >&2
exit 1
