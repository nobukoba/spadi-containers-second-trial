#!/usr/bin/env bash
# Exercise the pinned server and module without using an experiment's TCP port.
set -euo pipefail
source /opt/spadi/versions/versions.env
command -v redis-server
command -v redis-cli
redis-server --version | grep -F "v=${REDIS_VERSION} "
[[ "$(redis-cli --version)" == "redis-cli ${REDIS_VERSION}" ]]
if command -v valkey-server >/dev/null 2>&1 || command -v valkey-cli >/dev/null 2>&1; then
  echo 'ERROR: unexpected Valkey installation' >&2
  exit 1
fi
work="$(mktemp -d /tmp/spadi-redis-check.XXXXXX)"
server_pid=
cleanup() {
  if [[ -n "$server_pid" ]]; then
    kill "$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
  fi
  rm -rf "$work"
}
trap cleanup EXIT
redis-server --port 0 --unixsocket "$work/redis.sock" --unixsocketperm 700 \
  --save '' --appendonly no --daemonize no --dir "$work" \
  --loadmodule /opt/spadi/lib/redistimeseries.so >"$work/server.log" 2>&1 &
server_pid=$!
ready=false
for _ in $(seq 1 100); do
  if [[ "$(redis-cli -s "$work/redis.sock" ping 2>/dev/null || true)" == PONG ]]; then
    ready=true
    break
  fi
  kill -0 "$server_pid" 2>/dev/null || break
  sleep 0.1
done
if [[ "$ready" != true ]]; then
  cat "$work/server.log" >&2
  exit 1
fi
redis-cli -s "$work/redis.sock" INFO server | tr -d '\r' | grep -Fx "redis_version:${REDIS_VERSION}"
module_version="${REDISTIMESERIES_VERSION#v}"
IFS=. read -r major minor patch <<<"$module_version"
expected_module_version=$((major * 10000 + minor * 100 + patch))
actual_module_version="$(redis-cli --raw -s "$work/redis.sock" MODULE LIST | awk '$0 == "ver" {getline; print; exit}')"
[[ "$actual_module_version" == "$expected_module_version" ]]
[[ "$(redis-cli --raw -s "$work/redis.sock" TS.ADD spadi:smoke 1 42)" == 1 ]]
[[ "$(redis-cli --raw -s "$work/redis.sock" TS.RANGE spadi:smoke - +)" == $'1\n42' ]]
echo "Redis ${REDIS_VERSION} / RedisTimeSeries ${REDISTIMESERIES_VERSION} check passed."
