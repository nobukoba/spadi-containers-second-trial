# spadi-user-fee ガイド

**Language: [English](spadi-user-fee-guide.md) | 日本語**

FEE の基板制御・マスク設定を行うイメージです。

## ディレクトリ構造

```text
/opt/spadi/                         # SPADI_ROOT
├── bin/
├── lib/
├── lib64/
├── share/
├── versions/
├── scripts/
│   ├── spadi-prepare-runtime.sh
│   └── fee/
├── StrLRTDC/bin/set_tdcmask
└── StrHRTDC/bin/

/workspace/spadi/                   # SPADI_LOCAL → host workspace/spadi
├── scripts/
│   └── fee/
│   │   └── amaneq-lrtdc-1ch/{config.sh,setup.sh}
└── rawdata/
```

`/opt/spadi` はイメージが提供し、`/workspace/spadi` はホストに保存される作業領域です。 `spadi-prepare-runtime.sh` が scripts と rawdata を作成します。user イメージには `/opt/spadi/src` はありません。

環境変数 `SPADI_LOCAL` の既定値は `/workspace/spadi`、`SPADI_ROOT` は `/opt/spadi` です。起動時に設定されます。環境変数の設定だけではディレクトリは作られません。ホストの `workspace/spadi` と対応します。詳細は [README の共通手順](../README.ja.md)を参照してください。

## イメージのダウンロードと起動

以下のコマンドはホストの端末で実行します。Apptainer または Docker のどちらかを選んでください。

### Apptainer（Linux / Windows WSL2）

```bash
curl -fL -O \
  https://github.com/nobukoba/spadi-containers-second-trial/releases/download/latest/spadi-user-fee.sif
mkdir -p "$PWD/workspace"
apptainer shell --cleanenv --bind "$PWD/workspace:/workspace" \
  --shell /opt/spadi/spadi-shell.sh spadi-user-fee.sif
```

### Docker（macOS / Linux）

```bash
docker pull --platform linux/amd64 \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-user-fee:latest
mkdir -p "$PWD/workspace"
docker run --rm -it \
  --platform linux/amd64 \
  -e LOCAL_UID="$(id -u)" -e LOCAL_GID="$(id -g)" \
  -v "$PWD/workspace:/workspace" \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-user-fee:latest
```

作業ファイルはホストの `workspace` に保存されます。イメージを更新する場合は再ダウンロードまたは再 pull してください。

## 作業領域を準備する

このイメージに含まれるランタイム用スクリプトをコピーします。 既存の設定やソースは上書きしません。準備ヘルパーの共通仕様と更新方法は [README](../README.ja.md) を参照してください。

```bash
spadi-prepare-runtime.sh
```

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
