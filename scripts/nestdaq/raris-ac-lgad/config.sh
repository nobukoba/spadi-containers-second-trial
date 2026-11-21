#!/usr/bin/env bash
CONFIG_NAME="raris-ac-lgad"
TMUX_SESSION="nestdaq-raris-ac-lgad"
TMUX_SOCKET="spadi"

STF_PLAYERS=3
TF_BUILDERS=1

SPADI_WORKSPACE="${SPADI_LOCAL:-/workspace/spadi}"
RAWDATA_DIR="${SPADI_WORKSPACE}/rawdata/raris_ac_lgad_202603"
RUN_FILE="run000020.dat"

MAX_HBF=4
TFB_DECIMATION_FACTOR=1000
TFB_DISCARD_OUTPUT=false
TFB_ENABLE_UDS=false

STF_TO_TFB_HOST="127.0.0.1"
STF_TO_TFB_PORT=5500
TFB_OUTPUT_HOST="127.0.0.1"
TFB_OUTPUT_PORT=5501

REDIS_HOST="127.0.0.1"
REDIS_PORT=6379
DAQSERVICE_DB=0
METRICS_DB=1
PARAMETER_DB=2
WEBCTL_HOST="0.0.0.0"
WEBCTL_PORT=8080
NESTDAQ_HOST_IP="127.0.0.1"

# relative-path|public-download-url|optional-sha256
# Pin both the public source revision and content hashes for repeatable analysis.
RAWDATA_FILES=(
  "00/run000020.dat|https://raw.githubusercontent.com/nobukoba/container-interfacing-nestdaq-eicrecon/ccf94e725389b5d32b2cd167312deb88c6461eba/example_rawdata/raris_ac_lgad_202603/00/run000020.dat|b73c444a3c08db81ca655d8bb01f872a0743cad5d6ccc8a0326769b02131a3a0"
  "01/run000020.dat|https://raw.githubusercontent.com/nobukoba/container-interfacing-nestdaq-eicrecon/ccf94e725389b5d32b2cd167312deb88c6461eba/example_rawdata/raris_ac_lgad_202603/01/run000020.dat|3272efa10a4875ecc37e7b5559acbb36e7fdf16c4469e8ef5bab93a4de48d810"
  "02/run000020.dat|https://raw.githubusercontent.com/nobukoba/container-interfacing-nestdaq-eicrecon/ccf94e725389b5d32b2cd167312deb88c6461eba/example_rawdata/raris_ac_lgad_202603/02/run000020.dat|553faf9912022e80b7cc9e2cc6b41c1d19065b99dfc5307b50e54097738acd9b"
)
