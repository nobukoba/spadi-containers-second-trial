#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export NESTDAQ_CONFIG="${HERE}/config.sh"
source "${HERE}/../common/control-common.sh"
nestdaq_load_config "$NESTDAQ_CONFIG"
[[ "$RUN_NUMBER" =~ ^[0-9]+$ ]] || { echo 'RUN_NUMBER must be a nonnegative integer.' >&2; exit 2; }
[[ "$SOURCE_MODE" == live && "$TF_BUILDERS" == 1 && "$FILE_SINKS" == 1 && "$TDC_TYPE" == 1 ]] || { echo 'This recipe requires one LR-TDC source, one TFB, and one FileSink.' >&2; exit 2; }
[[ "$MAX_HBF" =~ ^[1-9][0-9]*$ ]] || { echo 'MAX_HBF must be positive.' >&2; exit 2; }
for cmd in tmux AmQStrTdcSampler STFBuilder TimeFrameBuilder FileSink daq-webctl; do command -v "$cmd" >/dev/null; done
if tmux -L "$TMUX_SOCKET" has-session -t "$TMUX_SESSION" 2>/dev/null; then
    echo "Session already exists: $TMUX_SESSION. Use run-status.sh or run-stop.sh." >&2
    exit 1
fi
printf -v output '%s/00/run%06d.dat' "$RAWDATA_DIR" "$((10#$RUN_NUMBER))"
[[ ! -e "$output" ]] || { echo "Output already exists: $output. Change RUN_NUMBER." >&2; exit 1; }
bash "${HERE}/fee-setup.sh"
bash "${HERE}/../common/start-valkey.sh" "$NESTDAQ_CONFIG"
# This recipe owns its Valkey service/DBs. Refuse to clear a running registry.
active="$(nestdaq_cli --raw -h "$VALKEY_HOST" -p "$VALKEY_PORT" -n "$DAQSERVICE_DB" keys 'daq_service:*:fair-mq-state')"
[[ -z "$active" ]] || { echo 'DAQ devices already registered on this Valkey service; use another port.' >&2; exit 1; }
bash "${HERE}/../common/apply-parameters.sh" "$NESTDAQ_CONFIG"
bash "${HERE}/../common/apply-topology.sh" "$NESTDAQ_CONFIG"
nestdaq_cli -h "$VALKEY_HOST" -p "$VALKEY_PORT" -n "$DAQSERVICE_DB" set run_info:run_number "$((10#$RUN_NUMBER))" >/dev/null
bash "${HERE}/../common/tmux-start.sh" "$NESTDAQ_CONFIG"
devices=(AmQStrTdcSampler STFBuilder TimeFrameBuilder FileSink)
nestdaq_wait_state IDLE "${devices[@]}"
# Allow the state-control subscribers to attach after device registration.
sleep 1
echo "NestDAQ prepared: all four devices are IDLE; acquisition has not started."
echo "Open http://localhost:${WEBCTL_PORT}/daq-webctl.html to initialize, Run, and Stop."
echo "Initial run number: $RUN_NUMBER. Choose later run numbers in the browser."
