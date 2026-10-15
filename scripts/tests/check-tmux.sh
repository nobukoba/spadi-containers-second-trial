#!/bin/bash
# Run in each Docker/SIF image; never touch a user's existing tmux sessions.
set -euo pipefail
[[ "$(command -v tmux)" == /usr/local/bin/tmux ]]
work="$(mktemp -d /tmp/spadi-tmux-check.XXXXXX)"
label="spadi-check-$$"
session="spadi-check-$$"
host_socket="$work/host.sock"
cleanup() {
  /usr/local/bin/tmux kill-session -t "$session" 2>/dev/null || true
  /usr/local/bin/tmux -L "$label" kill-server 2>/dev/null || true
  /usr/bin/tmux -S "$host_socket" kill-server 2>/dev/null || true
  rm -rf "$work"
}
trap cleanup EXIT
mkdir "$work/home"
printf '%s\n' 'set-option -g @host-config yes' > "$work/home/.tmux.conf"
printf 'touch %q\n' "$work/host-bashrc-read" > "$work/home/.bashrc"
# An external/default selection supplied by the caller must not be followed.
/usr/bin/tmux -f /dev/null -S "$host_socket" new-session -d -s host 'sleep 120'
host_pid="$(/usr/bin/tmux -S "$host_socket" display-message -p '#{pid}')"
env HOME="$work/home" TMUX="$host_socket,$host_pid,0" TMUX_PANE=%999 \
  TMUX_TMPDIR="$work" /usr/local/bin/tmux new-session -d -s "$session" 'sleep 120'
container_socket="$(/usr/local/bin/tmux display-message -p -t "$session" '#{socket_path}')"
[[ "$container_socket" == "/tmp/spadi-tmux-$(id -u)-$(stat -Lc %i /proc/self/ns/mnt)/tmux-$(id -u)/default" ]]
[[ "$container_socket" != "$host_socket" ]]
if /usr/bin/tmux -S "$host_socket" has-session -t "$session" 2>/dev/null; then
  echo 'ERROR: container session appeared in the external server' >&2
  exit 1
fi
/usr/bin/tmux -S "$host_socket" has-session -t host
# A named server is isolated too, and default panes use only container startup.
env HOME="$work/home" TMUX="$host_socket,$host_pid,0" TMUX_TMPDIR="$work" \
  /usr/local/bin/tmux -L "$label" new-session -d -s "$session"
named_socket="$(/usr/local/bin/tmux -L "$label" display-message -p -t "$session" '#{socket_path}')"
[[ "$named_socket" == "${container_socket%/*}/$label" ]]
[[ "$(/usr/local/bin/tmux -L "$label" show-options -gv default-command)" == /opt/spadi/spadi-shell.sh ]]
[[ -z "$(/usr/local/bin/tmux -L "$label" show-options -gqv @host-config)" ]]
# A valid TMUX from a pane must still find its own named server without -L.
named_pid="$(/usr/local/bin/tmux -L "$label" display-message -p '#{pid}')"
[[ "$(TMUX="$named_socket,$named_pid,0" /usr/local/bin/tmux display-message -p '#{socket_path}')" == "$named_socket" ]]
printf -v probe 'printf "%%s\\n" "$SPADI_PROMPT_NAME" > %q' "$work/pane-image"
/usr/local/bin/tmux -L "$label" send-keys -t "$session" "$probe" Enter
for _ in $(seq 1 100); do
  [[ -s "$work/pane-image" ]] && break
  sleep 0.1
done
[[ "$(cat "$work/pane-image")" == "$SPADI_PROMPT_NAME" ]]
[[ ! -e "$work/host-bashrc-read" ]]
echo 'tmux socket isolation, inherited environment, and container pane startup passed.'
