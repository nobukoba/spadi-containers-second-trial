#!/bin/bash
# SPADI environment setup.
# Source this file: source /opt/spadi/spadi-setup.sh

export SPADI_ROOT="${SPADI_ROOT:-/opt/spadi}"
export SPADI_LOCAL="${SPADI_LOCAL:-/workspace/spadi}"

_spadi_prepend_path() {
    local var_name="$1"
    local value="$2"
    local current="${!var_name:-}"
    case ":${current}:" in
        *":${value}:"*) ;;
        *) export "${var_name}=${value}${current:+:${current}}" ;;
    esac
}

_spadi_prepend_path PATH "${SPADI_ROOT}/bin"
_spadi_prepend_path PATH "${SPADI_ROOT}/scripts"
_spadi_prepend_path PATH "${SPADI_LOCAL}/bin"
_spadi_prepend_path PATH "${SPADI_LOCAL}/scripts"

_spadi_prepend_path LD_LIBRARY_PATH "${SPADI_ROOT}/lib"
_spadi_prepend_path LD_LIBRARY_PATH "${SPADI_LOCAL}/lib"

_spadi_prepend_path CMAKE_PREFIX_PATH "${SPADI_ROOT}"
_spadi_prepend_path CMAKE_PREFIX_PATH "${SPADI_LOCAL}"

_spadi_prepend_path PKG_CONFIG_PATH "${SPADI_ROOT}/lib/pkgconfig"
_spadi_prepend_path PKG_CONFIG_PATH "${SPADI_LOCAL}/lib/pkgconfig"

unset -f _spadi_prepend_path
