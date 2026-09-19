# SPADI Containers — Second Trial

Pre-built Docker/OCI and Apptainer SIF environments for SPADI FEE, NestDAQ, and ARTEMIS software.

The images target `linux/amd64`. Use `spadi-user-*` for normal operation and `spadi-devel-*` when you want to edit and rebuild SPADI software inside the container.

## Images

| Purpose | User image | Development image |
|---|---|---|
| FEE control | `spadi-user-fee` | `spadi-devel-fee` |
| NestDAQ | `spadi-user-daq` | `spadi-devel-daq` |
| ARTEMIS | `spadi-user-artemis` | `spadi-devel-artemis` |
| Everything | `spadi-user-full` | `spadi-devel-full` |

`DAQ = FEE + NestDAQ`; `FULL = DAQ + ARTEMIS`.

## Docker

For example, to use the NestDAQ development image on x86-64 Linux:

```bash
docker pull ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-daq:latest

mkdir -p "$PWD/workspace"

docker run --rm -it \
  -v "$PWD/workspace:/workspace" \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-daq:latest
```

On Apple Silicon, explicitly select the x86-64 image:

```bash
docker pull --platform linux/amd64 \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-daq:latest

docker run --rm -it \
  --platform linux/amd64 \
  -v "$PWD/workspace:/workspace" \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-daq:latest
```

The bind-mounted `/workspace` is persistent. Files edited below `/workspace/spadi` remain after the container exits or is replaced.

## Apptainer

SIF images use the same eight image names. Run them with a writable host directory bound to `/workspace`; the SIF itself can remain read-only.

`--cleanenv` is recommended so the SPADI environment does not accidentally depend on host software settings.

## For Developers

This section is for developers who **use a pre-built `spadi-devel-*` image to develop SPADI software**. Developers who modify Dockerfiles, GitHub Actions, SIF generation, or image publishing should instead read [Container Maintainer Guide](docs/container-maintainer-guide.md).

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
├── include/                   ├── include/
├── share/                     ├── share/
├── scripts/                   ├── scripts/
└── src/                       ├── src/
                               └── build/
```

`/opt/spadi` is the validated container baseline. Do not edit it for normal development. Source files, build trees, scripts, and locally installed software belong under `/workspace/spadi`.

### Prepare a persistent development workspace

Load the environment and prepare the local area:

```bash
source /opt/spadi/spadi-setup.sh
spadi-prepare-local.sh
```

`spadi-prepare-local.sh` creates the local directory structure and copies available source trees and editable build scripts from `/opt/spadi` into `/workspace/spadi`.

It is safe to run repeatedly. Existing files and directories under `$SPADI_LOCAL` are kept and are never overwritten by the prepare script. Therefore edits made in `$SPADI_LOCAL/src` or `$SPADI_LOCAL/scripts` survive another prepare operation.

The build directory is local scratch space:

```bash
rm -rf "$SPADI_LOCAL/build/<project>"
```

can be used to discard a build tree without deleting the edited source.

### Search-path precedence

`spadi-setup.sh` places the local installation before the validated installation. In particular, `$SPADI_LOCAL/bin` and `$SPADI_LOCAL/scripts` take precedence over their `$SPADI_ROOT` counterparts.

This means editable helper scripts can be invoked from any directory once the environment is loaded. For example:

```bash
hul-common-lib-build.sh
amaneq-build.sh
openfpgaloader-build.sh
sitcp-utility-build.sh
nestdaq-build.sh
nestdaq-user-impl-build.sh
artemis-build.sh
```

Each build uses the source under `$SPADI_LOCAL/src`, a separate build tree under `$SPADI_LOCAL/build`, and installs into `$SPADI_LOCAL`. The validated `/opt/spadi` installation is not modified.

To deliberately try the latest upstream source, keep cloning separate from building. The clone helpers refuse to overwrite an existing source tree:

```bash
# Remove or rename the existing local source yourself first if you really
# intend to replace it.
nestdaq-clone-latest.sh
nestdaq-build.sh
```

The same pattern is available for `nestdaq-user-impl` and ARTEMIS. There is no `--latest` mode hidden inside the build script.

Use:

```bash
spadi-env.sh
```

to inspect the effective paths.

### NestDAQ baseline

The DAQ image intentionally follows the dependency baseline documented by the official NestDAQ `v1.0.0` release where NestDAQ specifies exact versions.

| Component | Version used here | NestDAQ v1.0.0 requirement/baseline |
|---|---:|---:|
| NestDAQ | `v1.0.0` | official stable release |
| nestdaq-user-impl | `v1.0.0` | matching official stable release |
| FairMQ | `v1.4.55` | `1.4.26` or later |
| hiredis | `v1.0.0` | `1.0.0` |
| redis-plus-plus | `1.2.1` | `1.2.1` |
| libzmq | `v4.3.5` | pinned container dependency |

The exact repository-wide pins are maintained in `versions/versions.env`. Moving branches such as `main` are not used as the normal NestDAQ container baseline. ARTEMIS upstream development occurs on `develop`; the container records and builds a specific tested `develop` commit via `ARTEMIS_REF`, so an upstream branch update does not silently change the image.

### Container maintainers

Building Docker/SIF images is intentionally separate from rebuilding SPADI software inside a devel image. Container implementation, CI, validation, publishing, and version-maintenance procedures are documented in [docs/container-maintainer-guide.md](docs/container-maintainer-guide.md).

## Environment isolation

SPADI runtime settings are defined by the container and should not depend on software environment variables inherited from the host. Published binaries target generic x86-64 rather than `-march=native`/AVX-specific runner hardware.
