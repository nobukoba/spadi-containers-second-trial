#!/bin/bash
set -euo pipefail
: "${SPADI_ROOT:=/opt/spadi}"
: "${SPADI_LOCAL:=/workspace/spadi}"
: "${NPROC:=4}"

src="${SPADI_LOCAL}/src/nestdaq-user-impl"
build="${SPADI_LOCAL}/build/nestdaq-user-impl"
uhbook="${SPADI_LOCAL}/src/uhbook"

[[ -d "$src" ]] || { echo "Missing $src. Run spadi_prepare_local.sh first." >&2; exit 1; }
[[ -d "$uhbook" ]] || uhbook="${SPADI_ROOT}/src/uhbook"

cmake -S "$src" -B "$build" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="${SPADI_LOCAL}" \
  -DCMAKE_INSTALL_LIBDIR=lib \
  -DCMAKE_PREFIX_PATH="${SPADI_LOCAL};${SPADI_ROOT};${uhbook}" \
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
  -DCMAKE_CXX_STANDARD=17
cmake --build "$build" -j"${NPROC}" --verbose
cmake --install "$build"
