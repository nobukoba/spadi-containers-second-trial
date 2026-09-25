#!/bin/bash
set -euo pipefail

SPADI_UID="${LOCAL_UID:-1000}"
SPADI_GID="${LOCAL_GID:-1000}"

if [[ ! "${SPADI_UID}" =~ ^[1-9][0-9]*$ ]] || [[ ! "${SPADI_GID}" =~ ^[1-9][0-9]*$ ]]; then
  echo "LOCAL_UID and LOCAL_GID must be positive numeric IDs." >&2
  exit 2
fi

if existing_user="$(getent passwd "${SPADI_UID}" | cut -d: -f1)" && [[ -n "${existing_user}" && "${existing_user}" != "spadi" ]]; then
  echo "UID ${SPADI_UID} is already used by ${existing_user} inside the container." >&2
  exit 2
fi

if existing_group="$(getent group "${SPADI_GID}" | cut -d: -f1)" && [[ -n "${existing_group}" ]]; then
  target_group="${existing_group}"
else
  groupmod --gid "${SPADI_GID}" spadi
  target_group=spadi
fi

usermod --uid "${SPADI_UID}" --gid "${target_group}" spadi
chown -R "${SPADI_UID}:${SPADI_GID}" /home/spadi
chown "${SPADI_UID}:${SPADI_GID}" /workspace

export HOME=/home/spadi
export USER=spadi
export LOGNAME=spadi

exec setpriv   --reuid="${SPADI_UID}"   --regid="${SPADI_GID}"   --init-groups   --reset-env=false   -- "$@"
