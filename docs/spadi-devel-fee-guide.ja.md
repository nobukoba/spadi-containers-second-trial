# spadi-devel-fee ガイド

**Language: [English](spadi-devel-fee-guide.md) | 日本語**

FEE の基板制御・マスク設定を行うイメージです。 ソース編集と再ビルドも扱います。

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
│   ├── spadi-prepare-runtime.sh
│   ├── spadi-prepare-local.sh
│   ├── spadi-env.sh
│   ├── *-build.sh / *-clone-latest.sh
│   └── fee/
├── StrLRTDC/bin/set_tdcmask
├── StrHRTDC/bin/
└── src/
    ├── hul-common-lib/
    ├── amaneq-soft/
    ├── openFPGALoader/
    └── sitcp-sitcpxg-mpc-mpcx-ip-utility-first-trial/

/workspace/spadi/                   # SPADI_LOCAL → host workspace/spadi
├── scripts/
│   └── fee/
│   │   └── amaneq-lrtdc-1ch/{config.sh,setup.sh}
├── bin/
├── lib/
├── lib64/
├── include/
├── share/
├── src/
├── build/
└── rawdata/
```

`/opt/spadi` はイメージが提供し、`/workspace/spadi` はホストに保存される作業領域です。 `spadi-prepare-local.sh` がローカルの scripts、src、build、bin、lib、lib64、include、share、rawdata を作成します。ソース一覧は主に編集するプロジェクトを示しています。

環境変数 `SPADI_LOCAL` の既定値は `/workspace/spadi`、`SPADI_ROOT` は `/opt/spadi` です。起動時に設定されます。環境変数の設定だけではディレクトリは作られません。ホストの `workspace/spadi` と対応します。詳細は [README の共通手順](../README.ja.md)を参照してください。

## イメージをダウンロードする

以下はコンテナの外で、ホストの端末から実行します。利用する方式に合わせて、Apptainer または Docker のどちらかを選んでください。

### Apptainer

64 bit Linux (x86_64) または Windows WSL2 の Linux 端末で、Apptainer をインストールしてから、このイメージの SIF をダウンロードします。

```bash
curl -fL -O \
  https://github.com/nobukoba/spadi-containers-second-trial/releases/download/latest/spadi-devel-fee.sif
```

### Docker

macOS または Linux の端末で、Docker を起動してから、このイメージをダウンロードします。Apple Silicon の場合も `--platform linux/amd64` を指定します。

```bash
docker pull --platform linux/amd64 \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-fee:latest
```

`latest` は更新されます。再現性が必要な場合は、[GitHub Releases](https://github.com/nobukoba/spadi-containers-second-trial/releases/tag/latest) のタイムスタンプ付き SIF を保存するか、Docker イメージの digest を記録してください。起動方法と永続化の設定は [README の Quick start](../README.ja.md#quick-start) を参照してください。

## このイメージを起動する

[README の Quick start](../README.ja.md#quick-start) のイメージ名を **`spadi-devel-fee`** にして起動します。ダウンロードする SIF は `spadi-devel-fee.sif`、Docker イメージは `ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-fee:latest` です。起動後の以下の操作はコンテナ内で実行します。

```bash
/opt/spadi/scripts/spadi-version.sh
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
| `$SPADI_LOCAL/src/hul-common-lib` | `hul-common-lib-build.sh` |
| `$SPADI_LOCAL/src/amaneq-soft` | `amaneq-build.sh` |
| `$SPADI_LOCAL/src/openFPGALoader` | `openfpgaloader-build.sh` |
| `$SPADI_LOCAL/src/sitcp-sitcpxg-mpc-mpcx-ip-utility-first-trial` | `sitcp-utility-build.sh` |

```bash
hul-common-lib-build.sh
amaneq-build.sh
openfpgaloader-build.sh
sitcp-utility-build.sh
```

上は依存順の一覧です。変更したコンポーネントと、それに依存するコンポーネントだけ再ビルドしてください。標準の並列数は `NPROC=4` で、例えば `NPROC=2 amaneq-build.sh` のように変更できます。SiTCP utility はソース内で make を実行し、それ以外の掲載ヘルパーは `$SPADI_LOCAL/build/<project>` を使用します。

## 上流の最新ソースを試す

clone と build は別操作です。clone ヘルパーは既存ソースを上書きしません。現在のソースを保存し、同名ディレクトリがないことを確認してから、意図的に最新ソースへ切り替える場合だけ実行します。

```bash
amaneq-clone-latest.sh
amaneq-build.sh
```

通常の準備はイメージに固定されたソースを使用します。clone による最新ソースは固定版の検証範囲外です。

## 再ビルド後の確認

```bash
spadi-env.sh
ls -l "$SPADI_LOCAL/StrLRTDC/bin/set_tdcmask"
```

ローカルの `bin` と `lib` はイメージ側より先に検索されます。LR 用マスクヘルパーは、LR と HR の混同を避けるためイメージ側のフルパスを選びます。再ビルドした LR コマンドを個別に確認する場合は `$SPADI_LOCAL/StrLRTDC/bin/set_tdcmask` を明示してください。版情報レポーターはイメージの版を表示し、ローカルの改変内容は記録しません。ソースのコミットとビルドログも保存してください。

Dockerfile、CI、SIF の生成・公開を変更する場合は [コンテナ保守ガイド](container-maintainer-guide.md)を参照してください。

## AMANEQ LR-TDC の102チャンネルを設定する

1-Gbps Str-LRTDC の AMANEQ 1台を `192.168.10.16` に接続します。DIP1 = 0（デフォルト IP）、DIP3 = 1（スタンドアロン）にし、下側 DCRv2 メザニンの0始まりのチャンネル102を使います。ホスト側 Ethernet は `192.168.10.1/24` などにし、UDP 4660 が到達することを確認します。WSL2 でも Linux 側の経路を確認してください。取得中のプログラムを止めてから設定します。

```bash
cd "$SPADI_LOCAL/scripts/fee/amaneq-lrtdc-1ch"
cat config.sh
get_version 192.168.10.16
./setup.sh
```

`cat config.sh` は設定ファイルを表示するだけです。編集は `vim config.sh` などで行います。ヘルパーは LR 用 `set_tdcmask` で4バンクを一括設定し、`read_register` で照合します。直接実行する場合は以下です。

```bash
/opt/spadi/StrLRTDC/bin/set_tdcmask \
  192.168.10.16 ffffffff ffffffff ffffffff ffffffbf
read_register 192.168.10.16 10300000 4
```

| Bank | Channels | Mask |
|---|---|---|
| Main-U | 0–31 | `ffffffff` |
| Main-D | 32–63 | `ffffffff` |
| MZN-U | 64–95 | `ffffffff` |
| MZN-D | 96–127 | `ffffffbf` |

1 のビットがマスクです。102 は MZN-D の bit 6 なので、このビットだけ 0 にします。正常なら MZN-D の読み戻しは `0xffffffbf` です。IP は `config.sh` の `AMANEQ_IP` で変更します。リセット後は設定を再適用します。

### MZN-D の読み戻しに関する制約

実機 FW ID `0x60c4`、バージョン `2.10`（16進表記 `2.A`）で、MZN-D への書き込みは正常応答でも読み戻しが `0xffffffff` となる症状を確認しています。[公式 HDL](https://github.com/AMANEQ-official/strtdc-src/blob/71c188a74c93a7d06cb9e803d50360b05495e730/lrtdc-impl/strLrTdc.vhd#L685) は MZN-D の Read 分岐で誤って MZN-U を判定しています。書き込み失敗と断定できませんが、内部マスクも独立には確認できません。ヘルパーは `Mask verification failed at 10300000` で停止します。これを成功と扱わず、修正ファームウェアまたは独立した実データ検証で設定を確認してください。実機の NestDAQ 取得は未検証です。

## FEE ツールと取得用イメージ

`get_version`、`read_register`、`write_register` は基板制御、`openFPGALoader` は FPGA 書き込み、SiTCP の IP ユーティリティはネットワーク設定に使用します。LR 用と HR 用の `set_tdcmask` は同名なので、上記の LR 用フルパスを使用してください。

```bash
openFPGALoader --version
command -v mpc-mpcx-ip-reader
command -v sitcp-sitcpxg-ip-reader
```

FPGA 書き込みには対象基板に適合するビットストリームと JTAG 接続が必要です。このレシピはファームウェアの更新や IP の変更を自動実行しません。FEE イメージには NestDAQ / Web Controller がありません。ブラウザで取得する場合は [spadi-user-daq ガイド](spadi-user-daq-guide.ja.md)または [spadi-user-full ガイド](spadi-user-full-guide.ja.md)へ進みます。設定操作だけではデータファイルは作られません。
