#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/config-common.sh"; config="${1:-${NESTDAQ_CONFIG:-}}"; nestdaq_load_config "$config"
: "${TMUX_SESSION:?}"; : "${TF_BUILDERS:?}"; : "${WEBCTL_HOST:=0.0.0.0}"; : "${WEBCTL_PORT:=8080}"
TMUX=(tmux -L "${TMUX_SOCKET}")
"${TMUX[@]}" has-session -t "${TMUX_SESSION}" 2>/dev/null && { echo "tmux session already exists: ${TMUX_SESSION}" >&2; exit 1; }
"${TMUX[@]}" new-session -d -s "${TMUX_SESSION}" -n control "exec bash"
"${TMUX[@]}" set-window-option -g -t "${TMUX_SESSION}" remain-on-exit on
"${TMUX[@]}" set-option -t "${TMUX_SESSION}" allow-rename off
"${TMUX[@]}" bind-key x kill-pane
"${TMUX[@]}" new-window -t "${TMUX_SESSION}" -n webctl "exec daq-webctl --http-uri http://${WEBCTL_HOST}:${WEBCTL_PORT} --redis-uri tcp://${VALKEY_HOST}:${VALKEY_PORT}/${DAQSERVICE_DB}"
launch_device() {
  local device="$1" index="$2" window="$3" command
  # Quote paths for tmux's shell, including workspaces containing spaces.
  printf -v command 'NESTDAQ_CONFIG=%q keep-device-window.sh %q start-device.sh %q --startup-state idle' "$config" "${device}-${index}" "$device"
  "${TMUX[@]}" new-window -t "${TMUX_SESSION}" -n "$window" "$command"
}
case "${SOURCE_MODE:-replay}" in
  replay)
    : "${STF_PLAYERS:?}"
    for ((i=0;i<STF_PLAYERS;i++)); do launch_device STFBFilePlayer "$i" "STF${i}"; done
    ;;
  live)
    launch_device AmQStrTdcSampler 0 sampler
    launch_device STFBuilder 0 STF0
    ;;
  *) echo "Unknown SOURCE_MODE: $SOURCE_MODE" >&2; exit 2 ;;
esac
for ((i=0;i<TF_BUILDERS;i++)); do launch_device TimeFrameBuilder "$i" "TFB${i}"; done
for ((i=0;i<${FILE_SINKS:-0};i++)); do launch_device FileSink "$i" "sink${i}"; done
echo "Started tmux session: ${TMUX_SESSION}"; "${TMUX[@]}" list-windows -t "${TMUX_SESSION}"
