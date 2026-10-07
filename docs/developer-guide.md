# SPADI software developer guide

**Language: English | [日本語](developer-guide.ja.md)**

This page is for developers who **use a pre-built `spadi-devel-*` image to develop SPADI software**. Developers who modify Dockerfiles, GitHub Actions, SIF generation, or image publishing should instead read [Container Maintainer Guide](container-maintainer-guide.md).

## Start a development image

Apptainer: install on 64 bit Linux (x86_64), including Windows WSL2. Run in the Linux terminal.

```bash
curl -fL -O \
  https://github.com/nobukoba/spadi-containers-second-trial/releases/download/latest/spadi-devel-daq.sif
mkdir -p "$PWD/workspace"
apptainer shell --cleanenv --bind "$PWD/workspace:/workspace" \
  --shell /opt/spadi/spadi-shell.sh spadi-devel-daq.sif
```

Docker: macOS / Linux.

```bash
docker pull --platform linux/amd64 \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-daq:latest
mkdir -p "$PWD/workspace"
docker run --rm -it --platform linux/amd64 \
  -e LOCAL_UID="$(id -u)" -e LOCAL_GID="$(id -g)" \
  -v "$PWD/workspace:/workspace" \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-daq:latest
```

### Validated installation and local development area

The container-provided installation is:

```text
SPADI_ROOT=/opt/spadi
```

Your writable development installation is:

```text
SPADI_LOCAL=/workspace/spadi
```

The intended layout is:

```text
/opt/spadi/                    /workspace/spadi/
├── bin/                       ├── bin/
├── lib/                       ├── lib/
├── lib64/                     ├── lib64/
├── include/                   ├── include/
├── share/                     ├── share/
├── scripts/                   ├── scripts/
│   ├── nestdaq/               │   ├── nestdaq/
│   ├── fee/                   │   ├── fee/
│   └── artemis/               │   └── artemis/
└── src/                       ├── src/
                               ├── build/
                               └── rawdata/
```

Development images retain source trees under `/opt/spadi/src`; user images normally omit them and do not provide the development helpers.

`/opt/spadi` is the validated container baseline. Do not edit it for normal development. Source files, build trees, scripts, and locally installed software belong under `/workspace/spadi`.

### Prepare a persistent development workspace

Start a `spadi-devel-*` container using either method above. Run the following command inside the container to prepare the local area:

```bash
spadi-prepare-local.sh
```

`spadi-prepare-local.sh` creates the local directory structure and copies available source trees and editable build scripts from `/opt/spadi` into `/workspace/spadi`.

It is safe to run repeatedly. Existing files and directories under `$SPADI_LOCAL` are kept and are never overwritten by the prepare script. Therefore edits made in `$SPADI_LOCAL/src` or `$SPADI_LOCAL/scripts` survive another prepare operation.

### Runtime recipes

For AMANEQ live acquisition and RARiS replay, see the [user guide](user-guide.md). Runtime helpers are shared by user and development images.

The build directory is local scratch space. For example, to discard only the NestDAQ build tree before rebuilding:

```bash
rm -rf "$SPADI_LOCAL/build/nestdaq"
```

This keeps the edited source under `$SPADI_LOCAL/src/nestdaq`.

### Search-path precedence

`spadi-setup.sh` places the local installation before the validated installation. In particular, `$SPADI_LOCAL/bin` and `$SPADI_LOCAL/scripts` take precedence over their `$SPADI_ROOT` counterparts.

Edit the sources under `/workspace/spadi/src` (the host's `workspace/spadi/src`). Editable helper scripts live under `/workspace/spadi/scripts` and can be invoked from any directory once the environment is loaded.

For the NestDAQ development image used above, rebuild NestDAQ and then its user implementation:

```bash
nestdaq-build.sh
nestdaq-user-impl-build.sh
```

Other components have their own helpers. Run only the helpers for the components you want to rebuild:

| Build helper | Development images |
|---|---|
| `hul-common-lib-build.sh` | FEE, DAQ, FULL |
| `amaneq-build.sh` | FEE, DAQ, FULL |
| `openfpgaloader-build.sh` | FEE, DAQ, FULL |
| `sitcp-utility-build.sh` | FEE, DAQ, FULL |
| `nestdaq-build.sh` | DAQ, FULL |
| `nestdaq-user-impl-build.sh` | DAQ, FULL |
| `artemis-build.sh` | ARTEMIS, FULL |

Each build uses the source under `$SPADI_LOCAL/src`, a separate build tree under `$SPADI_LOCAL/build`, and installs into `$SPADI_LOCAL`. The validated `/opt/spadi` installation is not modified.

To deliberately try the latest upstream source, keep cloning separate from building. The clone helpers refuse to overwrite an existing source tree:

```bash
# Remove or rename the existing local source yourself first if you really
# intend to replace it.
nestdaq-clone-latest.sh
nestdaq-build.sh
```

The same pattern is available for FEE components (`hul-common-lib`, AMANEQ, openFPGALoader, and the SiTCP utility), `nestdaq-user-impl`, and ARTEMIS. There is no `--latest` mode hidden inside the build script.

Use:

```bash
spadi-env.sh
```

to inspect the effective paths.

### NestDAQ baseline

The DAQ image uses an AlmaLinux 9 runtime. It follows the NestDAQ `v1.0.0` build-dependency baseline where appropriate, while the Redis-compatible runtime service is the AlmaLinux 9 `valkey` package. RedisTimeSeries remains a separately pinned module used for NestDAQ `TS.*` metrics commands; the container does not attempt to reproduce an old Linux distribution merely to run the historical Redis package version.

| Component | Version used here | NestDAQ v1.0.0 requirement/baseline |
|---|---:|---:|
| NestDAQ | `v1.0.0` | official stable release |
| nestdaq-user-impl | `47897e9` | latest tested upstream commit (2026-10-03) |
| FairMQ | `v1.4.55` | `1.4.26` or later |
| hiredis | `v1.0.0` | `1.0.0` |
| redis-plus-plus | `1.3.15` | newer tested release; avoids the older redis-plus-plus setup associated with LockCatcher `SIGABRT` |
| libzmq | `v4.3.5` | pinned container dependency |

The `nestdaq-user-impl` pin above was updated after debugging the current NestDAQ user implementation on 2026-10-03. Rather than following the moving `main` branch, the container records the exact tested commit so the working setup can be reproduced later.

The redis-plus-plus difference above is intentional: NestDAQ v1.0.0 source includes `<sw/redis++/patterns/redlock.h>`, while its dependency table still reflects the older `recipes`-branch naming. The container now pins redis-plus-plus 1.3.15 because the older client setup triggered LockCatcher `SIGABRT` during current NestDAQ debugging. The image keeps redis-plus-plus and hiredis in the single `/opt/spadi` prefix to avoid mixing older libraries at runtime. `nestdaq-user-impl` is pinned to the exact tested 2026-10-03 commit rather than a moving `main` branch. The exact repository-wide pins are maintained in `versions/versions.env`. Moving branches such as `main` are not used as the normal container baseline. ARTEMIS upstream development occurs on `develop`; the container records and builds a specific tested `develop` commit via `ARTEMIS_REF`, so an upstream branch update does not silently change the image.

### Container maintainers

Building Docker/SIF images is intentionally separate from rebuilding SPADI software inside a devel image. Container implementation, CI, validation, publishing, and version-maintenance procedures are documented in [docs/container-maintainer-guide.md](container-maintainer-guide.md).
