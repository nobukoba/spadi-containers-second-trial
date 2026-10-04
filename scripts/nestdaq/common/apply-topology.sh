#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/config-common.sh"; nestdaq_load_config "${1:-${NESTDAQ_CONFIG:-}}"
: "${STF_TO_TFB_HOST:=127.0.0.1}"; : "${STF_TO_TFB_PORT:=5500}"; : "${TFB_OUTPUT_HOST:=127.0.0.1}"; : "${TFB_OUTPUT_PORT:=5501}"
uri="redis://${VALKEY_HOST}:${VALKEY_PORT}/${DAQSERVICE_DB}"
endpoint(){ nestdaq_cli -u "$uri" hset "daq_service:topology:endpoint:$1:$2" "${@:3}" >/dev/null; }
link(){ nestdaq_cli -u "$uri" set "daq_service:topology:link:$1:$2,$3:$4" none >/dev/null; }
keys="$(nestdaq_cli -u "$uri" keys 'daq_service:*' || true)"; [[ -z "$keys" ]] || nestdaq_cli -u "$uri" del $keys >/dev/null
endpoint STFBFilePlayer out type push method connect autoSubChannel true
endpoint TimeFrameBuilder in type pull method bind enable-uds false address "tcp://${STF_TO_TFB_HOST}:${STF_TO_TFB_PORT}"
endpoint TimeFrameBuilder out type push method bind enable-uds false address "tcp://${TFB_OUTPUT_HOST}:${TFB_OUTPUT_PORT}"
link STFBFilePlayer out TimeFrameBuilder in
echo "Topology: STFBFilePlayer x${STF_PLAYERS} -> TimeFrameBuilder x${TF_BUILDERS}"
echo "  STF -> TFB: tcp://${STF_TO_TFB_HOST}:${STF_TO_TFB_PORT}"
echo "  TFB output: tcp://${TFB_OUTPUT_HOST}:${TFB_OUTPUT_PORT}"
