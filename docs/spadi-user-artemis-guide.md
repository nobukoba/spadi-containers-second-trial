# spadi-user-artemis guide

**Language: English | [日本語](spadi-user-artemis-guide.ja.md)**

This image provides ROOT and ARTEMIS analysis.

## Directory structure

```text
/opt/spadi/                         # SPADI_ROOT
├── bin/
├── lib/
├── lib64/
├── include/
├── share/
├── versions/
└── scripts/
│   ├── spadi-prepare-local.sh
│   └── artemis/

/workspace/spadi/                   # SPADI_LOCAL → host workspace/spadi
├── scripts/
│   └── artemis/
├── analysis/example/{macro,output}/
└── rawdata/
```

/opt/spadi is supplied by the image; /workspace/spadi is the persistent host workspace. spadi-prepare-local.sh creates scripts and rawdata. User images do not provide /opt/spadi/src. The mkdir command below creates analysis directories.

The SPADI_LOCAL environment variable defaults to `/workspace/spadi`; SPADI_ROOT defaults to `/opt/spadi`. Startup sets both variables but does not create directories. The local area maps to the host directory `workspace/spadi`. See the [common README procedures](../README.md) for the full explanation.

## Download and start the image

Run the following commands in the host terminal. Choose either Apptainer or Docker.

### Apptainer (Linux / Windows WSL2)

```bash
curl -fL -O \
  https://github.com/nobukoba/spadi-containers-second-trial/releases/download/latest/spadi-user-artemis.sif
mkdir -p "$PWD/workspace"
apptainer shell --cleanenv --bind "$PWD/workspace:/workspace" \
  --shell /opt/spadi/spadi-shell.sh spadi-user-artemis.sif
```

### Docker (macOS / Linux)

```bash
docker pull --platform linux/amd64 \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-user-artemis:latest
mkdir -p "$PWD/workspace"
docker run --rm -it \
  --platform linux/amd64 \
  -e LOCAL_UID="$(id -u)" -e LOCAL_GID="$(id -g)" \
  -v "$PWD/workspace:/workspace" \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-user-artemis:latest
```

Files under `workspace` persist on the host. Download or pull again when updating the image.

## Prepare the workspace

Copy the runtime scripts available in this image. Existing configuration and source files are preserved. See the [README](../README.md) for common preparation and update procedures.

```bash
spadi-prepare-local.sh
```

## Start ROOT and ARTEMIS

Container startup loads the ROOT and ARTEMIS environment. Check the version and executables:

```bash
root-config --version
command -v root
command -v artemis
mkdir -p "$SPADI_LOCAL/analysis/example/macro" "$SPADI_LOCAL/analysis/example/output"
cd "$SPADI_LOCAL/analysis/example"
```

The mkdir command creates the analysis directories. spadi-prepare-local.sh prepares the available ARTEMIS scripts and rawdata directory; experiment steering files, calibration parameters, and input data must be supplied separately.

Check ROOT and save a ROOT file without a graphical display:

```bash
root -b -q -e 'TFile f("output/example.root", "RECREATE"); TH1D h("example", "Example", 100, 0, 100); h.Fill(42); h.Write(); f.Close();'
ls -lh output/example.root
```

The result persists at host workspace/spadi/analysis/example/output/example.root. This example creates a synthetic histogram; it does not decode experiment data.

Start interactive ROOT or ARTEMIS with the following commands. Enter .q at each application prompt to exit.

```bash
root -l
# Enter .q before running the next command.
artemis
```

Graphical histogram windows require a display connection; the batch example above uses no xterm or X11. Browser-controlled acquisition is provided by the DAQ/FULL Web Controller. ARTEMIS itself is operated from the terminal or analysis macros.

## Analyze experiment data

Place the experiment steering files, processors, calibration files, and macros under a working directory in $SPADI_LOCAL/analysis and start ARTEMIS there. Keep inputs under $SPADI_LOCAL/rawdata and output ROOT files in the analysis output directory so they persist on the host. Follow the experiment procedures for loading its libraries and running its analysis.

NestDAQ FileSink .dat files contain TF/STF records. They require a compatible input processor, decoder, and steering configuration; they cannot simply be opened as ROOT files. This repository does not ship a complete ARTEMIS steering configuration for the single-channel AMANEQ example. See the [official ARTEMIS README](https://github.com/artemis-dev/artemis/tree/develop).

## Appendix: Included software

These are the main included software components. Pins are defined in [versions.env](../versions/versions.env). Inspect `/opt/spadi/scripts/spadi-version.sh` and `/opt/spadi/versions/versions.env` inside your image for its actual build metadata. Locally rebuilt software may differ from this baseline.

| Software | Purpose | Pinned version / revision |
|---|---|---|
| [ROOT](https://github.com/root-project/root) | Analysis, histograms, TTree and Cling | [`v6-32-06`](https://github.com/root-project/root/tree/v6-32-06) |
| [ARTEMIS](https://github.com/artemis-dev/artemis) | Nuclear-physics analysis framework | [`c74e24adf90a`](https://github.com/artemis-dev/artemis/tree/c74e24adf90a83227fa3e5c38dc255ddc4aeb785) |
| [yaml-cpp](https://github.com/jbeder/yaml-cpp) | YAML configuration parser | [`0.8.0`](https://github.com/jbeder/yaml-cpp/tree/0.8.0) |
| [ZeroMQ](https://github.com/zeromq/libzmq) | Messaging library | [`v4.3.5`](https://github.com/zeromq/libzmq/tree/v4.3.5) |
| [hiredis](https://github.com/redis/hiredis) | Redis/Valkey C client | [`v1.0.0`](https://github.com/redis/hiredis/tree/v1.0.0) |
| [redis-plus-plus](https://github.com/sewenew/redis-plus-plus) | Redis/Valkey C++ client | [`1.3.15`](https://github.com/sewenew/redis-plus-plus/tree/1.3.15) |

The OS is AlmaLinux 9. tmux, vim / emacs, and basic file/process tools are also included. OS packages use AlmaLinux package versions rather than the source pins above.

ROOT enables TMVA, X11 / OpenGL, SQLite, and SSL; PyROOT, RooFit, and Web GUI are disabled. ARTEMIS disables GET and enables ZeroMQ / Redis support. OpenMPI and compression libraries are also included.

`spadi-user-*` images provide runtime software without source trees or local-development build helpers. A C++ compiler and headers are retained for ROOT / Cling runtime use.
