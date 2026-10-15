#!/bin/bash
# Check environment routing without Docker or a tmux installation.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
cat > "$work/tmux-real" <<'MOCK'
#!/bin/bash
printf '%s\n' "${TMUX_TMPDIR:-}" "${TMUX:-unset}" "${TMUX_PANE:-unset}"
printf '<%s>\n' "$@"
MOCK
chmod +x "$work/tmux-real"
sed "s|/usr/bin/tmux|$work/tmux-real|g" "$root/scripts/runtime/spadi-tmux.sh" > "$work/wrapper"
expected="/tmp/spadi-tmux-$(id -u)-$(stat -Lc %i /proc/self/ns/mnt)"
output="$(TMUX=/tmp/host.sock,123,0 TMUX_PANE=%99 TMUX_TMPDIR=/tmp/host bash "$work/wrapper" -L 'name with spaces' list-sessions)"
[[ "$output" == "$expected"$'\nunset\nunset\n<-f>\n</opt/spadi/tmux.conf>\n<-L>\n<name with spaces>\n<list-sessions>' ]]
inside="$expected/tmux-$(id -u)/spadi,123,0"
output="$(TMUX="$inside" TMUX_PANE=%5 bash "$work/wrapper" list-sessions)"
[[ "$output" == "$expected"$'\n'"$inside"$'\n%5\n<-f>\n</opt/spadi/tmux.conf>\n<list-sessions>' ]]
output="$(env -u TMUX -u TMUX_PANE bash "$work/wrapper" list-sessions)"
[[ "$output" == "$expected"$'\nunset\nunset\n<-f>\n</opt/spadi/tmux.conf>\n<list-sessions>' ]]
echo 'tmux wrapper: host variables rejected, internal pane retained, arguments preserved.'
