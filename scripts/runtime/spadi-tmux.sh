#!/bin/bash
# Keep implicit/default and -L connections inside this container mount namespace.
set -euo pipefail
uid="$(id -u)"
mount_id="$(stat -Lc %i /proc/self/ns/mnt)"
[[ "$mount_id" =~ ^[0-9]+$ ]] || { echo 'Cannot identify the container mount namespace.' >&2; exit 1; }
export TMUX_TMPDIR="/tmp/spadi-tmux-${uid}-${mount_id}"
if [[ ! -e "$TMUX_TMPDIR" ]]; then
  (umask 077; mkdir "$TMUX_TMPDIR") || [[ -d "$TMUX_TMPDIR" ]]
fi
if [[ -L "$TMUX_TMPDIR" || ! -d "$TMUX_TMPDIR" || "$(stat -c %u "$TMUX_TMPDIR")" != "$uid" ]]; then
  echo "Invalid tmux socket directory: $TMUX_TMPDIR" >&2
  exit 1
fi
chmod 700 "$TMUX_TMPDIR"
# Preserve current-pane/default-server behavior inside this container, but never
# let an inherited host TMUX select an external socket or trigger nesting checks.
inherited_tmux="${TMUX:-}"
case "${inherited_tmux%%,*}" in
  "$TMUX_TMPDIR/tmux-${uid}/"*) ;;
  *) unset TMUX TMUX_PANE ;;
esac
# Explicit -S/-f options remain deliberate user overrides. Ordinary commands
# and existing recipes using -L are isolated without changing their arguments.
exec /usr/bin/tmux -f /opt/spadi/tmux.conf "$@"
