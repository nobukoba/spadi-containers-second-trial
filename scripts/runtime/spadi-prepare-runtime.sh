#!/usr/bin/env bash
# Copy runtime recipes only; usable in user and development images.
set -euo pipefail
: "${SPADI_ROOT:=/opt/spadi}"
: "${SPADI_LOCAL:=/workspace/spadi}"
mkdir -p "${SPADI_LOCAL}/scripts" "${SPADI_LOCAL}/rawdata"
for component in fee nestdaq artemis; do
    source_root="${SPADI_ROOT}/scripts/${component}"
    [[ -d "$source_root" ]] || continue
    while IFS= read -r -d '' source_file; do
        relative="${source_file#"${SPADI_ROOT}/scripts/"}"
        destination="${SPADI_LOCAL}/scripts/${relative}"
        if [[ -d "$source_file" ]]; then
            mkdir -p "$destination"
        elif [[ ! -e "$destination" && ! -L "$destination" ]]; then
            mkdir -p "$(dirname "$destination")"
            cp -a "$source_file" "$destination"
            printf 'copied: %s\n' "$relative"
        fi
    done < <(find "$source_root" -mindepth 1 -print0)
done
printf 'Runtime recipes: %s/scripts (existing files kept)\n' "$SPADI_LOCAL"
