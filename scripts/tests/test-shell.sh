#!/usr/bin/env bash
# Check startup without compiling SPADI, including an Apptainer-style host user.
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for identity in 0:0 12345:12346; do
  docker run --rm --platform linux/amd64 --user "$identity" --workdir /tmp \
    --mount "type=bind,src=${script_dir}/../runtime,dst=/opt/spadi,readonly" \
    --tmpfs /workspace:mode=1777 \
    --env SPADI_ROOT=/opt/spadi --env SPADI_LOCAL=/workspace/spadi \
    --entrypoint /bin/bash almalinux:9 /opt/spadi/spadi-shell.sh -c '
      set -euo pipefail
      test "$PWD" = /workspace
      test "${PATH%%:*}" = /workspace/spadi/bin
      test "$LD_LIBRARY_PATH" = /workspace/spadi/lib:/workspace/spadi/lib64:/opt/spadi/lib:/opt/spadi/lib64
      touch startup-check
      test "$(stat -c %u startup-check)" = "$(id -u)"
    '
done
status=0
docker run --rm --platform linux/amd64 \
  --mount "type=bind,src=${script_dir}/../runtime,dst=/opt/spadi,readonly" \
  --tmpfs /workspace:mode=1777 --entrypoint /bin/bash \
  almalinux:9 /opt/spadi/spadi-shell.sh -c 'exit 42' || status=$?
test "$status" = 42
echo 'Shell startup, overlay paths, host identity, workspace, and exit status checks passed.'
