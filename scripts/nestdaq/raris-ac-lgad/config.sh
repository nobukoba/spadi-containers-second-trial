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

VALKEY_HOST="127.0.0.1"
VALKEY_PORT=6379
DAQSERVICE_DB=0
METRICS_DB=1
PARAMETER_DB=2
WEBCTL_HOST="0.0.0.0"
WEBCTL_PORT=8080
NESTDAQ_HOST_IP="127.0.0.1"

# relative-path|public-download-url|optional-sha256
# Replace these working reference URLs with public Google Drive direct-download
# URLs later without changing the downloader implementation.
RAWDATA_FILES=(
  "00/run000020.dat|https://raw.githubusercontent.com/nobukoba/container-interfacing-nestdaq-eicrecon/main/example_rawdata/raris_ac_lgad_202603/00/run000020.dat|"
  "01/run000020.dat|https://raw.githubusercontent.com/nobukoba/container-interfacing-nestdaq-eicrecon/main/example_rawdata/raris_ac_lgad_202603/01/run000020.dat|"
  "02/run000020.dat|https://raw.githubusercontent.com/nobukoba/container-interfacing-nestdaq-eicrecon/main/example_rawdata/raris_ac_lgad_202603/02/run000020.dat|"
)
