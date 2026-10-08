# SPADI Containers — Second Trial

**Language: English | [日本語](README.ja.md)**

Pre-built Docker and Apptainer SIF environments for SPADI Front End Electronics (FEE), NestDAQ, and ARTEMIS software.

Use `spadi-user-*` for normal operation and `spadi-devel-*` when you want to edit and rebuild SPADI software inside the container.

## Image types

| Purpose | User image | Development image |
|---|---|---|
| FEE control | [spadi-user-fee](docs/spadi-user-fee-guide.md) | [spadi-devel-fee](docs/spadi-devel-fee-guide.md) |
| NestDAQ | [spadi-user-daq](docs/spadi-user-daq-guide.md) | [spadi-devel-daq](docs/spadi-devel-daq-guide.md) |
| ARTEMIS | [spadi-user-artemis](docs/spadi-user-artemis-guide.md) | [spadi-devel-artemis](docs/spadi-devel-artemis-guide.md) |
| Everything | [spadi-user-full](docs/spadi-user-full-guide.md) | [spadi-devel-full](docs/spadi-devel-full-guide.md) |

`DAQ = FEE + NestDAQ`; `FULL = DAQ + ARTEMIS`.

## Quick start

These examples use the NestDAQ user image (spadi-user-daq).

### Apptainer (Linux / Windows WSL2)

Install Apptainer on 64 bit Linux (x86_64), including a Linux distribution running in Windows WSL2, then run the following commands in the Linux terminal.

```bash
curl -fL -O \
  https://github.com/nobukoba/spadi-containers-second-trial/releases/download/latest/spadi-user-daq.sif
mkdir -p "$PWD/workspace"
apptainer shell --cleanenv --bind "$PWD/workspace:/workspace" \
  --shell /opt/spadi/spadi-shell.sh spadi-user-daq.sif
```

### Docker (macOS / Linux)

Install and start Docker on macOS or Linux, then run the following commands.

```bash
docker pull --platform linux/amd64 \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-user-daq:latest

mkdir -p "$PWD/workspace"

docker run --rm -it \
  --platform linux/amd64 \
  -e LOCAL_UID="$(id -u)" \
  -e LOCAL_GID="$(id -g)" \
  -v "$PWD/workspace:/workspace" \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-user-daq:latest
```

Both load the SPADI environment and enter `/workspace`, the working directory inside the container, automatically. The container’s `/workspace` is mounted from the host’s `workspace` directory, so files saved there persist on the host. For another image, replace `spadi-user-daq` in the URLs and commands with a name from the table.

## Leave and reopen the container

Run `exit` inside either container to return to the host. Repeat the corresponding shell/run command from the same host directory to reuse `workspace`. Download or pull again only when you want to update the image. Keep your work under `/workspace`; changes elsewhere in a disposable Docker container are not persistent.

## Apptainer details

The Quick start uses `--cleanenv` to avoid inheriting host software environment settings. SPADI runtime settings are defined inside the container so the environment does not depend on the host software configuration:

```bash
apptainer shell --cleanenv --bind "$PWD/workspace:/workspace" \
  --shell /opt/spadi/spadi-shell.sh spadi-user-daq.sif
```

The `--shell` script sources `/opt/spadi/spadi-setup.sh` and enters `/workspace`. Keep `--shell`: plain `apptainer shell` skips Bash startup files. The SIF is read-only. Apptainer uses your host UID/GID, so `LOCAL_UID` and `LOCAL_GID` are unnecessary.

For another image, replace `spadi-user-daq` in the download URL and startup command with a name from the table. Automatic startup requires a newly built SIF containing this change.

## Docker details

The images target `linux/amd64`, so the same commands can be used on both Apple Silicon macOS and amd64 Linux. On an amd64 Linux host, `--platform linux/amd64` is optional and may be omitted. `LOCAL_UID` and `LOCAL_GID` make the container's `spadi` user use the host user's numeric UID/GID, so files created in the bind-mounted `/workspace` remain owned by the host user. The container username remains `spadi` on both macOS and Linux.

The bind-mounted `/workspace` is persistent. Files edited below `/workspace/spadi` remain after the container exits or is replaced.

Docker also loads the SPADI environment and enters `/workspace` automatically.

### Container networking

Apptainer normally shares the host network regardless of the image type. Docker shares the host network when started with `--network host`, regardless of the image type. Port publishing with `-p` is unnecessary in host network mode. The following example uses `spadi-user-daq`; replace the image name to use another image.

```bash
docker run --rm -it --platform linux/amd64 --network host \
  -e LOCAL_UID="$(id -u)" -e LOCAL_GID="$(id -g)" \
  -v "$PWD/workspace:/workspace" \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-user-daq:latest
```

The general macOS Docker example is intended for analysis and software use. To publish browser control from bridge networking, combine recipe WEBCTL_HOST=0.0.0.0 with -p 127.0.0.1:8081:8081 (8080 for RARiS). Verify hardware reachability separately.

## Image versions

Docker images are published at `ghcr.io/nobukoba/spadi-containers-second-trial/<image-name>` with `latest` and UTC build tags in `YYYYMMDD-HHMMutc` format. SIF files are available from [GitHub Releases](https://github.com/nobukoba/spadi-containers-second-trial/releases/tag/latest), with both stable filenames such as `spadi-user-daq.sif` and timestamped filenames.

`latest` can change. For a repeatable environment, retain the selected timestamped SIF or record the Docker image digest. Pinned component revisions are listed in [versions/versions.env](versions/versions.env); the current repository manifest may differ from an older downloaded image.

Images containing the version reporter can identify themselves from inside the container:

```bash
/opt/spadi/scripts/spadi-version.sh
```

The reporter reads `/opt/spadi/versions/container.env` and `/opt/spadi/versions/versions.env`. Older images published before this metadata was added may not contain these files or the reporter.

## Common directory structure

```text
/opt/spadi/                  # SPADI_ROOT: image-provided installation
├── bin/
├── lib/, lib64/
├── include/, share/        # include: devel and ROOT/ARTEMIS images
├── scripts/
├── versions/
└── src/                    # development images only

/workspace/                 # bind-mounted host workspace/
└── spadi/                   # SPADI_LOCAL
    ├── scripts/
    ├── rawdata/
    ├── analysis/           # created by analysis procedures
    ├── bin/, lib/, lib64/  # prepared in development workspaces
    ├── include/, share/        # include: devel and ROOT/ARTEMIS images
    ├── src/
    └── build/
```

This is the layout policy shared by all eight images. Available components and preparation stages determine which directories exist. Each image guide also shows its own relevant directory layout.

## About the SPADI_LOCAL environment variable

SPADI_LOCAL is an environment variable containing the path for editable configuration, sources, local builds, and acquired or analyzed data. Startup sets it automatically; its default is /workspace/spadi. SPADI_ROOT identifies the image-provided /opt/spadi installation.

| Variable | Default |
|---|---|
| `SPADI_ROOT` | `/opt/spadi` |
| `SPADI_LOCAL` | `/workspace/spadi` |

```bash
echo "$SPADI_ROOT"
echo "$SPADI_LOCAL"
```

The shell expands $ to the variable value: $SPADI_LOCAL/scripts defaults to /workspace/spadi/scripts. Setting the environment does not create directories. The bind mount maps container /workspace/spadi to workspace/spadi in the host launch directory; those files persist after exit.

Local bin, lib, lib64, CMake, and pkg-config paths precede the image installation. Use $SPADI_LOCAL for normal development rather than modifying /opt/spadi.

## Prepare the workspace

After entering either a user or devel container, run:

```bash
spadi-prepare-local.sh
```

The command creates `scripts` and `rawdata` under `$SPADI_LOCAL` (default: `/workspace/spadi`) and copies the scripts for components included in the image into `scripts`.

In devel images, it additionally copies sources into `src`, creates `build`, `bin`, `lib`, `lib64`, `include`, and `share`, and copies build and latest-source clone helpers into `scripts`. It does not build software.

Existing files and source directories are not overwritten. Running the command again adds only missing content.

## Update the image and workspace

To update an image, download the SIF again or pull the Docker image on the host, then start a container with the new image. Configuration, sources, and data saved in the host `workspace` remain.

Updating the image and updating scripts or sources already copied into the workspace are separate operations. Running `spadi-prepare-local.sh` in the new image does not replace existing copies. If an update is needed, stop the affected processes, back up edited files, compare the new files under `$SPADI_ROOT` with the copies under `$SPADI_LOCAL`, and apply the required changes.

See the image guides below for component-specific operations.

## Image guides

| Family | user | devel |
|---|---|---|
| FEE | [spadi-user-fee](docs/spadi-user-fee-guide.md) | [spadi-devel-fee](docs/spadi-devel-fee-guide.md) |
| DAQ | [spadi-user-daq](docs/spadi-user-daq-guide.md) | [spadi-devel-daq](docs/spadi-devel-daq-guide.md) |
| ARTEMIS | [spadi-user-artemis](docs/spadi-user-artemis-guide.md) | [spadi-devel-artemis](docs/spadi-devel-artemis-guide.md) |
| FULL | [spadi-user-full](docs/spadi-user-full-guide.md) | [spadi-devel-full](docs/spadi-devel-full-guide.md) |

For container implementation, CI, and publication, see the [container maintainer guide](docs/container-maintainer-guide.md).
