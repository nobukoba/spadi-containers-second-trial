# Read only by the shared interactive SPADI shell, never the host bashrc.
# A fixed image label keeps Docker and Apptainer independent of host identity.
case "${SPADI_PROMPT_NAME:-}" in
    user-fee|devel-fee|user-daq|devel-daq|user-artemis|devel-artemis|user-full|devel-full) ;;
    *) SPADI_PROMPT_NAME=container ;;
esac
# Apptainer supplies this runtime marker even with --cleanenv.
# SIF images originate from Docker, so filesystem markers cannot distinguish them.
if [[ -n ${APPTAINER_CONTAINER:-} ]]; then
    _spadi_runtime=Apptainer
else
    _spadi_runtime=Docker
fi
PS1='\[\e[0m\][${_spadi_runtime}] \[\e[01;32m\]spadi@${SPADI_PROMPT_NAME}\[\e[0m\]:\[\e[01;34m\]\w\[\e[0m\]$ '
unset PROMPT_COMMAND
alias ls='ls --color=auto'
