# spadi-devel-artemis ガイド

**Language: [English](spadi-devel-artemis-guide.md) | 日本語**

ROOT と ARTEMIS による解析を行うイメージです。 ソース編集と再ビルドも扱います。

## ディレクトリ構造

```text
/opt/spadi/                         # SPADI_ROOT
├── bin/
├── lib/
├── lib64/
├── include/
├── share/
├── versions/
├── scripts/
│   ├── spadi-prepare-local.sh
│   ├── spadi-prepare-local.sh
│   ├── spadi-env.sh
│   ├── *-build.sh / *-clone-latest.sh
│   └── artemis/
└── src/
    ├── root/
    └── artemis/

/workspace/spadi/                   # SPADI_LOCAL → host workspace/spadi
├── scripts/
│   └── artemis/
├── bin/
├── lib/
├── lib64/
├── include/
├── share/
├── src/
├── build/
├── analysis/example/{macro,output}/
└── rawdata/
```

`/opt/spadi` はイメージが提供し、`/workspace/spadi` はホストに保存される作業領域です。 `spadi-prepare-local.sh` がローカルの scripts、src、build、bin、lib、lib64、include、share、rawdata を作成します。ソース一覧は主に編集するプロジェクトを示しています。 analysis ディレクトリは後述の mkdir で作成します。

環境変数 `SPADI_LOCAL` の既定値は `/workspace/spadi`、`SPADI_ROOT` は `/opt/spadi` です。起動時に設定されます。環境変数の設定だけではディレクトリは作られません。ホストの `workspace/spadi` と対応します。詳細は [README の共通手順](../README.ja.md)を参照してください。

## イメージのダウンロードと起動

ホストの端末で、使用する方式のコマンドを順番に実行してください。

### Apptainer（Linux / Windows WSL2）

```bash
curl -fL -O \
  https://github.com/nobukoba/spadi-containers-second-trial/releases/download/latest/spadi-devel-artemis.sif
mkdir -p "$PWD/workspace"
apptainer shell --cleanenv --bind "$PWD/workspace:/workspace" \
  --shell /opt/spadi/spadi-shell.sh spadi-devel-artemis.sif
```

### Docker（macOS / Linux）

```bash
docker pull --platform linux/amd64 \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-artemis:latest
mkdir -p "$PWD/workspace"
docker run --rm -it \
  --platform linux/amd64 \
  -e LOCAL_UID="$(id -u)" -e LOCAL_GID="$(id -g)" \
  -v "$PWD/workspace:/workspace" \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-artemis:latest
```

## 作業領域を準備する

ソースとビルド用ディレクトリを含む作業領域を準備します。 既存の設定やソースは上書きしません。準備ヘルパーの共通仕様と更新方法は [README](../README.ja.md) を参照してください。

```bash
spadi-prepare-local.sh
```

## ソースを編集してビルドする

`spadi-prepare-local.sh` でコピーした `$SPADI_LOCAL/src` のソースを編集します。ビルドヘルパーは変更したソースを使い、成果物を `$SPADI_LOCAL` にインストールします。ビルド中はこの作業領域の DAQ や解析プロセスを停止してください。イメージの再ビルドは不要です。

| 編集対象 | ビルドヘルパー |
|---|---|
| `$SPADI_LOCAL/src/artemis` | `artemis-build.sh` |

```bash
artemis-build.sh
```

上は依存順の一覧です。変更したコンポーネントと、それに依存するコンポーネントだけ再ビルドしてください。標準の並列数は `NPROC=4` で、例えば `NPROC=2 artemis-build.sh` のように変更できます。ARTEMIS ヘルパーは `$SPADI_LOCAL/build/artemis` を使用します。`root-build.sh` は提供していません。ROOT のソースは参照・個別開発用に保持されています。

## 上流の最新ソースを試す

clone と build は別操作です。clone ヘルパーは既存ソースを上書きしません。現在のソースを保存し、同名ディレクトリがないことを確認してから、意図的に最新ソースへ切り替える場合だけ実行します。

```bash
artemis-clone-latest.sh
artemis-build.sh
```

通常の準備はイメージに固定されたソースを使用します。clone による最新ソースは固定版の検証範囲外です。ARTEMIS の clone ヘルパーは上流の既定ブランチを取得するので、通常のイメージで使う固定 `develop` コミットと同一とは限りません。

## 再ビルド後の確認

```bash
spadi-env.sh
command -v artemis
```

ローカルの `bin` と `lib` はイメージ側より先に検索されます。版情報レポーターはイメージの版を表示し、ローカルの改変内容は記録しません。ソースのコミットとビルドログも保存してください。

Dockerfile、CI、SIF の生成・公開を変更する場合は [コンテナ保守ガイド](container-maintainer-guide.md)を参照してください。

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
