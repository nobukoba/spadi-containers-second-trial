#!/usr/bin/env bash
# NestDAQ v1.0.0 daqctl payload and registry state names.
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/config-common.sh"

nestdaq_state() {
    local service="$1" index="${2:-0}"
    nestdaq_cli --raw -h "$VALKEY_HOST" -p "$VALKEY_PORT" -n "$DAQSERVICE_DB" get "daq_service:${service}:${service}-${index}:fair-mq-state"
}

nestdaq_wait_state() {
    local expected="$1"; shift
    local deadline=$((SECONDS + ${CONTROL_TIMEOUT:-30})) service state ready
    while (( SECONDS < deadline )); do
        ready=true
        for service in "$@"; do
            state="$(nestdaq_state "$service")"
            # FairMQ 1.4.55 reports "DEVICE READY", with an embedded space.
            state="${state//[ _-]/}"
            [[ "${state^^}" != ERROR ]] || { echo "${service}: ERROR; inspect run-attach.sh" >&2; return 1; }
            [[ "${state^^}" == "${expected^^}" ]] || ready=false
        done
        if "$ready"; then return 0; fi
        sleep 0.2
    done
    echo "Timed out waiting for $expected: $*; tmux retained for inspection." >&2
    return 1
}

nestdaq_change_state() {
    local transition="$1"; shift
    local services='' service
    for service in "$@"; do services+="${services:+,}\"${service}\""; done
    nestdaq_cli -h "$VALKEY_HOST" -p "$VALKEY_PORT" -n "$DAQSERVICE_DB" publish daqctl \
        "{\"command\":\"change_state\",\"value\":\"${transition}\",\"services\":[${services}],\"instances\":[\"all\"]}" >/dev/null
}

nestdaq_stop_service() {
    local service="$1" state
    state="$(nestdaq_state "$service")"
    state="${state//[ _-]/}"
    if [[ "${state^^}" == RUNNING ]]; then
        nestdaq_change_state STOP "$service"
        nestdaq_wait_state READY "$service"
    elif [[ "${state^^}" != READY && "${state^^}" != IDLE && "${state^^}" != DEVICEREADY ]]; then
        echo "Cannot safely stop ${service} in state ${state}; inspect run-attach.sh." >&2
        return 1
    fi
}
