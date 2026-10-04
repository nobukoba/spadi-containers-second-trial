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

for path in     "${SPADI_ROOT}/scripts/nestdaq/common"     "${SPADI_ROOT}/scripts/nestdaq"     "${SPADI_ROOT}/scripts/fee"     "${SPADI_ROOT}/scripts/artemis"     "${SPADI_ROOT}/scripts"     "${SPADI_ROOT}/bin"     "${SPADI_LOCAL}/scripts/nestdaq/common"     "${SPADI_LOCAL}/scripts/nestdaq"     "${SPADI_LOCAL}/scripts/fee"     "${SPADI_LOCAL}/scripts/artemis"     "${SPADI_LOCAL}/scripts"     "${SPADI_LOCAL}/bin"; do
    _spadi_prepend_path PATH "$path"
done

_spadi_prepend_path LD_LIBRARY_PATH "${SPADI_ROOT}/lib64"
_spadi_prepend_path LD_LIBRARY_PATH "${SPADI_ROOT}/lib"
_spadi_prepend_path LD_LIBRARY_PATH "${SPADI_LOCAL}/lib64"
_spadi_prepend_path LD_LIBRARY_PATH "${SPADI_LOCAL}/lib"

_spadi_prepend_path CMAKE_PREFIX_PATH "${SPADI_ROOT}"
_spadi_prepend_path CMAKE_PREFIX_PATH "${SPADI_LOCAL}"

_spadi_prepend_path PKG_CONFIG_PATH "${SPADI_ROOT}/lib64/pkgconfig"
_spadi_prepend_path PKG_CONFIG_PATH "${SPADI_ROOT}/lib/pkgconfig"
_spadi_prepend_path PKG_CONFIG_PATH "${SPADI_LOCAL}/lib64/pkgconfig"
_spadi_prepend_path PKG_CONFIG_PATH "${SPADI_LOCAL}/lib/pkgconfig"

unset -f _spadi_prepend_path
