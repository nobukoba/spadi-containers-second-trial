#!/usr/bin/env bash
# Test hardware command arguments and fail-closed handling without a board.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
temporary="$(mktemp -d)"
trap 'rm -rf "$temporary"' EXIT
export MASK_TEST_LOG="${temporary}/calls"
cat > "${temporary}/set_tdcmask" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "$MASK_TEST_LOG"
if [[ "${MASK_TEST_MODE:-}" == write-error ]]; then echo '#E: RBCP timeout'; fi
EOF
cat > "${temporary}/read_register" <<'EOF'
#!/usr/bin/env bash
value=ffffffff
[[ "$2" != 10300000 ]] || value=ffffffbf
case "${MASK_TEST_MODE:-}" in
    mismatch) value=0 ;;
    read-error) echo '#E: RBCP timeout' ;;
esac
printf '#D: Read register: 0 (0x%s)\n' "$value"
EOF
chmod +x "${temporary}/set_tdcmask" "${temporary}/read_register"
export PATH="${temporary}:$PATH"
recipe="${ROOT}/scripts/fee/amaneq-lrtdc-1ch"
bash -n "${recipe}/config.sh" "${recipe}/setup.sh"
bash "${recipe}/setup.sh"
cat > "${temporary}/expected" <<'EOF'
192.168.10.16 ffffffff ffffffff ffffffff ffffffbf
EOF
diff -u "${temporary}/expected" "$MASK_TEST_LOG"
source "${recipe}/config.sh"
for ((channel=0; channel<128; channel++)); do
    masks=("$MASK_MAIN_U" "$MASK_MAIN_D" "$MASK_MZN_U" "$MASK_MZN_D")
    masked=$(( (16#${masks[channel/32]} >> (channel%32)) & 1 ))
    if ((channel == 102)); then ((masked == 0)); else ((masked == 1)); fi
done
for mode in write-error read-error mismatch; do
    : > "$MASK_TEST_LOG"
    if MASK_TEST_MODE="$mode" bash "${recipe}/setup.sh" > "${temporary}/output" 2>&1; then
        echo "Expected failure: $mode" >&2
        exit 1
    fi
    [[ "$(wc -l < "$MASK_TEST_LOG")" -eq 1 ]]
done
echo 'PASS: only channel 102 unmasked; all error cases stop acquisition preparation.'
