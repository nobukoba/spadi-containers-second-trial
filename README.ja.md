# SPADI Containers — Second Trial

**Language: [English](README.md) | 日本語**

SPADI FEE、NestDAQ、ARTEMIS ソフトウェア用のビルド済み Docker/OCI および Apptainer SIF 環境です。

イメージは `linux/amd64` 向けです。通常利用には `spadi-user-*`、コンテナ内で SPADI ソフトウェアを編集・再ビルドする場合には `spadi-devel-*` を使用します。

## イメージ

| 用途 | User イメージ | Development イメージ |
|---|---|---|
| FEE 制御 | `spadi-user-fee` | `spadi-devel-fee` |
| NestDAQ | `spadi-user-daq` | `spadi-devel-daq` |
| ARTEMIS | `spadi-user-artemis` | `spadi-devel-artemis` |
| 全部入り | `spadi-user-full` | `spadi-devel-full` |

`DAQ = FEE + NestDAQ`; `FULL = DAQ + ARTEMIS`.

## Apptainer

Apptainer がインストールされた x86-64 Linux ホストを使用します。以下では NestDAQ development イメージを例にします。macOS では後述の Docker を使用してください。

ホスト上でビルド済み SIF をダウンロードします：

```bash
curl -fL -O \
  https://github.com/nobukoba/spadi-containers-second-trial/releases/download/latest/spadi-devel-daq.sif
```

永続化する workspace を作成してシェルを開きます：

```bash
mkdir -p "$PWD/workspace"

apptainer shell --cleanenv \
  --bind "$PWD/workspace:/workspace" \
  spadi-devel-daq.sif
```

コンテナ内で SPADI 環境を読み込み、workspace に移動します：

```bash
source /opt/spadi/spadi-setup.sh
cd /workspace
```

Use `--cleanenv` to avoid inheriting host software settings. The SIF remains read-only; files written under `/workspace` are saved in the host's `workspace` directory. Apptainer uses your host user identity, so the Docker-specific `LOCAL_UID` and `LOCAL_GID` options are not needed.

For another image, replace `spadi-devel-daq` in both the download URL and SIF filename with any name in the image table. For example, normal FEE operation uses:

```bash
curl -fL -O \
  https://github.com/nobukoba/spadi-containers-second-trial/releases/download/latest/spadi-user-fee.sif

mkdir -p "$PWD/workspace"

apptainer shell --cleanenv \
  --bind "$PWD/workspace:/workspace" \
  spadi-user-fee.sif
```

Then run the same environment setup commands inside that container.

## Docker

NestDAQ development イメージを使用する例です：

イメージを pull します：

```bash
docker pull --platform linux/amd64 \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-daq:latest
```

必要に応じて永続化する workspace を作成し、コンテナを起動します：

```bash
mkdir -p "$PWD/workspace"

docker run --rm -it \
  --platform linux/amd64 \
  -e LOCAL_UID="$(id -u)" \
  -e LOCAL_GID="$(id -g)" \
  -v "$PWD/workspace:/workspace" \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-daq:latest
```

The images target `linux/amd64`, so the same commands can be used on both Apple Silicon macOS and amd64 Linux. On an amd64 Linux host, `--platform linux/amd64` is optional and may be omitted. `LOCAL_UID` and `LOCAL_GID` make the container's `spadi` user use the host user's numeric UID/GID, so files created in the bind-mounted `/workspace` remain owned by the host user. The container username remains `spadi` on both macOS and Linux.

The bind-mounted `/workspace` is persistent. Files edited below `/workspace/spadi` remain after the container exits or is replaced.

Inside the Docker container, load the environment and enter the workspace:

```bash
source /opt/spadi/spadi-setup.sh
cd /workspace
```

To use another image, replace `spadi-devel-daq` in both Docker commands with its name from the image table.

## コンテナの終了と再起動

Run `exit` inside either container to return to the host. Repeat the corresponding shell/run command from the same host directory to reuse `workspace`. Download or pull again only when you want to update the image. Keep your work under `/workspace`; changes elsewhere in a disposable Docker container are not persistent.

## イメージのバージョン

Docker images are published at `ghcr.io/nobukoba/spadi-containers-second-trial/<image-name>` with `latest` and UTC build tags in `YYYYMMDD-HHMMutc` format. SIF files are available from [GitHub Releases](https://github.com/nobukoba/spadi-containers-second-trial/releases/tag/latest), with both stable filenames such as `spadi-devel-daq.sif` and timestamped filenames.

`latest` can change. For a repeatable environment, retain the selected timestamped SIF or record the Docker image digest. Pinned component revisions are listed in [versions/versions.env](versions/versions.env); the current repository manifest may differ from an older downloaded image.

Images containing the version reporter can identify themselves from inside the container:

```bash
source /opt/spadi/spadi-setup.sh
/opt/spadi/scripts/spadi-version.sh
```

The reporter reads `/opt/spadi/versions/container.env` and `/opt/spadi/versions/versions.env`. Older images published before this metadata was added may not contain these files or the reporter.

## 開発者向け

This section is for developers who **use a pre-built `spadi-devel-*` image to develop SPADI software**. Developers who modify Dockerfiles, GitHub Actions, SIF generation, or image publishing should instead read [Container Maintainer Guide](docs/container-maintainer-guide.md).

### 検証済みインストールとローカル開発領域

コンテナが提供する検証済みインストールは：

```text
SPADI_ROOT=/opt/spadi
```

書き込み可能な開発用インストール先は：

```text
SPADI_LOCAL=/workspace/spadi
```

想定するディレクトリ構成は：

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

### 永続的な開発 workspace の準備

Start a `spadi-devel-*` container using either method above. Run the following commands inside the container to load the environment and prepare the local area:

```bash
source /opt/spadi/spadi-setup.sh
spadi-prepare-local.sh
```

`spadi-prepare-local.sh` creates the local directory structure and copies available source trees and editable build scripts from `/opt/spadi` into `/workspace/spadi`.

It is safe to run repeatedly. Existing files and directories under `$SPADI_LOCAL` are kept and are never overwritten by the prepare script. Therefore edits made in `$SPADI_LOCAL/src` or `$SPADI_LOCAL/scripts` survive another prepare operation.

### NestDAQ リプレイ用レシピ

The DAQ images provide editable NestDAQ recipes under `/opt/spadi/scripts/nestdaq`. After `spadi-prepare-local.sh`, the user copies live under `$SPADI_LOCAL/scripts/nestdaq`.

For the RARiS AC-LGAD replay:

```bash
cd "$SPADI_LOCAL/scripts/nestdaq/raris-ac-lgad"
./rawdata-download.sh
./run-start.sh
./run-status.sh
./run-attach.sh
# Ctrl-b d detaches from tmux
./run-stop.sh
```

Edit only `config.sh` for normal changes such as process counts, raw-data paths, ports, and run parameters. Shared Redis/Valkey, topology, parameter, tmux, and download logic lives under `scripts/nestdaq/common`.

Raw data is stored under `$SPADI_LOCAL/rawdata` (normally `/workspace/spadi/rawdata`) so it persists with the bound workspace. The downloader shows curl transfer progress and resumes partial files. The initial RARiS recipe uses the existing public reference data URLs; those manifest entries can be replaced with public Google Drive direct-download URLs once the shared-drive file IDs are finalized.

The build directory is local scratch space. For example, to discard only the NestDAQ build tree before rebuilding:

```bash
rm -rf "$SPADI_LOCAL/build/nestdaq"
```

This keeps the edited source under `$SPADI_LOCAL/src/nestdaq`.

### 検索パスの優先順位

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

### NestDAQ ベースライン

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

### コンテナメンテナ向け

Building Docker/SIF images is intentionally separate from rebuilding SPADI software inside a devel image. Container implementation, CI, validation, publishing, and version-maintenance procedures are documented in [docs/container-maintainer-guide.md](docs/container-maintainer-guide.md).

## 環境の分離

SPADI runtime settings are defined by the container and should not depend on software environment variables inherited from the host. Published binaries target generic x86-64 rather than `-march=native`/AVX-specific runner hardware.
