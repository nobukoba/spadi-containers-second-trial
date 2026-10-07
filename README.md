# SPADI Containers — Second Trial

**Language: English | [日本語](README.ja.md)**

Pre-built Docker and Apptainer SIF environments for SPADI Front End Electronics (FEE), NestDAQ, and ARTEMIS software.

The images target `linux/amd64`. Use `spadi-user-*` for normal operation and `spadi-devel-*` when you want to edit and rebuild SPADI software inside the container.

## Image types

| Purpose | User image | Development image |
|---|---|---|
| FEE control | `spadi-user-fee` | `spadi-devel-fee` |
| NestDAQ | `spadi-user-daq` | `spadi-devel-daq` |
| ARTEMIS | `spadi-user-artemis` | `spadi-devel-artemis` |
| Everything | `spadi-user-full` | `spadi-devel-full` |

`DAQ = FEE + NestDAQ`; `FULL = DAQ + ARTEMIS`.

## Quick start

These examples use the NestDAQ user image (spadi-user-daq).

### Apptainer (64 bit Linux / Windows WSL2)

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

## Image versions

Docker images are published at `ghcr.io/nobukoba/spadi-containers-second-trial/<image-name>` with `latest` and UTC build tags in `YYYYMMDD-HHMMutc` format. SIF files are available from [GitHub Releases](https://github.com/nobukoba/spadi-containers-second-trial/releases/tag/latest), with both stable filenames such as `spadi-user-daq.sif` and timestamped filenames.

`latest` can change. For a repeatable environment, retain the selected timestamped SIF or record the Docker image digest. Pinned component revisions are listed in [versions/versions.env](versions/versions.env); the current repository manifest may differ from an older downloaded image.

Images containing the version reporter can identify themselves from inside the container:

```bash
/opt/spadi/scripts/spadi-version.sh
```

The reporter reads `/opt/spadi/versions/container.env` and `/opt/spadi/versions/versions.env`. Older images published before this metadata was added may not contain these files or the reporter.

## Guides

- [User guide](docs/user-guide.md): installed software, AMANEQ single-channel NestDAQ acquisition, RARiS replay, runtime helpers, and directory structure.
- [Developer guide](docs/developer-guide.md): pre-built devel images, editable source trees, build helpers, and the local installation prefix.
- [Container Maintainer Guide](docs/container-maintainer-guide.md): Dockerfiles, CI, and image publication.
