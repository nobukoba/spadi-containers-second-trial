#!/bin/bash
set -euo pipefail

: "${SPADI_ROOT:=/opt/spadi}"
: "${SPADI_LOCAL:=/workspace/spadi}"

mkdir -p "${SPADI_LOCAL}"/{bin,lib,include,share,src,build,scripts}

copy_if_missing() {
    local source="$1"
    local destination="$2"
    local label="$3"

    if [[ -e "$destination" ]]; then
        printf 'kept:    %s\n' "$label"
        return
    fi
    if [[ ! -e "$source" ]]; then
        return
    fi
    cp -a "$source" "$destination"
    printf 'copied:  %s\n' "$label"
}

if [[ -d "${SPADI_ROOT}/src" ]]; then
    shopt -s nullglob
    for source in "${SPADI_ROOT}/src"/*; do
        name="$(basename "$source")"
        copy_if_missing "$source" "${SPADI_LOCAL}/src/$name" "src/$name"
    done
    shopt -u nullglob
fi

for script in "${SPADI_ROOT}/scripts/"*_build.sh "${SPADI_ROOT}/scripts/"*_clone_latest.sh; do
    [[ -e "$script" ]] || continue
    name="$(basename "$script")"
    copy_if_missing "$script" "${SPADI_LOCAL}/scripts/$name" "scripts/$name"
done

printf '\nSPADI local workspace: %s\n' "${SPADI_LOCAL}"
printf 'Existing files are never overwritten.\n'
