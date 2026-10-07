# SPADI ソフトウェアの開発者向けガイド

**Language: [English](developer-guide.md) | 日本語**

このページは、**ビルド済みの `spadi-devel-*` イメージを使って SPADI ソフトウェアを開発する人**向けです。Dockerfile、GitHub Actions、SIF 生成、イメージ公開方法そのものを変更する場合は、[Container Maintainer Guide](container-maintainer-guide.md) を参照してください。

## 開発イメージの起動

Apptainer は 64 bit Linux (x86_64) または Windows WSL2 の Linux にインストールし、Linux 側の端末で実行します。

```bash
curl -fL -O \
  https://github.com/nobukoba/spadi-containers-second-trial/releases/download/latest/spadi-devel-daq.sif
mkdir -p "$PWD/workspace"
apptainer shell --cleanenv --bind "$PWD/workspace:/workspace" \
  --shell /opt/spadi/spadi-shell.sh spadi-devel-daq.sif
```

Docker は macOS / Linux で起動してから実行してください。

```bash
docker pull --platform linux/amd64 \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-daq:latest
mkdir -p "$PWD/workspace"
docker run --rm -it --platform linux/amd64 \
  -e LOCAL_UID="$(id -u)" -e LOCAL_GID="$(id -g)" \
  -v "$PWD/workspace:/workspace" \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-daq:latest
```

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
spadi-prepare-local.sh
```

`spadi-prepare-local.sh` はローカルのディレクトリ構造を作成し、利用可能なソースツリーと編集可能なビルドスクリプトを `/opt/spadi` から `/workspace/spadi` にコピーします。

何度実行しても安全です。`$SPADI_LOCAL` 以下に既に存在するファイルやディレクトリは保持され、prepare スクリプトによって上書きされません。そのため `$SPADI_LOCAL/src` や `$SPADI_LOCAL/scripts` に加えた変更は、再度 prepare を実行しても残ります。

### 実行設定

AMANEQ の NestDAQ 実機読み出しと RARiS の再生は[ユーザー向けガイド](user-guide.ja.md)を参照してください。実行用ヘルパーは user / devel イメージ共通です。

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

DAQ イメージは AlmaLinux 9 runtime を使用します。適切な部分では NestDAQ `v1.0.0` のビルド依存関係を基準としつつ、Redis 互換の runtime service には AlmaLinux 9 の `valkey` パッケージを使用します。RedisTimeSeries は NestDAQ の `TS.*` metrics コマンドで使用する独立した固定バージョンのモジュールとして維持します。過去の Redis パッケージ版を動かすためだけに古い Linux distribution を再現することはしません。

| コンポーネント | この環境でのバージョン | NestDAQ v1.0.0 の要件／基準 |
|---|---:|---:|
| NestDAQ | `v1.0.0` | 公式 stable release |
| nestdaq-user-impl | `47897e9` | 検証済み最新 upstream commit (2026-10-03) |
| FairMQ | `v1.4.55` | `1.4.26` 以降 |
| hiredis | `v1.0.0` | `1.0.0` |
| redis-plus-plus | `1.3.15` | 検証済みの新しい release。LockCatcher `SIGABRT` に関連した古い redis-plus-plus 構成を回避 |
| libzmq | `v4.3.5` | コンテナで固定した依存パッケージ |

上記の `nestdaq-user-impl` の固定値は、2026-10-03 に現在の NestDAQ user implementation をデバッグした後に更新しました。更新され続ける `main` branch を追従するのではなく、動作確認した正確な commit をコンテナに記録することで、後から同じ動作環境を再現できるようにしています。

上記の redis-plus-plus の違いは意図的なものです。NestDAQ v1.0.0 のソースは `<sw/redis++/patterns/redlock.h>` を include していますが、依存関係表には古い `recipes` branch の名称が残っています。現在の NestDAQ のデバッグでは古い client 構成で LockCatcher `SIGABRT` が発生したため、このコンテナでは redis-plus-plus 1.3.15 に固定しています。runtime で古いライブラリが混在しないよう、redis-plus-plus と hiredis は単一の `/opt/spadi` prefix に配置します。`nestdaq-user-impl` も変化する `main` branch ではなく、2026-10-03 に検証した正確な commit に固定しています。リポジトリ全体の正確な固定バージョンは `versions/versions.env` で管理します。`main` のように更新される branch は通常のコンテナ基準には使用しません。ARTEMIS の upstream 開発は `develop` で行われますが、コンテナでは `ARTEMIS_REF` により検証済みの特定 `develop` commit を記録してビルドするため、upstream branch の更新によってイメージが意図せず変化することはありません。

### コンテナメンテナ向け

Docker/SIF イメージのビルドと、devel イメージ内での SPADI ソフトウェアの再ビルドは意図的に分離しています。コンテナ実装、CI、検証、公開、バージョン管理の手順は [docs/container-maintainer-guide.md](container-maintainer-guide.md) に記載しています。
