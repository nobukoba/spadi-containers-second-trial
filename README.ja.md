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

NestDAQ 開発イメージ (spadi-devel-daq) を使用する例です。

### Apptainer（64 bit Linux / Windows WSL2）

64 bit Linux (x86_64) に Apptainer をインストールしてから、以下のコマンドを実行してください。Windows WSL2 の Linux ディストリビューションも利用できます。コマンドは Linux 側の端末で実行してください。

```bash
curl -fL -O \
  https://github.com/nobukoba/spadi-containers-second-trial/releases/download/latest/spadi-devel-daq.sif
mkdir -p "$PWD/workspace"
apptainer shell --cleanenv --bind "$PWD/workspace:/workspace" \
  --shell /opt/spadi/spadi-shell.sh spadi-devel-daq.sif
```

### Docker（macOS / Linux）

macOS または Linux に Docker をインストールし、起動してから、以下のコマンドを実行してください。

```bash
docker pull --platform linux/amd64 \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-daq:latest

mkdir -p "$PWD/workspace"

docker run --rm -it \
  --platform linux/amd64 \
  -e LOCAL_UID="$(id -u)" \
  -e LOCAL_GID="$(id -g)" \
  -v "$PWD/workspace:/workspace" \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-daq:latest
```

どちらも SPADI 環境の読み込みと、コンテナ内の作業ディレクトリ `/workspace` への移動は自動です。コンテナ内の `/workspace` はホストの `workspace` ディレクトリに接続されているため、ここに置いた作業ファイルはホスト側に保存されます。別のイメージを使用するには、URL とコマンドの `spadi-devel-daq` を上の表の名前に置き換えてください。

## コンテナの終了と再起動

どちらのコンテナでも `exit` を実行するとホストに戻ります。同じホストディレクトリから対応する shell/run コマンドを再実行すれば、同じ `workspace` を再利用できます。イメージを更新したい場合だけ再度 download または pull してください。作業ファイルは `/workspace` 以下に置いてください。使い捨ての Docker コンテナ内でそれ以外の場所に加えた変更は永続化されません。

## Apptainer の詳細

Quick start の `--cleanenv` は、ホストのソフトウェア環境変数の影響を避けるために付けています。SPADI の実行環境はコンテナ側で定義し、ホストのソフトウェア設定に依存させません：

```bash
apptainer shell --cleanenv --bind "$PWD/workspace:/workspace" \
  --shell /opt/spadi/spadi-shell.sh spadi-devel-daq.sif
```

`--shell` で指定した起動スクリプトが `/opt/spadi/spadi-setup.sh` を読み込み、`/workspace` に移動します。通常の `apptainer shell` は Bash の起動設定を読み込まないため、`--shell` を省略しないでください。SIF は読み取り専用で、Apptainer はホストユーザーの UID/GID を使用するため `LOCAL_UID` と `LOCAL_GID` は不要です。

イメージを変えるには、ダウンロード URL と起動コマンドの `spadi-devel-daq` を上の表の名前に置き換えてください。自動起動には、この変更を含む新しい SIF が必要です。

## Docker の詳細

イメージは `linux/amd64` 向けなので、Apple Silicon macOS と amd64 Linux のどちらでも同じコマンドを使用できます。amd64 Linux ホストでは `--platform linux/amd64` は省略できます。`LOCAL_UID` と `LOCAL_GID` により、コンテナ内の `spadi` ユーザーはホストユーザーと同じ数値 UID/GID を使用するため、bind mount した `/workspace` 内に作成したファイルの所有者をホストユーザーのままにできます。macOS、Linux のどちらでもコンテナ内のユーザー名は `spadi` です。

bind mount された `/workspace` は永続化されます。`/workspace/spadi` 以下で編集したファイルは、コンテナを終了または入れ替えても残ります。

Docker でも SPADI 環境の読み込みと `/workspace` への移動は自動です。

## イメージのバージョン

Docker イメージは `ghcr.io/nobukoba/spadi-containers-second-trial/<image-name>` に公開され、`latest` と UTC ビルド時刻を表す `YYYYMMDD-HHMMutc` 形式のタグが付与されます。SIF ファイルは [GitHub Releases](https://github.com/nobukoba/spadi-containers-second-trial/releases/tag/latest) から取得でき、`spadi-devel-daq.sif` のような固定ファイル名とタイムスタンプ付きファイル名の両方を提供します。

`latest` は更新される可能性があります。再現可能な環境が必要な場合は、選択したタイムスタンプ付き SIF を保存するか、Docker イメージの digest を記録してください。固定された各コンポーネントのリビジョンは [versions/versions.env](versions/versions.env) に記載されています。現在のリポジトリの manifest は、以前ダウンロードしたイメージとは異なる場合があります。

バージョン表示機能を含むイメージでは、コンテナ内から自身のバージョン情報を確認できます：

```bash
/opt/spadi/scripts/spadi-version.sh
```

このスクリプトは `/opt/spadi/versions/container.env` と `/opt/spadi/versions/versions.env` を読み込みます。このメタデータが追加される以前に公開された古いイメージには、これらのファイルやバージョン表示スクリプトが含まれていない場合があります。

## ユーザー向け

インストール済みソフトウェアを実行する場合は、ビルド済みの `spadi-user-*` を使用します。FEE 制御には `spadi-user-fee`、`spadi-user-daq`、`spadi-user-full` を使用できます。NestDAQ は DAQ / FULL、ARTEMIS は ARTEMIS / FULL に含まれます。

### AMANEQ の LR-TDC を1チャンネルだけ読み出す

まずはスタンドアロンの Str-LRTDC を使い、IP **192.168.10.16** の AMANEQ で **チャンネル102だけを unmask**、残りの入力（0〜127）をすべて mask する例です。Linux または Windows WSL2 の Linux 端末で FEE の user イメージを取得し、起動します：

```bash
curl -fL -O \
  https://github.com/nobukoba/spadi-containers-second-trial/releases/download/latest/spadi-user-fee.sif
mkdir -p "$PWD/workspace"
apptainer shell --cleanenv --bind "$PWD/workspace:/workspace" \
  --shell /opt/spadi/spadi-shell.sh spadi-user-fee.sif
```

コンテナ内で FEE 設定スクリプトを永続領域にコピーします。既存のコピーは上書きしません：

```bash
mkdir -p "$SPADI_LOCAL/scripts/fee"
if [ ! -e "$SPADI_LOCAL/scripts/fee/amaneq-lrtdc-1ch" ]; then
  cp -a /opt/spadi/scripts/fee/amaneq-lrtdc-1ch "$SPADI_LOCAL/scripts/fee/"
fi
cd "$SPADI_LOCAL/scripts/fee/amaneq-lrtdc-1ch"
ping -c 3 192.168.10.16
bash setup.sh
```

IP とマスク値は `config.sh` にまとめています。`setup.sh` は Main-U、Main-D、MZN-U、MZN-D に順に `ffffffff ffffffff ffffffff ffffffbf` を設定し、読み戻して一致を確認します。番号は0始まりで、102は MZN-D の bit 6（102 − 96）です。1が mask、0が unmask なので、最後の値だけ `0xffffffbf` にします。TDC 入力のマスクであり、スケーラーのカウントやハートビートデリミタは止まりません。

1台で試す場合は DIP3 = 1（スタンドアロン）、DIP1 = 0（デフォルト IP）にして、下側 DCRv2 メザニンのチャンネル102へ信号を接続してください。ホストには同じネットワークのアドレス（例：`192.168.10.1/24`）を設定し、UDP 4660 と TCP 24 で接続できるようにします。WSL2 でも Linux 側から AMANEQ に到達できることを確認してください。

マスクの確認に成功したら、短時間の読み出しを実行します：

```bash
mkdir -p "$SPADI_LOCAL/rawdata/amaneq-lrtdc-1ch/data"
cd "$SPADI_LOCAL/rawdata/amaneq-lrtdc-1ch"
test ! -e data/run1.dat && strdaq 192.168.10.16 1
# Ctrl-C で停止し、End of DAQ を待ってから保存ファイルを確認します。
ls -lh data/run1.dat
```

保存先はホスト側に残る `/workspace/spadi/rawdata/amaneq-lrtdc-1ch/data/run1.dat` です。次の取得では run 番号を変えてください。スタンドアロンでは TCP 接続でデータ送信が始まるので、`set_hbfstate` は不要です。現在固定している `strdaq` はメモリに蓄積し、停止時にファイルへ書く簡易試験用なので、短時間にとどめてください。継続的な取得には NestDAQ を使います。入力信号がなくてもデリミタが記録されるため、ファイルサイズだけでは102のヒットを確認できません。

詳細は [FEE 設定・読み出しガイド](scripts/fee/amaneq-lrtdc-1ch/README.md) を参照してください。この手順には新しいスクリプトを含むイメージが必要です。user イメージでは開発用の `spadi-prepare-local.sh` やコンパイルは不要です。

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

Docker/SIF イメージのビルドと、devel イメージ内での SPADI ソフトウェアの再ビルドは意図的に分離しています。コンテナ実装、CI、検証、公開、バージョン管理の手順は [docs/container-maintainer-guide.md](docs/container-maintainer-guide.md) に記載しています。
