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

ホスト側のソフトウェア環境設定を引き継がないように `--cleanenv` を使用します。SIF は読み取り専用のままで、`/workspace` に書き込んだファイルはホスト側の `workspace` ディレクトリに保存されます。Apptainer ではホストのユーザー ID がそのまま使われるため、Docker 用の `LOCAL_UID` と `LOCAL_GID` の指定は不要です。

別のイメージを使用する場合は、ダウンロード URL と SIF ファイル名の `spadi-devel-daq` を上のイメージ表にある名前に置き換えてください。例えば通常の FEE 操作では次のようにします：

```bash
curl -fL -O \
  https://github.com/nobukoba/spadi-containers-second-trial/releases/download/latest/spadi-user-fee.sif

mkdir -p "$PWD/workspace"

apptainer shell --cleanenv \
  --bind "$PWD/workspace:/workspace" \
  spadi-user-fee.sif
```

その後、コンテナ内で同じ環境設定コマンドを実行します。

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

イメージは `linux/amd64` 向けなので、Apple Silicon macOS と amd64 Linux のどちらでも同じコマンドを使用できます。amd64 Linux ホストでは `--platform linux/amd64` は省略できます。`LOCAL_UID` と `LOCAL_GID` により、コンテナ内の `spadi` ユーザーはホストユーザーと同じ数値 UID/GID を使用するため、bind mount した `/workspace` 内に作成したファイルの所有者をホストユーザーのままにできます。macOS、Linux のどちらでもコンテナ内のユーザー名は `spadi` です。

bind mount された `/workspace` は永続化されます。`/workspace/spadi` 以下で編集したファイルは、コンテナを終了または入れ替えても残ります。

Docker コンテナ内で SPADI 環境を読み込み、workspace に移動します：

```bash
source /opt/spadi/spadi-setup.sh
cd /workspace
```

別のイメージを使用する場合は、2つの Docker コマンド内の `spadi-devel-daq` をイメージ表にある名前に置き換えてください。

## コンテナの終了と再起動

どちらのコンテナでも `exit` を実行するとホストに戻ります。同じホストディレクトリから対応する shell/run コマンドを再実行すれば、同じ `workspace` を再利用できます。イメージを更新したい場合だけ再度 download または pull してください。作業ファイルは `/workspace` 以下に置いてください。使い捨ての Docker コンテナ内でそれ以外の場所に加えた変更は永続化されません。

## イメージのバージョン

Docker イメージは `ghcr.io/nobukoba/spadi-containers-second-trial/<image-name>` に公開され、`latest` と UTC ビルド時刻を表す `YYYYMMDD-HHMMutc` 形式のタグが付与されます。SIF ファイルは [GitHub Releases](https://github.com/nobukoba/spadi-containers-second-trial/releases/tag/latest) から取得でき、`spadi-devel-daq.sif` のような固定ファイル名とタイムスタンプ付きファイル名の両方を提供します。

`latest` は更新される可能性があります。再現可能な環境が必要な場合は、選択したタイムスタンプ付き SIF を保存するか、Docker イメージの digest を記録してください。固定された各コンポーネントのリビジョンは [versions/versions.env](versions/versions.env) に記載されています。現在のリポジトリの manifest は、以前ダウンロードしたイメージとは異なる場合があります。

バージョン表示機能を含むイメージでは、コンテナ内から自身のバージョン情報を確認できます：

```bash
source /opt/spadi/spadi-setup.sh
/opt/spadi/scripts/spadi-version.sh
```

このスクリプトは `/opt/spadi/versions/container.env` と `/opt/spadi/versions/versions.env` を読み込みます。このメタデータが追加される以前に公開された古いイメージには、これらのファイルやバージョン表示スクリプトが含まれていない場合があります。

## 開発者向け

この節は、**ビルド済みの `spadi-devel-*` イメージを使って SPADI ソフトウェアを開発する人**向けです。Dockerfile、GitHub Actions、SIF 生成、イメージ公開方法そのものを変更する場合は、[Container Maintainer Guide](docs/container-maintainer-guide.md) を参照してください。

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

Development イメージには `/opt/spadi/src` 以下にソースツリーが保持されます。User イメージでは通常これらを含めず、開発用ヘルパーも提供しません。

`/opt/spadi` は検証済みのコンテナ基準環境です。通常の開発ではここを直接編集しないでください。ソースファイル、ビルドツリー、スクリプト、ローカルにインストールするソフトウェアは `/workspace/spadi` 以下に置きます。

### 永続的な開発 workspace の準備

上記いずれかの方法で `spadi-devel-*` コンテナを起動します。コンテナ内で次のコマンドを実行し、環境を読み込んでローカル開発領域を準備します：

```bash
source /opt/spadi/spadi-setup.sh
spadi-prepare-local.sh
```

`spadi-prepare-local.sh` はローカルのディレクトリ構造を作成し、利用可能なソースツリーと編集可能なビルドスクリプトを `/opt/spadi` から `/workspace/spadi` にコピーします。

何度実行しても安全です。`$SPADI_LOCAL` 以下に既に存在するファイルやディレクトリは保持され、prepare スクリプトによって上書きされません。そのため `$SPADI_LOCAL/src` や `$SPADI_LOCAL/scripts` に加えた変更は、再度 prepare を実行しても残ります。

### NestDAQ リプレイ用レシピ

DAQ イメージには `/opt/spadi/scripts/nestdaq` 以下に編集可能な NestDAQ レシピが用意されています。`spadi-prepare-local.sh` 実行後は、そのコピーが `$SPADI_LOCAL/scripts/nestdaq` 以下に配置されます。

RARiS AC-LGAD データをリプレイする場合：

```bash
cd "$SPADI_LOCAL/scripts/nestdaq/raris-ac-lgad"
./rawdata-download.sh
./run-start.sh
./run-status.sh
./run-attach.sh
# Ctrl-b d で tmux から detach
./run-stop.sh
```

プロセス数、raw data のパス、ポート、run parameter など通常の設定変更は `config.sh` のみを編集します。共通の Redis/Valkey、topology、parameter、tmux、download 処理は `scripts/nestdaq/common` 以下にあります。

Raw data は `$SPADI_LOCAL/rawdata`（通常は `/workspace/spadi/rawdata`）に保存されるため、bind した workspace とともに永続化されます。ダウンローダーは curl の転送進捗を表示し、途中までダウンロードしたファイルは再開できます。初期の RARiS レシピでは既存の公開参照データ URL を使用しています。共有 Drive のファイル ID が確定したら、manifest の該当項目を公開 Google Drive の直接ダウンロード URL に置き換えられます。

build ディレクトリはローカルの作業領域です。例えば再ビルド前に NestDAQ の build tree だけを削除する場合：

```bash
rm -rf "$SPADI_LOCAL/build/nestdaq"
```

これにより、編集済みソース `$SPADI_LOCAL/src/nestdaq` はそのまま保持されます。

### 検索パスの優先順位

`spadi-setup.sh` はローカルインストールを検証済みインストールより先に検索するよう設定します。特に `$SPADI_LOCAL/bin` と `$SPADI_LOCAL/scripts` は、それぞれ `$SPADI_ROOT` 側より優先されます。

ソースは `/workspace/spadi/src`（ホスト側では `workspace/spadi/src`）以下を編集します。編集可能なヘルパースクリプトは `/workspace/spadi/scripts` にあり、環境を読み込んだ後はどのディレクトリからでも実行できます。

上記の NestDAQ development イメージでは、NestDAQ、続いて user implementation を次のように再ビルドします：

```bash
nestdaq-build.sh
nestdaq-user-impl-build.sh
```

他のコンポーネントにもそれぞれビルド用ヘルパーがあります。再ビルドしたいコンポーネントのものだけを実行してください：

| ビルド用ヘルパー | 対応する Development イメージ |
|---|---|
| `hul-common-lib-build.sh` | FEE, DAQ, FULL |
| `amaneq-build.sh` | FEE, DAQ, FULL |
| `openfpgaloader-build.sh` | FEE, DAQ, FULL |
| `sitcp-utility-build.sh` | FEE, DAQ, FULL |
| `nestdaq-build.sh` | DAQ, FULL |
| `nestdaq-user-impl-build.sh` | DAQ, FULL |
| `artemis-build.sh` | ARTEMIS, FULL |

各ビルドでは `$SPADI_LOCAL/src` 以下のソースを使用し、独立した build tree を `$SPADI_LOCAL/build` 以下に作成して、`$SPADI_LOCAL` にインストールします。検証済みの `/opt/spadi` は変更されません。

意図的に upstream の最新版を試す場合も、clone と build は分離します。clone 用ヘルパーは既存のソースツリーを上書きしません：

```bash
# 本当に置き換える場合は、既存のローカルソースを先に自分で
# 削除またはリネームしてください。
nestdaq-clone-latest.sh
nestdaq-build.sh
```

同じ方式を FEE コンポーネント（`hul-common-lib`、AMANEQ、openFPGALoader、SiTCP utility）、`nestdaq-user-impl`、ARTEMIS にも利用できます。build スクリプト内部に暗黙の `--latest` モードはありません。

次を実行すると：

```bash
spadi-env.sh
```

実際に有効になっているパスを確認できます。

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
