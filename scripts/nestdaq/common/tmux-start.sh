#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/config-common.sh"; config="${1:-${NESTDAQ_CONFIG:-}}"; nestdaq_load_config "$config"
: "${TMUX_SESSION:?}"; : "${STF_PLAYERS:?}"; : "${TF_BUILDERS:?}"; : "${WEBCTL_HOST:=0.0.0.0}"; : "${WEBCTL_PORT:=8080}"
TMUX=(tmux -L "${TMUX_SOCKET}")
"${TMUX[@]}" has-session -t "${TMUX_SESSION}" 2>/dev/null && { echo "tmux session already exists: ${TMUX_SESSION}" >&2; exit 1; }
"${TMUX[@]}" new-session -d -s "${TMUX_SESSION}" -n control "exec bash"
"${TMUX[@]}" set-window-option -g -t "${TMUX_SESSION}" remain-on-exit on
"${TMUX[@]}" set-option -t "${TMUX_SESSION}" allow-rename off
"${TMUX[@]}" bind-key x kill-pane
"${TMUX[@]}" new-window -t "${TMUX_SESSION}" -n webctl "exec daq-webctl --http-uri http://${WEBCTL_HOST}:${WEBCTL_PORT}"
for ((i=0;i<STF_PLAYERS;i++)); do "${TMUX[@]}" new-window -t "${TMUX_SESSION}" -n "STF${i}" "NESTDAQ_CONFIG='$config' keep-device-window.sh 'STFBFilePlayer-${i}' start-device.sh STFBFilePlayer"; sleep 0.2; done
for ((i=0;i<TF_BUILDERS;i++)); do "${TMUX[@]}" new-window -t "${TMUX_SESSION}" -n "TFB${i}" "NESTDAQ_CONFIG='$config' keep-device-window.sh 'TimeFrameBuilder-${i}' start-device.sh TimeFrameBuilder"; sleep 0.2; done
echo "Started tmux session: ${TMUX_SESSION}"; "${TMUX[@]}" list-windows -t "${TMUX_SESSION}"
