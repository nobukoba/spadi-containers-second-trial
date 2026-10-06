#!/usr/bin/env bash
# Host-side regression test; no SPADI compilation or published image needed.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
test_image="${ENTRYPOINT_TEST_IMAGE:-almalinux:9}"

docker run --rm -i --platform linux/amd64 \
  --mount "type=bind,src=${script_dir}/../runtime/spadi-entrypoint.sh,dst=/test-entrypoint.sh,readonly" \
  --entrypoint /bin/bash "$test_image" -s <<'CONTAINER_TEST'
set -euo pipefail
source /etc/os-release
test "$ID" = almalinux
test "${VERSION_ID%%.*}" = 9
if ! command -v useradd >/dev/null || ! command -v setpriv >/dev/null; then
  dnf -y install shadow-utils util-linux > /tmp/install.log 2>&1 || {
    tail -n 50 /tmp/install.log
    exit 1
  }
fi
groupadd --gid 1000 spadi
useradd --uid 1000 --gid spadi --create-home --shell /bin/bash spadi
mkdir -p /workspace

export SPADI_ROOT=/opt/spadi
export PATH=/opt/spadi/bin:$PATH
export LD_LIBRARY_PATH=/opt/spadi/lib:/opt/spadi/lib64
export CMAKE_PREFIX_PATH=/opt/spadi
export PKG_CONFIG_PATH=/opt/spadi/lib/pkgconfig

check_identity() {
  bash /test-entrypoint.sh bash -c '
    set -euo pipefail
    test "$(id -u)" = "$1"
    test "$(id -g)" = "$2"
    test "$(id -un)" = spadi
    test "$HOME" = /home/spadi
    test "$USER" = spadi
    test "$LOGNAME" = spadi
    test "$SPADI_ROOT" = /opt/spadi
    test "${PATH%%:*}" = /opt/spadi/bin
    test "$LD_LIBRARY_PATH" = /opt/spadi/lib:/opt/spadi/lib64
    test "$CMAKE_PREFIX_PATH" = /opt/spadi
    test "$PKG_CONFIG_PATH" = /opt/spadi/lib/pkgconfig
    test "$3" = "argument with spaces"
    test "$4" = "--literal"
    touch /workspace/identity-check
    test "$(stat -c %u /workspace/identity-check)" = "$1"
    test "$(stat -c %g /workspace/identity-check)" = "$2"
    rm /workspace/identity-check
  ' test "$1" "$2" 'argument with spaces' --literal
}

# Cover defaults, remapping to a new group, and reusing an existing group.
check_identity 1000 1000
export LOCAL_UID=12345 LOCAL_GID=12346
check_identity 12345 12346
export LOCAL_UID=23456 LOCAL_GID=1
check_identity 23456 1

status=0
bash /test-entrypoint.sh bash -c 'exit 42' || status=$?
test "$status" = 42

status=0
LOCAL_UID=0 bash /test-entrypoint.sh /bin/true || status=$?
test "$status" = 2
echo 'Entrypoint identity, environment, arguments, ownership, and exit status checks passed.'
CONTAINER_TEST
