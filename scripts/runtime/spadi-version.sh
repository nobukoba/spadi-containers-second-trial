#!/bin/bash
set -euo pipefail

metadata="${SPADI_ROOT:-/opt/spadi}/versions/container.env"
components="${SPADI_ROOT:-/opt/spadi}/versions/versions.env"

if [[ -f "$metadata" ]]; then
  source "$metadata"
fi

printf 'SPADI container version : %s\n' "${SPADI_CONTAINER_VERSION:-unknown}"
printf 'Git commit              : %s\n' "${SPADI_GIT_COMMIT:-unknown}"
printf 'Image target            : %s\n' "${SPADI_IMAGE_TARGET:-unknown}"
echo
echo "Components"
if [[ -f "$components" ]]; then
  cat "$components"
else
  echo "version manifest not found: $components" >&2
  exit 1
fi
