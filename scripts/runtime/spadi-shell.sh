#!/bin/bash
# Used by Docker CMD and Apptainer shell --shell; never remap the host user.
set -e
source /opt/spadi/spadi-setup.sh
cd /workspace
# Avoid host ~/.bashrc overriding the validated SPADI environment in Apptainer.
unset BASH_ENV ENV PROMPT_COMMAND
# A shell session stays interactive even when CI pipes input without a TTY.
# Explicit command arguments (for example -c) retain their original behavior.
if [[ $# -eq 0 ]]; then
    set -- -i
fi
exec /bin/bash --noprofile --rcfile /opt/spadi/spadi-bashrc.sh "$@"
