#!/bin/bash
# Used by Docker CMD and Apptainer shell --shell; never remap the host user.
set -e
source /opt/spadi/spadi-setup.sh
cd /workspace
# Avoid host ~/.bashrc overriding the validated SPADI environment in Apptainer.
unset BASH_ENV ENV PROMPT_COMMAND
exec /bin/bash --noprofile --rcfile /opt/spadi/spadi-bashrc.sh "$@"
