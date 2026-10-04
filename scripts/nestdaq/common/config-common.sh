#!/usr/bin/env bash
set -euo pipefail
nestdaq_load_config() {
  local config="${1:-${NESTDAQ_CONFIG:-}}"
  [[ -n "$config" && -r "$config" ]] || { echo "NestDAQ config not found: ${config:-<unset>}" >&2; return 2; }
  source "$config"
  : "${SPADI_ROOT:=/opt/spadi}"; : "${SPADI_LOCAL:=/workspace/spadi}"
  : "${VALKEY_HOST:=127.0.0.1}"; : "${VALKEY_PORT:=6379}"
  : "${DAQSERVICE_DB:=0}"; : "${METRICS_DB:=1}"; : "${PARAMETER_DB:=2}"
  : "${NESTDAQ_HOST_IP:=127.0.0.1}"; : "${TMUX_SOCKET:=spadi}"
}
nestdaq_cli() {
  if command -v valkey-cli >/dev/null 2>&1; then command valkey-cli "$@"
  elif command -v redis-cli >/dev/null 2>&1; then command redis-cli "$@"
  else echo "Neither valkey-cli nor redis-cli was found." >&2; return 127; fi
}
