# spadi-devel-artemis guide

**Language: English | [日本語](spadi-devel-artemis-guide.ja.md)**

This image provides ROOT and ARTEMIS analysis. This guide also covers source editing and rebuilding.

## Directory structure

```text
/opt/spadi/                         # SPADI_ROOT
├── bin/
├── lib/
├── lib64/
├── include/
├── share/
├── versions/
├── scripts/
│   ├── spadi-prepare-runtime.sh
│   ├── spadi-prepare-local.sh
│   ├── spadi-env.sh
│   ├── *-build.sh / *-clone-latest.sh
│   └── artemis/
└── src/
    ├── root/
    └── artemis/

/workspace/spadi/                   # SPADI_LOCAL → host workspace/spadi
├── scripts/
│   └── artemis/
├── bin/
├── lib/
├── lib64/
├── include/
├── share/
├── src/
├── build/
├── analysis/example/{macro,output}/
└── rawdata/
```

/opt/spadi is supplied by the image; /workspace/spadi is the persistent host workspace. spadi-prepare-local.sh creates the local scripts, src, build, bin, lib, lib64, include, share, and rawdata directories. Source lists show the main editable projects. The mkdir command below creates analysis directories.

The SPADI_LOCAL environment variable defaults to `/workspace/spadi`; SPADI_ROOT defaults to `/opt/spadi`. Startup sets both variables but does not create directories. The local area maps to the host directory `workspace/spadi`. See the [common README procedures](../README.md) for the full explanation.

## Download the image

Run these commands in a host terminal, outside the container. Choose either Apptainer or Docker for your environment.

### Apptainer

Install Apptainer on 64 bit Linux (x86_64) or a Windows WSL2 Linux distribution, then download this image's SIF from the Linux terminal.

```bash
curl -fL -O \
  https://github.com/nobukoba/spadi-containers-second-trial/releases/download/latest/spadi-devel-artemis.sif
```

### Docker

Start Docker on macOS or Linux, then download this image from the host terminal. Keep `--platform linux/amd64` on Apple Silicon as well.

```bash
docker pull --platform linux/amd64 \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-artemis:latest
```

`latest` can change. For repeatable environments, retain a timestamped SIF from [GitHub Releases](https://github.com/nobukoba/spadi-containers-second-trial/releases/tag/latest) or record the Docker image digest. See the [README Quick start](../README.md#quick-start) for startup and persistence settings.

## Start this image

Use **`spadi-devel-artemis`** as the image name in the [README Quick start](../README.md#quick-start). Its SIF filename is `spadi-devel-artemis.sif`; its Docker image is `ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-artemis:latest`. Run the remaining commands inside the container.

```bash
/opt/spadi/scripts/spadi-version.sh
```

## Prepare the workspace

Prepare a workspace including source and build directories. Existing configuration and source files are preserved. See the [README](../README.md) for common preparation and update procedures.

```bash
spadi-prepare-local.sh
```

## Edit and build software

Edit the source copied by spadi-prepare-local.sh under $SPADI_LOCAL/src. Build helpers compile that source and install the result into $SPADI_LOCAL. Stop DAQ or analysis processes using the local installation before rebuilding. You do not need to rebuild the container image.

| Source directory | Build helper |
|---|---|
| `$SPADI_LOCAL/src/artemis` | `artemis-build.sh` |

```bash
artemis-build.sh
```

The list is in dependency order. Rebuild the changed component and its dependents as needed. Helpers default to NPROC=4; set a smaller value, for example NPROC=2 artemis-build.sh. The ARTEMIS helper uses $SPADI_LOCAL/build/artemis. No root-build.sh helper is provided; retained ROOT sources are available for inspection and separate development.

## Try latest upstream source

Cloning and building are separate operations. Clone helpers refuse existing source directories. Preserve your current source and confirm the destination is absent before deliberately switching to latest upstream source.

```bash
artemis-clone-latest.sh
artemis-build.sh
```

Normal preparation copies the sources pinned in the image. Latest upstream source is outside that validated baseline. The ARTEMIS clone helper uses the upstream default branch, which may differ from the pinned develop commit used in the image.

## Check the rebuilt installation

```bash
spadi-env.sh
command -v artemis
```

Local bin and lib paths precede the image installation. The version reporter describes the image, not your local modifications; record source commits and build logs too.

For Dockerfile, CI, SIF creation, and publication changes, see the [container maintainer guide](container-maintainer-guide.md).

## Start ROOT and ARTEMIS

Container startup loads the ROOT and ARTEMIS environment. Check the version and executables:

```bash
root-config --version
command -v root
command -v artemis
mkdir -p "$SPADI_LOCAL/analysis/example/macro" "$SPADI_LOCAL/analysis/example/output"
cd "$SPADI_LOCAL/analysis/example"
```

The mkdir command creates the analysis directories. spadi-prepare-runtime.sh prepares the available ARTEMIS scripts and rawdata directory; experiment steering files, calibration parameters, and input data must be supplied separately.

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
