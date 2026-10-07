#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/../common/control-common.sh"
nestdaq_load_config "${HERE}/config.sh"
printf 'Config: %s\nAMANEQ: %s (channel 102)\nInitial run: %s\nOutput: %s/00\n' "$CONFIG_NAME" "$AMANEQ_IP" "$RUN_NUMBER" "$RAWDATA_DIR"
if tmux -L "$TMUX_SOCKET" has-session -t "$TMUX_SESSION" 2>/dev/null; then
    tmux -L "$TMUX_SOCKET" list-windows -t "$TMUX_SESSION"
else
    echo 'tmux: STOPPED'
fi
if nestdaq_cli -h "$VALKEY_HOST" -p "$VALKEY_PORT" ping >/dev/null 2>&1; then
    next_run="$(nestdaq_cli --raw -h "$VALKEY_HOST" -p "$VALKEY_PORT" -n "$DAQSERVICE_DB" get run_info:run_number)"
    printf 'Browser next run: %s\nWeb control: http://localhost:%s/daq-webctl.html\n' "$next_run" "$WEBCTL_PORT"
    for service in AmQStrTdcSampler STFBuilder TimeFrameBuilder FileSink; do
        state="$(nestdaq_state "$service")"
        printf '%-20s %s\n' "$service" "${state:-NOT REGISTERED}"
    done
else
    echo 'Valkey: STOPPED'
fi
