#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/config-common.sh"; nestdaq_load_config "${1:-${NESTDAQ_CONFIG:-}}"
: "${TF_BUILDERS:?}"
: "${MAX_HBF:=4}"; : "${TFB_DECIMATION_FACTOR:=1000}"; : "${TFB_DISCARD_OUTPUT:=false}"; : "${TFB_ENABLE_UDS:=false}"
uri="redis://${VALKEY_HOST}:${VALKEY_PORT}/${PARAMETER_DB}"; nestdaq_cli -u "$uri" flushdb >/dev/null
param(){ nestdaq_cli -u "$uri" hset "parameters:$1" "${@:2}" >/dev/null; }
case "${SOURCE_MODE:-replay}" in
  replay)
    : "${STF_PLAYERS:?}"; : "${RAWDATA_DIR:?}"; : "${RUN_FILE:?}"
    for ((i=0;i<STF_PLAYERS;i++)); do
      if declare -p STF_INPUT_FILES >/dev/null 2>&1 && [[ -n "${STF_INPUT_FILES[$i]:-}" ]]; then rel="${STF_INPUT_FILES[$i]}"; else printf -v subdir '%02d' "$i"; rel="${subdir}/${RUN_FILE}"; fi
      param "STFBFilePlayer-${i}" in-file "${RAWDATA_DIR}/${rel}"
      param "STFBuilder-${i}" max-hbf "${MAX_HBF}"
    done
    ;;
  live)
    : "${AMANEQ_IP:?}"; : "${TDC_TYPE:?}"
    # The pinned sampler reads these exact case-sensitive parameter names.
    param AmQStrTdcSampler-0 msiTcpIp "$AMANEQ_IP" TdcType "$TDC_TYPE" enable-uds false
    param STFBuilder-0 max-hbf "$MAX_HBF" discard-output false enable-uds false
    ;;
  *) echo "Unknown SOURCE_MODE: $SOURCE_MODE" >&2; exit 2 ;;
esac
for ((i=0;i<TF_BUILDERS;i++)); do param "TimeFrameBuilder-${i}" decimation-factor "${TFB_DECIMATION_FACTOR}" discard-output "${TFB_DISCARD_OUTPUT}" enable-uds "${TFB_ENABLE_UDS}"; done
if (( ${FILE_SINKS:-0} > 0 )); then
  : "${RAWDATA_DIR:?}"
  for ((i=0;i<FILE_SINKS;i++)); do
    printf -v subdir '%02d' "$i"
    mkdir -p "${RAWDATA_DIR}/${subdir}"
    param "FileSink-${i}" multipart true merge-message true prefix "${RAWDATA_DIR}/${subdir}" openmode create file-extension .dat enable-uds false
  done
fi
echo "Parameters loaded: ${SOURCE_MODE:-replay}, ${TF_BUILDERS} TimeFrameBuilder(s), ${FILE_SINKS:-0} FileSink(s)."
