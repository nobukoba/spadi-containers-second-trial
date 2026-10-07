# SPADI Containers — Second Trial

**Language: [English](README.md) | 日本語**

SPADI Front End Electronics (FEE)、NestDAQ、ARTEMIS ソフトウェア用のビルド済み Docker および Apptainer SIF 環境です。

イメージは `linux/amd64` 向けです。通常利用には `spadi-user-*`、コンテナ内で SPADI ソフトウェアを編集・再ビルドする場合には `spadi-devel-*` を使用します。

## イメージの種類

| 用途 | User イメージ | Development イメージ |
|---|---|---|
| FEE 制御 | [spadi-user-fee](docs/spadi-user-fee-guide.ja.md) | [spadi-devel-fee](docs/spadi-devel-fee-guide.ja.md) |
| NestDAQ | [spadi-user-daq](docs/spadi-user-daq-guide.ja.md) | [spadi-devel-daq](docs/spadi-devel-daq-guide.ja.md) |
| ARTEMIS | [spadi-user-artemis](docs/spadi-user-artemis-guide.ja.md) | [spadi-devel-artemis](docs/spadi-devel-artemis-guide.ja.md) |
| 全部入り | [spadi-user-full](docs/spadi-user-full-guide.ja.md) | [spadi-devel-full](docs/spadi-devel-full-guide.ja.md) |

`DAQ = FEE + NestDAQ`; `FULL = DAQ + ARTEMIS`.

## Quick start

NestDAQ ユーザーイメージ (spadi-user-daq) を使用する例です。

### Apptainer（64 bit Linux / Windows WSL2）

64 bit Linux (x86_64) に Apptainer をインストールしてから、以下のコマンドを実行してください。Windows WSL2 の Linux ディストリビューションも利用できます。コマンドは Linux 側の端末で実行してください。

```bash
curl -fL -O \
  https://github.com/nobukoba/spadi-containers-second-trial/releases/download/latest/spadi-user-daq.sif
mkdir -p "$PWD/workspace"
apptainer shell --cleanenv --bind "$PWD/workspace:/workspace" \
  --shell /opt/spadi/spadi-shell.sh spadi-user-daq.sif
```

### Docker（macOS / Linux）

macOS または Linux に Docker をインストールし、起動してから、以下のコマンドを実行してください。

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

どちらも SPADI 環境の読み込みと、コンテナ内の作業ディレクトリ `/workspace` への移動は自動です。コンテナ内の `/workspace` はホストの `workspace` ディレクトリに接続されているため、ここに置いた作業ファイルはホスト側に保存されます。別のイメージを使用するには、URL とコマンドの `spadi-user-daq` を上の表の名前に置き換えてください。

## コンテナの終了と再起動

どちらのコンテナでも `exit` を実行するとホストに戻ります。同じホストディレクトリから対応する shell/run コマンドを再実行すれば、同じ `workspace` を再利用できます。イメージを更新したい場合だけ再度 download または pull してください。作業ファイルは `/workspace` 以下に置いてください。使い捨ての Docker コンテナ内でそれ以外の場所に加えた変更は永続化されません。

## Apptainer の詳細

Quick start の `--cleanenv` は、ホストのソフトウェア環境変数の影響を避けるために付けています。SPADI の実行環境はコンテナ側で定義し、ホストのソフトウェア設定に依存させません：

```bash
apptainer shell --cleanenv --bind "$PWD/workspace:/workspace" \
  --shell /opt/spadi/spadi-shell.sh spadi-user-daq.sif
```

`--shell` で指定した起動スクリプトが `/opt/spadi/spadi-setup.sh` を読み込み、`/workspace` に移動します。通常の `apptainer shell` は Bash の起動設定を読み込まないため、`--shell` を省略しないでください。SIF は読み取り専用で、Apptainer はホストユーザーの UID/GID を使用するため `LOCAL_UID` と `LOCAL_GID` は不要です。

イメージを変えるには、ダウンロード URL と起動コマンドの `spadi-user-daq` を上の表の名前に置き換えてください。自動起動には、この変更を含む新しい SIF が必要です。

## Docker の詳細

イメージは `linux/amd64` 向けなので、Apple Silicon macOS と amd64 Linux のどちらでも同じコマンドを使用できます。amd64 Linux ホストでは `--platform linux/amd64` は省略できます。`LOCAL_UID` と `LOCAL_GID` により、コンテナ内の `spadi` ユーザーはホストユーザーと同じ数値 UID/GID を使用するため、bind mount した `/workspace` 内に作成したファイルの所有者をホストユーザーのままにできます。macOS、Linux のどちらでもコンテナ内のユーザー名は `spadi` です。

bind mount された `/workspace` は永続化されます。`/workspace/spadi` 以下で編集したファイルは、コンテナを終了または入れ替えても残ります。

Docker でも SPADI 環境の読み込みと `/workspace` への移動は自動です。

### DAQ / FULL で使用するネットワーク

Linux の Docker で実機取得や既定の Web Controller を使う場合は、次の host network で起動します。FULL や devel を使う場合はイメージ名を該当する名前に変更します。

```bash
docker run --rm -it --platform linux/amd64 --network host \
  -e LOCAL_UID="$(id -u)" -e LOCAL_GID="$(id -g)" \
  -v "$PWD/workspace:/workspace" \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-user-daq:latest
```

macOS の一般 Docker 起動例は解析・ソフトウェア利用向けです。ブラウザ用ポートを publish する場合は、レシピの `WEBCTL_HOST=0.0.0.0` と起動時の `-p 127.0.0.1:8081:8081`（RARiS は8080）を組み合わせます。実機への到達性は別途確認してください。

## イメージのバージョン

Docker イメージは `ghcr.io/nobukoba/spadi-containers-second-trial/<image-name>` に公開され、`latest` と UTC ビルド時刻を表す `YYYYMMDD-HHMMutc` 形式のタグが付与されます。SIF ファイルは [GitHub Releases](https://github.com/nobukoba/spadi-containers-second-trial/releases/tag/latest) から取得でき、`spadi-user-daq.sif` のような固定ファイル名とタイムスタンプ付きファイル名の両方を提供します。

`latest` は更新される可能性があります。再現可能な環境が必要な場合は、選択したタイムスタンプ付き SIF を保存するか、Docker イメージの digest を記録してください。固定された各コンポーネントのリビジョンは [versions/versions.env](versions/versions.env) に記載されています。現在のリポジトリの manifest は、以前ダウンロードしたイメージとは異なる場合があります。

バージョン表示機能を含むイメージでは、コンテナ内から自身のバージョン情報を確認できます：

```bash
/opt/spadi/scripts/spadi-version.sh
```

このスクリプトは `/opt/spadi/versions/container.env` と `/opt/spadi/versions/versions.env` を読み込みます。このメタデータが追加される以前に公開された古いイメージには、これらのファイルやバージョン表示スクリプトが含まれていない場合があります。

## 共通のディレクトリ構造

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

これは8イメージ共通の配置方針です。コンポーネントと作成段階によって存在するディレクトリは異なります。各イメージのガイドにも、そのイメージで使うディレクトリ構造を掲載しています。

## 環境変数 SPADI_LOCAL について

環境変数 `SPADI_LOCAL` は、ユーザーが編集する設定、ソース、ビルド結果、取得・解析データを置く作業領域のパスです。起動時に自動設定され、既定値は `/workspace/spadi` です。`SPADI_ROOT` はイメージが提供する `/opt/spadi` を指します。

| Variable | Default |
|---|---|
| `SPADI_ROOT` | `/opt/spadi` |
| `SPADI_LOCAL` | `/workspace/spadi` |

```bash
echo "$SPADI_ROOT"
echo "$SPADI_LOCAL"
```

`$` はシェルに環境変数の値を展開させる記号です。`$SPADI_LOCAL/scripts` は既定値では `/workspace/spadi/scripts` になります。環境の設定だけではディレクトリは作成されません。起動コマンドの bind mount により、コンテナの `/workspace/spadi` は起動元のホストディレクトリの `workspace/spadi` に対応し、終了後も残ります。

ローカルの `bin`、`lib`、`lib64`、CMake / pkg-config の検索パスはイメージ側より優先されます。通常の開発では `/opt/spadi` を編集せず、`$SPADI_LOCAL` 以下を使います。

## 共通の準備と更新

| 操作 | 作成されるもの |
|---|---|
| `コンテナ起動` | 環境変数の設定のみ。作業領域は未作成 |
| `spadi-prepare-runtime.sh` | 利用可能なコンポーネントの scripts と rawdata。user / devel 共通 |
| `spadi-prepare-local.sh` | ソース、build、ローカルインストール先、ヘルパー。devel のみ |
| `AMANEQ run-start.sh` | rawdata/amaneq-lrtdc-1ch/00。デバイスは Idle 待機 |
| `ブラウザの FileSink Run` | 00/run000001.dat などの run ファイル |
| `ARTEMIS ガイドの mkdir / ROOT 例` | analysis ディレクトリ / ROOT 出力 |

コンテナ内で、ランタイム用には以下を実行します。

```bash
spadi-prepare-runtime.sh
```

ソースを編集する devel イメージでは、以下を実行します。

```bash
spadi-prepare-local.sh
```

両ヘルパーとも既存ファイルを上書きしません。新しいイメージを取得しただけでは、作業領域にある古いヘルパーは更新されません。使用中のセッションを停止し、既存のスクリプトを別名で保存してから再準備し、変更を比較してください。編集済みの `config.sh` は保持します。特に NestDAQ の `common`、run ヘルパー、FEE の `setup.sh` を一緒に確認し、古い自動 Run の手順を混在させないでください。

## イメージ別ガイド

| イメージ | ガイド |
|---|---|
| `spadi-user-fee` | [ガイド](docs/spadi-user-fee-guide.ja.md) |
| `spadi-devel-fee` | [ガイド](docs/spadi-devel-fee-guide.ja.md) |
| `spadi-user-daq` | [ガイド](docs/spadi-user-daq-guide.ja.md) |
| `spadi-devel-daq` | [ガイド](docs/spadi-devel-daq-guide.ja.md) |
| `spadi-user-artemis` | [ガイド](docs/spadi-user-artemis-guide.ja.md) |
| `spadi-devel-artemis` | [ガイド](docs/spadi-devel-artemis-guide.ja.md) |
| `spadi-user-full` | [ガイド](docs/spadi-user-full-guide.ja.md) |
| `spadi-devel-full` | [ガイド](docs/spadi-devel-full-guide.ja.md) |

コンテナの実装・CI・公開は [コンテナ保守ガイド](docs/container-maintainer-guide.md)を参照してください。
