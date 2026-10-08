# spadi-user-artemis ガイド

**Language: [English](spadi-user-artemis-guide.md) | 日本語**

ROOT と ARTEMIS による解析を行うイメージです。

## ディレクトリ構造

```text
/opt/spadi/                         # SPADI_ROOT
├── bin/
├── lib/
├── lib64/
├── include/
├── share/
├── versions/
└── scripts/
│   ├── spadi-prepare-local.sh
│   └── artemis/

/workspace/spadi/                   # SPADI_LOCAL → host workspace/spadi
├── scripts/
│   └── artemis/
├── analysis/example/{macro,output}/
└── rawdata/
```

`/opt/spadi` はイメージが提供し、`/workspace/spadi` はホストに保存される作業領域です。 `spadi-prepare-local.sh` が scripts と rawdata を作成します。user イメージには `/opt/spadi/src` はありません。 analysis ディレクトリは後述の mkdir で作成します。

環境変数 `SPADI_LOCAL` の既定値は `/workspace/spadi`、`SPADI_ROOT` は `/opt/spadi` です。起動時に設定されます。環境変数の設定だけではディレクトリは作られません。ホストの `workspace/spadi` と対応します。詳細は [README の共通手順](../README.ja.md)を参照してください。

## イメージのダウンロードと起動

以下のコマンドはホストの端末で実行します。Apptainer または Docker のどちらかを選んでください。

### Apptainer（Linux / Windows WSL2）

```bash
curl -fL -O \
  https://github.com/nobukoba/spadi-containers-second-trial/releases/download/latest/spadi-user-artemis.sif
mkdir -p "$PWD/workspace"
apptainer shell --cleanenv --bind "$PWD/workspace:/workspace" \
  --shell /opt/spadi/spadi-shell.sh spadi-user-artemis.sif
```

### Docker（macOS / Linux）

```bash
docker pull --platform linux/amd64 \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-user-artemis:latest
mkdir -p "$PWD/workspace"
docker run --rm -it \
  --platform linux/amd64 \
  -e LOCAL_UID="$(id -u)" -e LOCAL_GID="$(id -g)" \
  -v "$PWD/workspace:/workspace" \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-user-artemis:latest
```

作業ファイルはホストの `workspace` に保存されます。イメージを更新する場合は再ダウンロードまたは再 pull してください。

## 作業領域を準備する

このイメージに含まれるランタイム用スクリプトをコピーします。 既存の設定やソースは上書きしません。準備ヘルパーの共通仕様と更新方法は [README](../README.ja.md) を参照してください。

```bash
spadi-prepare-local.sh
```

## ROOT と ARTEMIS を起動する

ROOT / ARTEMIS の環境は起動時に読み込まれます。バージョンと実行ファイルを確認します。

```bash
root-config --version
command -v root
command -v artemis
mkdir -p "$SPADI_LOCAL/analysis/example/macro" "$SPADI_LOCAL/analysis/example/output"
cd "$SPADI_LOCAL/analysis/example"
```

解析用ディレクトリは上の `mkdir` が作ります。`spadi-prepare-local.sh` は利用可能な ARTEMIS スクリプトと `rawdata` を準備しますが、実験用 steering、較正値、入力データを自動生成しません。

画面表示を使わずに ROOT の動作と ROOT ファイルの保存を確認します。

```bash
root -b -q -e 'TFile f("output/example.root", "RECREATE"); TH1D h("example", "Example", 100, 0, 100); h.Fill(42); h.Write(); f.Close();'
ls -lh output/example.root
```

結果はホストの `workspace/spadi/analysis/example/output/example.root` に残ります。この例は人工的なヒストグラムであり、実験データのデコードではありません。

対話的な ROOT と ARTEMIS は次のように起動します。それぞれのプロンプトで `.q` を入力すると終了します。

```bash
root -l
# Enter .q before running the next command.
artemis
```

ヒストグラムをウィンドウ表示する場合は別途ディスプレイ接続が必要ですが、上のバッチ例は xterm / X11 を使用しません。取得のブラウザ操作は DAQ / FULL に含まれる Web Controller の機能です。ARTEMIS 自体の操作は端末または解析マクロで行います。

## 実験の解析を進める

使用する実験の steering、processor、較正ファイル、マクロを `$SPADI_LOCAL/analysis` 以下の作業ディレクトリへ配置し、そこから ARTEMIS を起動します。入力データは `$SPADI_LOCAL/rawdata`、出力の ROOT ファイルは解析作業ディレクトリの `output` に置くとホストに保存されます。実験側のライブラリ読み込みや解析実行コマンドは、その実験の手順に従ってください。

NestDAQ FileSink の `.dat` は TF/STF を含む形式です。ROOT に直接開かせるのではなく、対応する入力 processor とデコーダ、steering が必要です。このリポジトリには AMANEQ 1チャンネル用の完成した ARTEMIS steering はありません。[ARTEMIS 公式 README](https://github.com/artemis-dev/artemis/tree/develop)も参照してください。

## Appendix: 含まれるソフトウェア

以下はイメージに含まれる主要ソフトウェアです。固定バージョン・リビジョンの定義は [versions.env](../versions/versions.env) にあります。使用中のイメージの情報は、コンテナ内の `/opt/spadi/scripts/spadi-version.sh` と `/opt/spadi/versions/versions.env` で確認できます。ローカルで再ビルドしたソフトウェアはこの一覧の固定版とは別です。

| ソフトウェア | 用途 | 固定版・リビジョン |
|---|---|---|
| [ROOT](https://github.com/root-project/root) | 解析、ヒストグラム、TTree、Cling | [`v6-32-06`](https://github.com/root-project/root/tree/v6-32-06) |
| [ARTEMIS](https://github.com/artemis-dev/artemis) | 原子核実験用解析フレームワーク | [`c74e24adf90a`](https://github.com/artemis-dev/artemis/tree/c74e24adf90a83227fa3e5c38dc255ddc4aeb785) |
| [yaml-cpp](https://github.com/jbeder/yaml-cpp) | YAML 設定の読み込み | [`0.8.0`](https://github.com/jbeder/yaml-cpp/tree/0.8.0) |
| [ZeroMQ](https://github.com/zeromq/libzmq) | メッセージ通信ライブラリ | [`v4.3.5`](https://github.com/zeromq/libzmq/tree/v4.3.5) |
| [hiredis](https://github.com/redis/hiredis) | Redis/Valkey C クライアント | [`v1.0.0`](https://github.com/redis/hiredis/tree/v1.0.0) |
| [redis-plus-plus](https://github.com/sewenew/redis-plus-plus) | Redis/Valkey C++ クライアント | [`1.3.15`](https://github.com/sewenew/redis-plus-plus/tree/1.3.15) |

OS は AlmaLinux 9 です。tmux、vim / emacs、基本的なファイル・プロセス操作ツールも含みます。OS パッケージは AlmaLinux のパッケージ版で、上表のソース固定版とは管理方法が異なります。

ROOT は TMVA、X11 / OpenGL、SQLite、SSL を有効にし、PyROOT、RooFit、Web GUI は無効にしています。ARTEMIS の GET は無効、ZeroMQ / Redis 対応は有効です。OpenMPI と圧縮ライブラリも含みます。

`spadi-user-*` は実行用です。ソースとローカル開発用ビルドヘルパーは含みません。 ROOT / Cling の実行に必要な C++ コンパイラとヘッダーは含みます。
