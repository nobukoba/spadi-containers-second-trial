#!/usr/bin/env bash
set -u
[[ $# -ge 2 ]] || { echo "Usage: keep-device-window.sh <label> <command> [args...]" >&2; exit 2; }
label="$1"; shift; "$@"; status=$?
echo; echo "========================================"; echo "${label} exited with status: ${status}"; echo "This tmux window is kept for debugging."; echo "========================================"; exec bash
