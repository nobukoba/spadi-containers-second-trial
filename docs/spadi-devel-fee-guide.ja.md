# spadi-devel-fee ガイド

**Language: [English](spadi-devel-fee-guide.md) | 日本語**

FEE の基板制御、SiTCP ネットワーク設定、FPGA 書き込みを行うイメージです。 ソース編集と再ビルドも扱います。

## ディレクトリ構造

```text
/opt/spadi/                         # SPADI_ROOT
├── bin/
│   ├── get_version / read_register / write_register
│   ├── openFPGALoader
│   ├── sitcp-sitcpxg-ip-{reader,writer}
│   ├── mpc-mpcx-ip-{reader,writer,command}
│   ├── StrLRTDC/set_tdcmask
│   └── StrHRTDC/
├── lib/
├── lib64/
├── include/
├── share/
├── versions/
├── scripts/
│   ├── spadi-prepare-local.sh
│   ├── spadi-env.sh
│   ├── *-build.sh / *-clone-latest.sh
│   └── fee/
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

## イメージのダウンロードと起動

以下のコマンドはホストの端末で実行します。Apptainer または Docker のどちらかを選んでください。

### Apptainer（Linux / Windows WSL2）

```bash
curl -fL -O \
  https://github.com/nobukoba/spadi-containers-second-trial/releases/download/latest/spadi-devel-fee.sif
mkdir -p "$PWD/workspace"
apptainer shell --cleanenv --bind "$PWD/workspace:/workspace" \
  --shell /opt/spadi/spadi-shell.sh spadi-devel-fee.sif
```

### Docker（macOS / Linux）

```bash
docker pull --platform linux/amd64 \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-fee:latest
mkdir -p "$PWD/workspace"
docker run --rm -it \
  --platform linux/amd64 \
  -e LOCAL_UID="$(id -u)" -e LOCAL_GID="$(id -g)" \
  -v "$PWD/workspace:/workspace" \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-fee:latest
```

作業ファイルはホストの `workspace` に保存されます。イメージを更新する場合は再ダウンロードまたは再 pull してください。

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
ls -l "$SPADI_LOCAL/bin/StrLRTDC/set_tdcmask"
```

ローカルの `bin` と `lib` はイメージ側より先に検索されます。再ビルドした LR コマンドを個別に確認する場合は `$SPADI_LOCAL/bin/StrLRTDC/set_tdcmask` を明示してください。版情報レポーターはイメージの版を表示し、ローカルの改変内容は記録しません。ソースのコミットとビルドログも保存してください。

Dockerfile、CI、SIF の生成・公開を変更する場合は [コンテナ保守ガイド](container-maintainer-guide.md)を参照してください。

## SiTCP / SiTCP-XG のネットワーク設定

以下はコンテナ内で実行します。基板の現在の IP を指定して RBCP（UDP 4660）で通信します。ホストの Ethernet 設定と基板への経路を先に確認し、DAQ を停止してください。通常の Apptainer 起動はホストのネットワークを共有します。Linux の Docker で同じ経路を使う場合は、起動例の `docker run` に `--network host` を追加します。環境ごとの条件は [README](../README.ja.md) を参照してください。

### 現在の設定を読む

```bash
sitcp-sitcpxg-ip-reader 192.168.10.16
mpc-mpcx-ip-reader 192.168.10.16
```

前者は SiTCP / SiTCP-XG の MAC・IP、後者は MPC / MPCX の EEPROM 設定を表示します。対象の実装に対応するコマンドを選びます。

### EEPROM の IP を変更する

以下は現在の IP が `192.168.10.16`、保存する新しい IP が `192.168.10.17` の例です。

```bash
sitcp-sitcpxg-ip-writer 192.168.10.16 192.168.10.17
```

既定では EEPROM を更新します。現在動作中の IP の切り替えと、リセット後に EEPROM の IP が使われるかは基板の実装・DIP 設定に依存します。書き込み直後に新 IP に切り替わったと決めつけず、基板の手順に従って再起動・設定確認を行ってください。

### MPC / MPCX のライセンス書き込みと EEPROM の IP 変更

対象基板用に取得したファイルをホストの `workspace` に置きます。以下の `board.mpcx` は利用者が用意するファイル名の例です。

```bash
mpc-mpcx-ip-writer 192.168.10.16 /workspace/board.mpcx \
  --set-eeprom-ip 192.168.10.17
mpc-mpcx-ip-reader 192.168.10.16
```

ライセンスファイルはイメージに含まれません。このコマンドは現在の IP `192.168.10.16` に接続してライセンスを書き込み、EEPROM に IP `192.168.10.17` を保存します。現在動作中の IP は変更しないため、直後の読み取りは元の IP を使います。MPC ファイルの場合は `/workspace/board.mpc` など、用意したファイルのパスに置き換えてください。再起動後の IP 選択は基板の DIP 設定・実装に従います。追加オプション、MPC ファイル、現在の IP を変更する操作については `mpc-mpcx-ip-command --help` と [収録リビジョンのユーティリティ README](https://github.com/nobukoba/sitcp-sitcpxg-mpc-mpcx-ip-utility-first-trial/blob/4bc47b6f5ac791acfbd88c73dd987b7625074273/README.md) を参照してください。

## openFPGALoader で FPGA を書き込む

対象 FPGA に適合するビットストリームと対応 JTAG ケーブルを用意します。以下は Digilent HS3 の例です。基板やケーブルが異なる場合は、対応一覧から実際の名前を選んでください。

### USB ケーブルをコンテナから使えるようにする

Linux ホストで USB デバイスへのアクセス権を設定し、ケーブルを接続します。通常の Apptainer 起動ではホストの `/dev` を利用します。Docker では USB デバイスを明示的に渡す必要があります。ホストの `lsusb` で Bus / Device 番号を確認し、起動例の `docker run` に、例えば `--device=/dev/bus/usb/001/002` を追加してください。番号は再接続で変わることがあります。ホスト側の権限設定は [公式インストール手順](https://trabucayre.github.io/openFPGALoader/guide/install.html) を参照してください。WSL2 では先に USB を Linux 側に接続する必要があります。macOS の Docker 起動例だけではホストの USB JTAG ケーブルは使えません。

### ケーブルと FPGA を確認する

```bash
openFPGALoader --version
openFPGALoader --list-cables
openFPGALoader --list-boards
openFPGALoader -c digilent_hs3 --detect
```

### SRAM にビットストリームをロードする

ホストの `workspace/firmware.bit` に対象基板のファイルを置き、コンテナ内で実行します。

```bash
openFPGALoader -c digilent_hs3 /workspace/firmware.bit
```

SRAM へのロードは揮発性で、電源断で失われます。フラッシュへの保存は別操作の `-f` です。対応基板名（`-b`）、FPGA 型番、フラッシュ構成を確認してから使用してください。基板ごとに必要な指定が異なるため、上の SRAM コマンドに無条件で `-f` を足さないでください。詳細は [公式の基本操作](https://trabucayre.github.io/openFPGALoader/guide/first-steps.html) を参照してください。

## hul-common-lib と amaneq-soft による基板制御

### hul-common-lib：バージョン確認とレジスタ操作

[hul-common-lib](https://github.com/spadi-alliance/hul-common-lib) は、RBCP による基板制御の共通ライブラリとコマンドを提供します。`get_version` はファームウェア情報の確認、`read_register` はレジスタの読み取り、`write_register` は書き込みに使います。

まず、基板の IP とネットワーク経路を確認して、コンテナ内でバージョンを読み取ります。以下の IP は例なので、接続先に合わせて変更してください。

```bash
get_version 192.168.10.16
```

レジスタ操作では対象ファームウェアのレジスタマップでアドレス・サイズ・値を確認します。書き込み後は読み戻しも確認してください。コマンドの引数とライブラリの使い方は [上流の README](https://github.com/spadi-alliance/hul-common-lib#readme) を参照してください。

### amaneq-soft：ファームウェア別の設定ツール

[amaneq-soft](https://github.com/spadi-alliance/amaneq-soft) は AMANEQ のファームウェアに対応した制御・設定ツールを提供します。収録する LR-TDC 用ツールは `$SPADI_ROOT/bin/StrLRTDC/`、HR-TDC 用は `$SPADI_ROOT/bin/StrHRTDC/` にあります。

例えば `set_tdcmask` は TDC チャンネルのマスクを設定するツールです。LR 用と HR 用には同名のコマンドがあるため、対象ファームウェアのフルパスを選びます。LR 用は `$SPADI_ROOT/bin/StrLRTDC/set_tdcmask` で、IP と4バンクのマスク値を指定します。設定値と操作手順は [上流の README・ソース](https://github.com/spadi-alliance/amaneq-soft#readme) で確認してください。設定を変更する際は DAQ を停止します。

特定のチャンネルを使う取得手順は、[DAQ ガイド](spadi-user-daq-guide.ja.md)または [FULL ガイド](spadi-user-full-guide.ja.md)を参照してください。

## データ取得へ進む

FEE イメージには NestDAQ / Web Controller がありません。ブラウザで取得する場合は [spadi-user-daq ガイド](spadi-user-daq-guide.ja.md)または [spadi-user-full ガイド](spadi-user-full-guide.ja.md)へ進みます。基板の設定操作だけでは取得データファイルは作られません。

## Appendix: 含まれるソフトウェア

以下はイメージに含まれる主要ソフトウェアです。固定バージョン・リビジョンの定義は [versions.env](../versions/versions.env) にあります。使用中のイメージの情報は、コンテナ内の `/opt/spadi/scripts/spadi-version.sh` と `/opt/spadi/versions/versions.env` で確認できます。ローカルで再ビルドしたソフトウェアはこの一覧の固定版とは別です。

| ソフトウェア | 用途 | 固定版・リビジョン |
|---|---|---|
| [hul-common-lib](https://github.com/spadi-alliance/hul-common-lib) | RBCP 基板制御：get_version、read_register、write_register | [`65476509aa40`](https://github.com/spadi-alliance/hul-common-lib/tree/65476509aa401aad10148ec7c2d2a50ba7d2db3e) |
| [amaneq-soft](https://github.com/spadi-alliance/amaneq-soft) | AMANEQ LR/HR 用ツール（bin/StrLRTDC、bin/StrHRTDC） | [`86fef97ccc4e`](https://github.com/spadi-alliance/amaneq-soft/tree/86fef97ccc4e6488739e2d8b549a1c5bddd3542e) |
| [openFPGALoader](https://github.com/trabucayre/openFPGALoader) | 対応インターフェースによる FPGA SRAM・フラッシュ書き込み | [`24e46d13bb8f`](https://github.com/trabucayre/openFPGALoader/tree/24e46d13bb8f2bc9371e9ca8443ece2fafc4b20d) |
| [SiTCP IP / MPC utilities](https://github.com/nobukoba/sitcp-sitcpxg-mpc-mpcx-ip-utility-first-trial) | SiTCP/SiTCP-XG IP、MPC/MPCX ライセンス設定 | [`4bc47b6f5ac7`](https://github.com/nobukoba/sitcp-sitcpxg-mpc-mpcx-ip-utility-first-trial/tree/4bc47b6f5ac791acfbd88c73dd987b7625074273) |

OS は AlmaLinux 9 です。ネットワーク調査ツール（iproute、iputils、net-tools、bind-utils、traceroute、tcpdump、nmap-ncat）、curl / wget、vim / emacs なども含みます。OS パッケージは AlmaLinux のパッケージ版で、上表のソース固定版とは管理方法が異なります。

devel は上記ランタイムに加えて、ソース、開発用ヘッダー、コンパイラ、Make / CMake、Git、および対象コンポーネントのビルド・取得ヘルパーを含みます。編集・ビルドは `$SPADI_LOCAL/src` と `$SPADI_LOCAL/build`、インストールは `$SPADI_LOCAL` を使います。
