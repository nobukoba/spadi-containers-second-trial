#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
bash "${HERE}/fee-setup.sh"
exec bash "${HERE}/initialize.sh"
