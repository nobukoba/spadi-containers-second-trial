#!/bin/bash
set -euo pipefail
: "${SPADI_ROOT:=/opt/spadi}"
: "${SPADI_LOCAL:=/workspace/spadi}"
: "${NPROC:=4}"
src="${SPADI_LOCAL}/src/openFPGALoader"
build="${SPADI_LOCAL}/build/openFPGALoader"
[[ -d "$src" ]] || { echo "Missing $src. Run spadi-prepare-local.sh first." >&2; exit 1; }
cmake -S "$src" -B "$build" -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="${SPADI_LOCAL}" -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_PREFIX_PATH="${SPADI_LOCAL};${SPADI_ROOT}" -DCMAKE_C_FLAGS_RELEASE="-O2 -DNDEBUG -march=x86-64 -mtune=generic" -DCMAKE_CXX_FLAGS_RELEASE="-O2 -DNDEBUG -march=x86-64 -mtune=generic"
cmake --build "$build" -j"${NPROC}"
cmake --install "$build"
