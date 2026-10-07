# SPADI Containers — Second Trial

**Language: [English](README.md) | 日本語**

SPADI Front End Electronics (FEE)、NestDAQ、ARTEMIS ソフトウェア用のビルド済み Docker および Apptainer SIF 環境です。

イメージは `linux/amd64` 向けです。通常利用には `spadi-user-*`、コンテナ内で SPADI ソフトウェアを編集・再ビルドする場合には `spadi-devel-*` を使用します。

## イメージの種類

| 用途 | User イメージ | Development イメージ |
|---|---|---|
| FEE 制御 | `spadi-user-fee` | `spadi-devel-fee` |
| NestDAQ | `spadi-user-daq` | `spadi-devel-daq` |
| ARTEMIS | `spadi-user-artemis` | `spadi-devel-artemis` |
| 全部入り | `spadi-user-full` | `spadi-devel-full` |

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

## イメージのバージョン

Docker イメージは `ghcr.io/nobukoba/spadi-containers-second-trial/<image-name>` に公開され、`latest` と UTC ビルド時刻を表す `YYYYMMDD-HHMMutc` 形式のタグが付与されます。SIF ファイルは [GitHub Releases](https://github.com/nobukoba/spadi-containers-second-trial/releases/tag/latest) から取得でき、`spadi-user-daq.sif` のような固定ファイル名とタイムスタンプ付きファイル名の両方を提供します。

`latest` は更新される可能性があります。再現可能な環境が必要な場合は、選択したタイムスタンプ付き SIF を保存するか、Docker イメージの digest を記録してください。固定された各コンポーネントのリビジョンは [versions/versions.env](versions/versions.env) に記載されています。現在のリポジトリの manifest は、以前ダウンロードしたイメージとは異なる場合があります。

バージョン表示機能を含むイメージでは、コンテナ内から自身のバージョン情報を確認できます：

```bash
/opt/spadi/scripts/spadi-version.sh
```

このスクリプトは `/opt/spadi/versions/container.env` と `/opt/spadi/versions/versions.env` を読み込みます。このメタデータが追加される以前に公開された古いイメージには、これらのファイルやバージョン表示スクリプトが含まれていない場合があります。

## ガイド

- [ユーザー向けガイド](docs/user-guide.ja.md)：AMANEQ 1チャンネルの NestDAQ 読み出し、RARiS 再生、実行用ヘルパー、ディレクトリ構造。
- [開発者向けガイド](docs/developer-guide.ja.md)：devel イメージ、ソース編集、ビルド用ヘルパー、ローカルインストール。
- [Container Maintainer Guide](docs/container-maintainer-guide.md)：Dockerfile、CI、イメージ公開。
