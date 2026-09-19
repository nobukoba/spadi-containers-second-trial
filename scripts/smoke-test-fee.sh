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
  echo "usage: smoke-test-fee.sh {user|devel}" >&2
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
test -d /workspace
contains_path_entry "$PATH" "/opt/spadi/bin"
contains_path_entry "${LD_LIBRARY_PATH:-}" "/opt/spadi/lib"
contains_path_entry "${LD_LIBRARY_PATH:-}" "/opt/spadi/lib64"
contains_path_entry "${CMAKE_PREFIX_PATH:-}" "/opt/spadi"
contains_path_entry "${PKG_CONFIG_PATH:-}" "/opt/spadi/lib/pkgconfig"
contains_path_entry "${PKG_CONFIG_PATH:-}" "/opt/spadi/lib64/pkgconfig"

# The workflow deliberately contaminates host-side software environment
# variables before the Apptainer --cleanenv test. None of those sentinel paths
# may be visible inside the container. Apptainer's own runtime additions, such
# as /.singularity.d/libs, are allowed.
for value in \
  "$PATH" \
  "${LD_LIBRARY_PATH:-}" \
  "${CMAKE_PREFIX_PATH:-}" \
  "${PKG_CONFIG_PATH:-}" \
  "${ROOTSYS:-}" \
  "${PYTHONPATH:-}"; do
  if [[ "$value" == *spadi-host-sentinel* ]]; then
    echo "ERROR: host software environment leaked into container: $value" >&2
    exit 1
  fi
done

echo "=== FEE commands ==="
command -v openFPGALoader
openFPGALoader --version
command -v mpc-mpcx-ip-writer
command -v mpc-mpcx-ip-reader
command -v mpc-mpcx-ip-command
command -v sitcp-sitcpxg-ip-writer
command -v sitcp-sitcpxg-ip-reader

test -x /opt/spadi/bin/get_version
test -x /opt/spadi/StrHRTDC/bin/get_version_hrtdc
find /opt/spadi -name HulCoreConfig.cmake -print -quit | grep -q .

echo "=== Network diagnostics ==="
command -v ip
command -v ss
command -v ping
command -v netstat
command -v dig
command -v nslookup
command -v traceroute
command -v tcpdump
command -v nc
command -v curl
command -v lsof

echo "=== Shared libraries ==="
while IFS= read -r exe; do
  if file "$exe" | grep -q 'ELF'; then
    if ldd "$exe" 2>&1 | grep -q 'not found'; then
      echo "ERROR: unresolved shared library dependency: $exe" >&2
      ldd "$exe" >&2 || true
      exit 1
    fi
  fi
done < <(find /opt/spadi/bin /opt/spadi/StrHRTDC/bin -maxdepth 1 -type f -perm -111 2>/dev/null)

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
  test -d /opt/spadi/src/hul-common-lib
  test -d /opt/spadi/src/amaneq-soft
  test -d /opt/spadi/src/openFPGALoader
  test -d /opt/spadi/src/sitcp-sitcpxg-mpc-mpcx-ip-utility-first-trial
  test -d /opt/spadi/include
fi

echo "FEE ${kind} container check passed."
