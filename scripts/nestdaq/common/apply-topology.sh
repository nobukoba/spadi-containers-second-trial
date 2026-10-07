#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/config-common.sh"; nestdaq_load_config "${1:-${NESTDAQ_CONFIG:-}}"
: "${STF_TO_TFB_HOST:=127.0.0.1}"; : "${STF_TO_TFB_PORT:=5500}"; : "${TFB_OUTPUT_HOST:=127.0.0.1}"; : "${TFB_OUTPUT_PORT:=5501}"
uri="redis://${VALKEY_HOST}:${VALKEY_PORT}/${DAQSERVICE_DB}"
endpoint(){ nestdaq_cli -u "$uri" hset "daq_service:topology:endpoint:$1:$2" "${@:3}" >/dev/null; }
link(){ nestdaq_cli -u "$uri" set "daq_service:topology:link:$1:$2,$3:$4" none >/dev/null; }
keys="$(nestdaq_cli -u "$uri" keys 'daq_service:*' || true)"; [[ -z "$keys" ]] || nestdaq_cli -u "$uri" del $keys >/dev/null
case "${SOURCE_MODE:-replay}" in
  replay)
    endpoint STFBFilePlayer out type push method connect autoSubChannel true
    link STFBFilePlayer out TimeFrameBuilder in
    ;;
  live)
    : "${SAMPLER_OUTPUT_HOST:?}"; : "${SAMPLER_OUTPUT_PORT:?}"
    endpoint AmQStrTdcSampler out type push method bind enable-uds false address "tcp://${SAMPLER_OUTPUT_HOST}:${SAMPLER_OUTPUT_PORT}"
    endpoint STFBuilder in type pull method connect enable-uds false
    endpoint STFBuilder out type push method connect autoSubChannel true enable-uds false
    link AmQStrTdcSampler out STFBuilder in
    link STFBuilder out TimeFrameBuilder in
    ;;
  *) echo "Unknown SOURCE_MODE: $SOURCE_MODE" >&2; exit 2 ;;
esac
endpoint TimeFrameBuilder in type pull method bind enable-uds false address "tcp://${STF_TO_TFB_HOST}:${STF_TO_TFB_PORT}"
endpoint TimeFrameBuilder out type push method bind enable-uds false address "tcp://${TFB_OUTPUT_HOST}:${TFB_OUTPUT_PORT}"
if (( ${FILE_SINKS:-0} > 0 )); then
  endpoint FileSink in type pull method connect autoSubChannel true enable-uds false
  link TimeFrameBuilder out FileSink in
  if [[ "${SOURCE_MODE:-replay}" == live ]]; then
    # Pinned FileSink requires a DQM channel even without a monitor subscriber.
    endpoint FileSink dqm type pub method bind waitForPeerConnection false enable-uds false address "tcp://${TFB_OUTPUT_HOST}:${FILE_SINK_DQM_PORT:-5602}"
  fi
fi
echo "Topology source: ${SOURCE_MODE:-replay}; TFB x${TF_BUILDERS}; FileSink x${FILE_SINKS:-0}"
echo "  STF -> TFB: tcp://${STF_TO_TFB_HOST}:${STF_TO_TFB_PORT}"
echo "  TFB output: tcp://${TFB_OUTPUT_HOST}:${TFB_OUTPUT_PORT}"
