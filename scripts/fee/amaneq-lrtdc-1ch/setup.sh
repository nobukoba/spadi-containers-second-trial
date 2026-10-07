#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/config.sh"
[[ $# -le 1 ]] || { echo 'Usage: setup.sh [AMANEQ-IP]' >&2; exit 2; }
AMANEQ_IP="${1:-$AMANEQ_IP}"

command -v write_register >/dev/null
command -v read_register >/dev/null

set_mask() {
    local address="$1" expected="$2" output
    # The pinned upstream tools can report RBCP errors but still exit zero.
    output="$(write_register "$AMANEQ_IP" "$address" "$expected" 4 2>&1)"
    printf '%s\n' "$output"
    if [[ "$output" == *'#E'* ]]; then
        echo "Mask write failed at $address" >&2
        exit 1
    fi
    output="$(read_register "$AMANEQ_IP" "$address" 4 2>&1)"
    printf '%s\n' "$output"
    if [[ "$output" == *'#E'* || "$output" != *"(0x${expected})"* ]]; then
        echo "Mask verification failed at $address; expected 0x${expected}" >&2
        exit 1
    fi
}

# Apply the selected bank last, after masking every other bank.
set_mask 10000000 "$MASK_MAIN_U"
set_mask 10100000 "$MASK_MAIN_D"
set_mask 10200000 "$MASK_MZN_U"
set_mask 10300000 "$MASK_MZN_D"
echo "Verified LR-TDC masks at ${AMANEQ_IP}: only channel 102 is unmasked."
