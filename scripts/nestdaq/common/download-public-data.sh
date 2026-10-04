#!/usr/bin/env bash
set -euo pipefail
[[ $# -ge 3 ]] || { echo "Usage: download-public-data.sh <destination-root> <relative-path> <url> [sha256]" >&2; exit 2; }
root="$1"; relative="$2"; url="$3"; expected_sha="${4:-}"; dest="${root}/${relative}"; mkdir -p "$(dirname "$dest")"
if [[ -f "$dest" && -n "$expected_sha" ]] && [[ "$(sha256sum "$dest" | awk '{print $1}')" == "$expected_sha" ]]; then echo "already complete: $relative"; exit 0; fi
echo; echo "Downloading: $relative"; echo "Source:      $url"; echo "Destination: $dest"
curl --fail --location --progress-bar --continue-at - --output "$dest" "$url"
[[ -z "$expected_sha" ]] || echo "${expected_sha}  ${dest}" | sha256sum --check -
echo "complete: $relative"
