#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/../common/control-common.sh"
nestdaq_load_config "${HERE}/config.sh"
if ! tmux -L "$TMUX_SOCKET" has-session -t "$TMUX_SESSION" 2>/dev/null; then
    echo "Not running: $TMUX_SESSION"
    exit 0
fi
# Close the board connection first; keep downstream consumers running to drain.
for service in AmQStrTdcSampler STFBuilder TimeFrameBuilder FileSink; do
    nestdaq_stop_service "$service"
    sleep 1
done
# STOP -> READY waits for FileSink's PostRun trailer and close before cleanup.
nestdaq_change_state quit AmQStrTdcSampler STFBuilder TimeFrameBuilder FileSink
deadline=$((SECONDS + CONTROL_TIMEOUT))
while (( SECONDS < deadline )); do
    remaining=false
    for service in AmQStrTdcSampler STFBuilder TimeFrameBuilder FileSink; do
        state="$(nestdaq_state "$service")"
        [[ -z "$state" || "${state^^}" == EXITING ]] || remaining=true
    done
    if ! "$remaining"; then
        tmux -L "$TMUX_SOCKET" kill-session -t "$TMUX_SESSION"
        echo "Stopped: $TMUX_SESSION. Files saved under $RAWDATA_DIR/00"
        exit 0
    fi
    sleep 0.2
done
echo 'Shutdown timed out; tmux retained for inspection.' >&2
exit 1
