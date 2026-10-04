#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/config-common.sh"; nestdaq_load_config "${1:-${NESTDAQ_CONFIG:-}}"
RTS_MODULE="${REDISTIMESERIES_MODULE:-${SPADI_ROOT}/lib/redistimeseries.so}"
PIDFILE="/tmp/spadi-valkey-${VALKEY_PORT}.pid"; LOGFILE="/tmp/spadi-valkey-${VALKEY_PORT}.log"
if ! nestdaq_cli -h "${VALKEY_HOST}" -p "${VALKEY_PORT}" ping >/dev/null 2>&1; then
  [[ -r "$RTS_MODULE" ]] || { echo "RedisTimeSeries module not found: $RTS_MODULE" >&2; exit 1; }
  valkey-server --bind "${VALKEY_HOST}" --port "${VALKEY_PORT}" --loadmodule "$RTS_MODULE" --daemonize yes --pidfile "$PIDFILE" --logfile "$LOGFILE" --dir /tmp
  for _ in $(seq 1 50); do nestdaq_cli -h "${VALKEY_HOST}" -p "${VALKEY_PORT}" ping >/dev/null 2>&1 && break; sleep 0.1; done
fi
nestdaq_cli -h "${VALKEY_HOST}" -p "${VALKEY_PORT}" ping >/dev/null
nestdaq_cli -h "${VALKEY_HOST}" -p "${VALKEY_PORT}" COMMAND INFO TS.ADD | grep -qi 'ts.add' || { echo "RedisTimeSeries TS.ADD is unavailable." >&2; exit 1; }
echo "Valkey ready at ${VALKEY_HOST}:${VALKEY_PORT}"
