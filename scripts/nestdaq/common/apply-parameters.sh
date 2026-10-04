#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/config-common.sh"; nestdaq_load_config "${1:-${NESTDAQ_CONFIG:-}}"
: "${STF_PLAYERS:?}"; : "${TF_BUILDERS:?}"; : "${RAWDATA_DIR:?}"; : "${RUN_FILE:?}"
: "${MAX_HBF:=4}"; : "${TFB_DECIMATION_FACTOR:=1000}"; : "${TFB_DISCARD_OUTPUT:=false}"; : "${TFB_ENABLE_UDS:=false}"
uri="redis://${VALKEY_HOST}:${VALKEY_PORT}/${PARAMETER_DB}"; nestdaq_cli -u "$uri" flushdb >/dev/null
param(){ nestdaq_cli -u "$uri" hset "parameters:$1" "${@:2}" >/dev/null; }
for ((i=0;i<STF_PLAYERS;i++)); do
  if declare -p STF_INPUT_FILES >/dev/null 2>&1 && [[ -n "${STF_INPUT_FILES[$i]:-}" ]]; then rel="${STF_INPUT_FILES[$i]}"; else printf -v subdir '%02d' "$i"; rel="${subdir}/${RUN_FILE}"; fi
  param "STFBFilePlayer-${i}" in-file "${RAWDATA_DIR}/${rel}"
  param "STFBuilder-${i}" max-hbf "${MAX_HBF}"
done
for ((i=0;i<TF_BUILDERS;i++)); do param "TimeFrameBuilder-${i}" decimation-factor "${TFB_DECIMATION_FACTOR}" discard-output "${TFB_DISCARD_OUTPUT}" enable-uds "${TFB_ENABLE_UDS}"; done
echo "Parameters loaded for ${STF_PLAYERS} STFBFilePlayer(s) and ${TF_BUILDERS} TimeFrameBuilder(s)."
