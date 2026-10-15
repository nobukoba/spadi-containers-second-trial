#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/config-common.sh"; nestdaq_load_config "${1:-${NESTDAQ_CONFIG:-}}"
RTS_MODULE="${REDISTIMESERIES_MODULE:-${SPADI_ROOT}/lib/redistimeseries.so}"
PIDFILE="/tmp/spadi-redis-${REDIS_PORT}.pid"; LOGFILE="/tmp/spadi-redis-${REDIS_PORT}.log"
if ! nestdaq_cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" ping >/dev/null 2>&1; then
  [[ -r "$RTS_MODULE" ]] || { echo "RedisTimeSeries module not found: $RTS_MODULE" >&2; exit 1; }
  redis-server --bind "${REDIS_HOST}" --port "${REDIS_PORT}" --loadmodule "$RTS_MODULE" --daemonize yes --pidfile "$PIDFILE" --logfile "$LOGFILE" --dir /tmp
  for _ in $(seq 1 50); do nestdaq_cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" ping >/dev/null 2>&1 && break; sleep 0.1; done
fi
nestdaq_cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" ping >/dev/null
# Do not silently reuse an old Valkey or a different Redis server on this port.
expected_version="$(sed -n 's/^REDIS_VERSION=//p' "${SPADI_ROOT}/versions/versions.env")"
[[ -n "$expected_version" ]] || { echo "Pinned Redis version is missing." >&2; exit 1; }
actual_version="$(nestdaq_cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" INFO server | tr -d '\r' | sed -n 's/^redis_version://p')"
[[ "$actual_version" == "$expected_version" ]] || {
  echo "Expected Redis ${expected_version}, found ${actual_version:-unknown} at ${REDIS_HOST}:${REDIS_PORT}. Stop the old service or choose another port." >&2
  exit 1
}
nestdaq_cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" COMMAND INFO TS.ADD | grep -qi 'ts.add' || { echo "RedisTimeSeries TS.ADD is unavailable." >&2; exit 1; }
echo "Redis ready at ${REDIS_HOST}:${REDIS_PORT}"
