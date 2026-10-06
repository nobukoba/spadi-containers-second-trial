#!/bin/bash
set -euo pipefail

: "${SPADI_ROOT:=/opt/spadi}"
: "${SPADI_LOCAL:=/workspace/spadi}"

mkdir -p "${SPADI_LOCAL}"/{bin,lib,lib64,include,share,src,build,scripts,rawdata}

copy_if_missing() {
    local source="$1"
    local destination="$2"
    local label="$3"
    if [[ -e "$destination" ]]; then printf 'kept:    %s\n' "$label"; return; fi
    [[ -e "$source" ]] || return
    mkdir -p "$(dirname "$destination")"
    cp -a "$source" "$destination"
    printf 'copied:  %s\n' "$label"
}

copy_tree_missing() {
    local source_root="$1" destination_root="$2" label_root="$3"
    [[ -d "$source_root" ]] || return
    mkdir -p "$destination_root"
    while IFS= read -r -d '' source; do
        local relative="${source#"${source_root}/"}"
        local destination="${destination_root}/${relative}"
        if [[ -d "$source" ]]; then mkdir -p "$destination"
        else copy_if_missing "$source" "$destination" "${label_root}/${relative}"; fi
    done < <(find "$source_root" -mindepth 1 -print0)
}

if [[ -d "${SPADI_ROOT}/src" ]]; then
    shopt -s nullglob
    for source in "${SPADI_ROOT}/src"/*; do
        name="$(basename "$source")"
        copy_if_missing "$source" "${SPADI_LOCAL}/src/$name" "src/$name"
    done
    shopt -u nullglob
fi

for script in "${SPADI_ROOT}/scripts/"*-build.sh "${SPADI_ROOT}/scripts/"*-clone-latest.sh; do
    [[ -e "$script" ]] || continue
    name="$(basename "$script")"
    copy_if_missing "$script" "${SPADI_LOCAL}/scripts/$name" "scripts/$name"
done

for component in nestdaq fee artemis; do
    copy_tree_missing "${SPADI_ROOT}/scripts/${component}" "${SPADI_LOCAL}/scripts/${component}" "scripts/${component}"
done

printf '\nSPADI local workspace: %s\n' "${SPADI_LOCAL}"
printf 'Existing files are never overwritten.\n'
