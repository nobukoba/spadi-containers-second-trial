#!/usr/bin/env bash
set -euo pipefail


# Version metadata must be self-describing in Docker and SIF images.
test -x /opt/spadi/scripts/spadi-version.sh
test -r /opt/spadi/versions/versions.env
test -r /opt/spadi/versions/container.env
version_output="$(/opt/spadi/scripts/spadi-version.sh)"
grep -q '^SPADI container version : ' <<<"$version_output"
grep -q '^Git commit              : ' <<<"$version_output"
grep -q '^Image target            : ' <<<"$version_output"
grep -q '^NESTDAQ_REF=' /opt/spadi/versions/versions.env
grep -q '^ROOT_VERSION=' /opt/spadi/versions/versions.env
grep -q '^ARTEMIS_REF=' /opt/spadi/versions/versions.env
kind="${1:-${SPADI_IMAGE_KIND:-}}"
if [[ "$kind" != "user" && "$kind" != "devel" ]]; then
  echo "usage: smoke-test-full.sh {user|devel}" >&2
  exit 2
fi

assert_command_absent() {
  local cmd="$1"
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "ERROR: unexpected command in runtime image: $cmd ($(command -v "$cmd"))" >&2
    return 1
  fi
}

echo "=== Unified environment ==="
test "${SPADI_ROOT:-}" = "/opt/spadi"
test "${ROOTSYS:-}" = "/opt/spadi"
test "${ARTEMIS_ROOT:-}" = "/opt/spadi"
test "${TARTSYS:-}" = "/opt/spadi"
test "${EXP_CONFIG_ROOT:-}" = "/opt/spadi/scripts/exp-config"
test -d /workspace
test -w /workspace

echo "=== FEE ==="
command -v openFPGALoader
command -v mpc-mpcx-ip-writer
command -v sitcp-sitcpxg-ip-reader

echo "=== DAQ ==="
command -v daq-webctl
command -v TimeFrameBuilder
command -v STFBFilePlayer
test -r /opt/spadi/lib/redistimeseries.so
test -d /opt/spadi/scripts/exp-config

echo "=== Redis client linkage ==="
grep -q '^REDIS_PLUS_PLUS_VERSION=1.3.15$' /opt/spadi/versions/versions.env
grep -q '^HIREDIS_VERSION=v1.0.0$' /opt/spadi/versions/versions.env
test -e /opt/spadi/lib/libredis++.so
test -e /opt/spadi/lib/libhiredis.so
ldd /opt/spadi/bin/TimeFrameBuilder | grep -Eq 'libredis\+\+\.so.*=> /opt/spadi/lib/'
ldd /opt/spadi/bin/TimeFrameBuilder | grep -Eq 'libhiredis\.so.*=> /opt/spadi/lib/'

echo "=== ROOT / ARTEMIS ==="
command -v root-config
root-config --version
command -v root
root -b -q -e 'gSystem->Exit(0);'
command -v artemis

echo "=== ROOT compressed TTree I/O ==="
cat > /workspace/root-compression-smoke.C <<'EOF'
#include <Compression.h>
#include <TFile.h>
#include <TTree.h>
#include <array>
#include <cstdio>
#include <memory>

int root_compression_smoke() {
  using EAlgorithm = ROOT::RCompressionSetting::EAlgorithm;
  const std::array<EAlgorithm::EValues, 4> algorithms = {
    EAlgorithm::kZLIB, EAlgorithm::kLZMA,
    EAlgorithm::kLZ4, EAlgorithm::kZSTD
  };
  for (auto algorithm : algorithms) {
    const int code = static_cast<int>(algorithm);
    const TString path = TString::Format("/workspace/root-compression-%d.root", code);
    {
      TFile out(path, "RECREATE", "", ROOT::CompressionSettings(algorithm, 1));
      if (out.IsZombie()) return 10 + code;
      TTree tree("tree", "compression smoke test");
      int value = 0;
      tree.Branch("value", &value);
      for (value = 0; value < 1000; ++value) tree.Fill();
      tree.Write();
      out.Close();
    }
    {
      std::unique_ptr<TFile> in(TFile::Open(path, "READ"));
      if (!in || in->IsZombie()) return 20 + code;
      TTree *tree = nullptr;
      in->GetObject("tree", tree);
      if (!tree || tree->GetEntries() != 1000) return 30 + code;
      int value = -1;
      tree->SetBranchAddress("value", &value);
      if (tree->GetEntry(999) <= 0 || value != 999) return 40 + code;
    }
    std::remove(path.Data());
  }
  return 0;
}
EOF
root -b -q '/workspace/root-compression-smoke.C()'
rm -f /workspace/root-compression-smoke.C
test -r /opt/spadi/bin/thisroot.sh
test -r /opt/spadi/bin/thisartemis.sh
artemis --help >/tmp/artemis-help.txt 2>&1 || true

for exe in \
  "$(command -v openFPGALoader)" \
  "$(command -v daq-webctl)" \
  "$(command -v TimeFrameBuilder)" \
  "$(command -v root)" \
  "$(command -v artemis)"; do
  if ldd "$exe" | grep -q 'not found'; then
    echo "ERROR: unresolved shared library for $exe" >&2
    exit 1
  fi
done

command -v TriggerView >/dev/null 2>&1 || {
  echo "ERROR: ROOT-dependent TriggerView was not installed in FULL image" >&2
  exit 1
}

if [[ "$kind" == "user" ]]; then
  echo "=== User image policy ==="
  command -v c++
  test -r /opt/spadi/include/ROOT.modulemap
  assert_command_absent cmake
  assert_command_absent git
  test ! -d /opt/spadi/src
else
  echo "=== Development image policy ==="
  command -v gcc
  command -v g++
  command -v cmake
  command -v make
  command -v git
  test -d /opt/spadi/src/nestdaq
  test -d /opt/spadi/src/nestdaq-user-impl
  test -d /opt/spadi/src/root
  test -d /opt/spadi/src/artemis
  test -d /opt/spadi/include
fi

echo "FULL ${kind} container check passed."
