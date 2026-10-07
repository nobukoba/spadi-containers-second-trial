#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/config.sh"
[[ $# -le 1 ]] || { echo 'Usage: setup.sh [AMANEQ-IP]' >&2; exit 2; }
AMANEQ_IP="${1:-$AMANEQ_IP}"

# Select the LR tool explicitly: HR installs a command with the same name.
tdcmask="${SPADI_ROOT:-/opt/spadi}/StrLRTDC/bin/set_tdcmask"
if [[ ! -x "$tdcmask" ]]; then
    tdcmask="$(command -v set_tdcmask)"
fi
command -v read_register >/dev/null
output="$("$tdcmask" "$AMANEQ_IP" "$MASK_MAIN_U" "$MASK_MAIN_D" "$MASK_MZN_U" "$MASK_MZN_D" 2>&1)"
printf '%s\n' "$output"
if [[ "$output" == *'#E'* ]]; then
    echo 'TDC mask write failed' >&2
    exit 1
fi

verify_mask() {
    local address="$1" expected="$2" output
    output="$(read_register "$AMANEQ_IP" "$address" 4 2>&1)"
    printf '%s\n' "$output"
    if [[ "$output" == *'#E'* || "$output" != *"(0x${expected})"* ]]; then
        echo "Mask verification failed at $address; expected 0x${expected}" >&2
        exit 1
    fi
}

# Verify all four banks after the single set_tdcmask invocation.
verify_mask 10000000 "$MASK_MAIN_U"
verify_mask 10100000 "$MASK_MAIN_D"
verify_mask 10200000 "$MASK_MZN_U"
verify_mask 10300000 "$MASK_MZN_D"
echo "Verified LR-TDC masks at ${AMANEQ_IP}: only channel 102 is unmasked."
