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
│   ├── spadi-prepare-runtime.sh
│   └── artemis/

/workspace/spadi/                   # SPADI_LOCAL → host workspace/spadi
├── scripts/
│   └── artemis/
├── analysis/example/{macro,output}/
└── rawdata/
```

`/opt/spadi` はイメージが提供し、`/workspace/spadi` はホストに保存される作業領域です。 `spadi-prepare-runtime.sh` が scripts と rawdata を作成します。user イメージには `/opt/spadi/src` はありません。 analysis ディレクトリは後述の mkdir で作成します。

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
spadi-prepare-runtime.sh
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

解析用ディレクトリは上の `mkdir` が作ります。`spadi-prepare-runtime.sh` は利用可能な ARTEMIS スクリプトと `rawdata` を準備しますが、実験用 steering、較正値、入力データを自動生成しません。

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
