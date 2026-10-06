#!/bin/bash
set -euo pipefail
printf 'SPADI_ROOT  = %s\n' "${SPADI_ROOT:-}"
printf 'SPADI_LOCAL = %s\n\n' "${SPADI_LOCAL:-}"
for name in PATH LD_LIBRARY_PATH CMAKE_PREFIX_PATH PKG_CONFIG_PATH; do
    printf '%s\n' "$name"
    value="${!name:-}"
    if [[ -z "$value" ]]; then
        echo "  (empty)"
    else
        tr ':' '\n' <<< "$value" | sed 's/^/  /'
    fi
    echo
done
