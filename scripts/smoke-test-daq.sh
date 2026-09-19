#!/usr/bin/env bash
set -euo pipefail


# Version metadata must be self-describing in Docker and SIF images.
test -x /opt/spadi/scripts/spadi-version.sh
test -r /opt/spadi/versions/versions.env
test -r /opt/spadi/versions/container.env
version_output="$(/opt/spadi/scripts/spadi-version.sh)"
grep -q '^SPADI container version : ' <<<"$version_output"
grep -q '^Git commit              : ' <<<"$version_output"
grep -q '^Image target            : ' <<<"$version_output"
grep -q '^NESTDAQ_REF=' /opt/spadi/versions/versions.env
grep -q '^ROOT_VERSION=' /opt/spadi/versions/versions.env
grep -q '^ARTEMIS_REF=' /opt/spadi/versions/versions.env
kind="${1:-${SPADI_IMAGE_KIND:-}}"
if [[ "$kind" != "user" && "$kind" != "devel" ]]; then
  echo "usage: smoke-test-daq.sh {user|devel}" >&2
  exit 2
fi

assert_command_absent() {
  local cmd="$1"
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "ERROR: unexpected command in runtime image: $cmd ($(command -v "$cmd"))" >&2
    return 1
  fi
}

contains_path_entry() {
  local value="$1"
  local expected="$2"
  case ":${value}:" in
    *":${expected}:"*) return 0 ;;
    *) return 1 ;;
  esac
}

echo "=== SPADI environment ==="
test "${SPADI_ROOT:-}" = "/opt/spadi"
test "${EXP_CONFIG_ROOT:-}" = "/opt/spadi/scripts/exp-config"
test -d /workspace
contains_path_entry "$PATH" "/opt/spadi/bin"
contains_path_entry "${LD_LIBRARY_PATH:-}" "/opt/spadi/lib"
contains_path_entry "${LD_LIBRARY_PATH:-}" "/opt/spadi/lib64"
contains_path_entry "${CMAKE_PREFIX_PATH:-}" "/opt/spadi"

for value in "$PATH" "${LD_LIBRARY_PATH:-}" "${CMAKE_PREFIX_PATH:-}" "${PKG_CONFIG_PATH:-}" "${ROOTSYS:-}" "${PYTHONPATH:-}"; do
  if [[ "$value" == *spadi-host-sentinel* ]]; then
    echo "ERROR: host software environment leaked into container: $value" >&2
    exit 1
  fi
done

echo "=== FEE layer ==="
command -v openFPGALoader
command -v mpc-mpcx-ip-writer
command -v sitcp-sitcpxg-ip-reader

echo "=== DAQ commands and files ==="
command -v daq-webctl
command -v TimeFrameBuilder
command -v STFBFilePlayer
command -v valkey-server
command -v valkey-cli
command -v tmux
test -r /opt/spadi/lib/redistimeseries.so
test -d /opt/spadi/scripts/exp-config

echo "=== Shared libraries ==="
for exe in /opt/spadi/bin/daq-webctl /opt/spadi/bin/TimeFrameBuilder /opt/spadi/bin/STFBFilePlayer; do
  test -x "$exe"
  ldd "$exe" | (! grep -q 'not found')
done

echo "=== CPU compatibility ==="
for exe in /opt/spadi/bin/daq-webctl /opt/spadi/bin/TimeFrameBuilder /opt/spadi/bin/STFBFilePlayer; do
  objdump -d "$exe" > /tmp/spadi-smoke.dis
  if grep -Eq 'vzeroupper|ymm[0-9]+|zmm[0-9]+|vmovdqu' /tmp/spadi-smoke.dis; then
    echo "ERROR: AVX instructions found in $exe" >&2
    exit 1
  fi
done
rm -f /tmp/spadi-smoke.dis

if [[ "$kind" == "user" ]]; then
  echo "=== User image policy ==="
  assert_command_absent gcc
  assert_command_absent g++
  assert_command_absent cmake
  assert_command_absent make
  assert_command_absent git
  test ! -d /opt/spadi/src
  test ! -d /opt/spadi/include
else
  echo "=== Development image policy ==="
  command -v gcc
  command -v g++
  command -v cmake
  command -v make
  command -v git
  test -d /opt/spadi/src/nestdaq
  test -d /opt/spadi/src/nestdaq-user-impl
  test -d /opt/spadi/src/libzmq
  test -d /opt/spadi/include
  if grep -R --line-number -- '-march=native' /opt/spadi/src/nestdaq/cmake /opt/spadi/src/nestdaq/CMakeLists.txt /opt/spadi/src/nestdaq-user-impl/CMakeLists.txt; then
    echo "ERROR: -march=native remains in DAQ development sources" >&2
    exit 1
  fi
fi

echo "DAQ ${kind} container check passed."
