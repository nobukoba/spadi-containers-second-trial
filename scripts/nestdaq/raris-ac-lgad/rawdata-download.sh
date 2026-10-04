#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"; source "${HERE}/config.sh"
mkdir -p "${RAWDATA_DIR}"
echo "Dataset:     ${CONFIG_NAME}"; echo "Destination: ${RAWDATA_DIR}"
for entry in "${RAWDATA_FILES[@]}"; do IFS='|' read -r relative url sha <<< "$entry"; download-public-data.sh "${RAWDATA_DIR}" "$relative" "$url" "$sha"; done
