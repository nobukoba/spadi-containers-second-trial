# Source inside the interactive shell under test (Docker or Apptainer).
set -euo pipefail
[[ $- == *i* ]]
test "$PWD" = /workspace
expected='\[\e[01;32m\]spadi@${SPADI_PROMPT_NAME}\[\e[0m\]:\[\e[01;34m\]\w\[\e[0m\]$ '
test "$PS1" = "$expected"
test "$(alias ls)" = "alias ls='ls --color=auto'"
test -z "${PROMPT_COMMAND:-}"
test -z "${BASH_ENV:-}"
test "${PATH%%:*}" = /workspace/spadi/bin
mkdir -p /workspace/prompt-check
cd /workspace/prompt-check
# Verify prompt expansion reflects directory changes and the selected image.
case "${PS1@P}" in
    *"spadi@${SPADI_PROMPT_NAME}"*"/workspace/prompt-check"*) ;;
    *) exit 1 ;;
esac
