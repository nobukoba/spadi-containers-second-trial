#!/bin/bash
set -euo pipefail
: "${SPADI_LOCAL:=/workspace/spadi}"
: "${NPROC:=4}"
src="${SPADI_LOCAL}/src/sitcp-sitcpxg-mpc-mpcx-ip-utility-first-trial"
[[ -d "$src" ]] || { echo "Missing $src. Run spadi-prepare-local.sh first." >&2; exit 1; }
make -C "$src" -j"${NPROC}" CXXFLAGS="-O2 -std=c++17 -Wall -Wextra -Wpedantic -march=x86-64 -mtune=generic"
make -C "$src" PREFIX="${SPADI_LOCAL}" install
