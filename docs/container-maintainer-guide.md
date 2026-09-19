# Container Maintainer Guide

This page is for developers who maintain the SPADI container images themselves.

It is intentionally separate from the workflow for researchers and software developers who use a pre-built `spadi-devel-*` Docker/SIF image to edit and self-build SPADI software. That user-side development workflow belongs in the main README.

## Scope

Container maintainers work on:

- Dockerfiles and image composition
- pinned upstream versions in `versions/versions.env`
- GitHub Actions, GHCR publishing, and SIF generation
- Docker and Apptainer smoke tests
- image tags and releases
- compatibility and dependency maintenance

Building Docker or SIF images is not part of the normal container-user self-build workflow.

## Image matrix

The repository maintains eight images:

- `spadi-user-fee` and `spadi-devel-fee`
- `spadi-user-daq` and `spadi-devel-daq`
- `spadi-user-artemis` and `spadi-devel-artemis`
- `spadi-user-full` and `spadi-devel-full`

DAQ contains FEE + NestDAQ. FULL contains DAQ + ARTEMIS.

## Validation pipeline

Container changes are validated in this order:

```text
Build Docker image
    ↓
Test Docker image
    ↓
Create Apptainer SIF
    ↓
Test SIF with --cleanenv
    ↓
Publish
```

A successful Docker build alone is not sufficient validation.

## Version policy

`versions/versions.env` is the source of truth for pinned upstream revisions. Prefer suitable official stable release tags; otherwise use an exact commit SHA. Do not silently replace a pin with a moving `main`, `master`, or development branch.

User and devel images in the same family must use the same revisions.

ARTEMIS upstream uses the moving `develop` branch. Published containers do not build directly from that moving branch: `ARTEMIS_REF` records a selected exact commit SHA from `develop`. To update ARTEMIS, choose the intended `develop` commit, update `ARTEMIS_REF`, then rebuild and validate the affected images.

The GitHub Actions workflow sources `versions/versions.env` and passes those values as Docker build arguments. Dockerfile `ARG` values are fallback defaults for direct/manual builds; CI must not maintain an independent version list. When a pinned dependency changes, update `versions/versions.env` first.

### Container release version and embedded metadata

The SPADI container release version is the Git tag, for example `v0.1.0`. A release tag must map to the corresponding GHCR image tags for all eight images; released version tags are immutable and must not be overwritten. Keep `latest` only as a convenience pointer, and retain UTC/CI tags for traceability.

Every image must also be self-describing. The container contains:

- `/opt/spadi/versions/versions.env`: pinned component versions and commit SHAs
- `/opt/spadi/versions/container.env`: SPADI container version, repository Git commit, and image target
- `/opt/spadi/scripts/spadi-version.sh`: human-readable version reporter

Inside Docker or SIF, run:

```bash
source /opt/spadi/spadi-setup.sh
spadi-version.sh
```

This metadata must survive into both user and devel images. Docker and Apptainer smoke tests must verify it so an old standalone SIF can identify its exact container release and component revisions without consulting GitHub.

## AlmaLinux 9 runtime policy

AlmaLinux 9 is the container OS baseline. Use its supported runtime packages where practical. In particular, DAQ uses the AlmaLinux 9 `valkey` package as the Redis-compatible service instead of forcing an historical Redis server package solely to match old upstream documentation. Keep NestDAQ-facing client/build libraries pinned independently, and keep RedisTimeSeries pinned as an explicit module dependency for `TS.*` metrics commands.

## Build cost and CI

ROOT and ARTEMIS builds are expensive. Documentation-only changes and host-only helper changes must not trigger those builds. Keep expensive compiled layers cacheable when changing lightweight image-resident scripts.

The push workflow should keep the eight targets independently startable and parallelizable. Do not make one target consume a mutable sibling `:latest` image as a build prerequisite.

When diagnosing Actions failures, inspect the failed job/step and a small relevant log tail first. Do not download or process a complete long ROOT/ARTEMIS/FULL log unless the focused output is insufficient.

## Repository structure

```text
spadi-containers-second-trial/
├── README.md
├── AGENTS.md
├── docs/
│   └── container-maintainer-guide.md
├── versions/
│   └── versions.env
├── containers/
│   ├── fee/
│   ├── daq/
│   ├── artemis/
│   └── full/
├── scripts/
└── .github/
    └── workflows/
```

Before changing implementation details, read `AGENTS.md`; it is the repository's persistent engineering knowledge base.
