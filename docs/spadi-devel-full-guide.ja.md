# spadi-devel-full ガイド

**Language: [English](spadi-devel-full-guide.md) | 日本語**

FEE、NestDAQ、ROOT、ARTEMIS を使う取得と解析を行うイメージです。 ソース編集と再ビルドも扱います。

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
│   ├── fee/
│   ├── nestdaq/
│   └── artemis/
├── StrLRTDC/bin/set_tdcmask
├── StrHRTDC/bin/
├── scripts/exp-config/
└── src/
    ├── hul-common-lib/
    ├── amaneq-soft/
    ├── openFPGALoader/
    ├── sitcp-sitcpxg-mpc-mpcx-ip-utility-first-trial/
    ├── nestdaq/
    ├── nestdaq-user-impl/
    ├── root/
    └── artemis/

/workspace/spadi/                   # SPADI_LOCAL → host workspace/spadi
├── scripts/
│   ├── fee/
│   │   └── amaneq-lrtdc-1ch/{config.sh,setup.sh}
│   ├── nestdaq/
│   │   ├── common/
│   │   ├── amaneq-lrtdc-1ch/
│   │   └── raris-ac-lgad/
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
    ├── amaneq-lrtdc-1ch/00/run000001.dat
    └── raris_ac_lgad_202603/{00,01,02}/run000020.dat
```

`/opt/spadi` はイメージが提供し、`/workspace/spadi` はホストに保存される作業領域です。 `spadi-prepare-local.sh` がローカルの scripts、src、build、bin、lib、lib64、include、share、rawdata を作成します。ソース一覧は主に編集するプロジェクトを示しています。 AMANEQ の run-start.sh が出力サブディレクトリを作り、ブラウザの FileSink Run がデータファイルを作ります。RARiS のファイルは rawdata-download.sh が取得します。 analysis ディレクトリは後述の mkdir で作成します。

環境変数 `SPADI_LOCAL` の既定値は `/workspace/spadi`、`SPADI_ROOT` は `/opt/spadi` です。起動時に設定されます。環境変数の設定だけではディレクトリは作られません。ホストの `workspace/spadi` と対応します。詳細は [README の共通手順](../README.ja.md)を参照してください。

## イメージをダウンロードする

以下はコンテナの外で、ホストの端末から実行します。利用する方式に合わせて、Apptainer または Docker のどちらかを選んでください。

### Apptainer

64 bit Linux (x86_64) または Windows WSL2 の Linux 端末で、Apptainer をインストールしてから、このイメージの SIF をダウンロードします。

```bash
curl -fL -O \
  https://github.com/nobukoba/spadi-containers-second-trial/releases/download/latest/spadi-devel-full.sif
```

### Docker

macOS または Linux の端末で、Docker を起動してから、このイメージをダウンロードします。Apple Silicon の場合も `--platform linux/amd64` を指定します。

```bash
docker pull --platform linux/amd64 \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-full:latest
```

`latest` は更新されます。再現性が必要な場合は、[GitHub Releases](https://github.com/nobukoba/spadi-containers-second-trial/releases/tag/latest) のタイムスタンプ付き SIF を保存するか、Docker イメージの digest を記録してください。起動方法と永続化の設定は [README の Quick start](../README.ja.md#quick-start) を参照してください。

## このイメージを起動する

[README の Quick start](../README.ja.md#quick-start) のイメージ名を **`spadi-devel-full`** にして起動します。ダウンロードする SIF は `spadi-devel-full.sif`、Docker イメージは `ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-full:latest` です。起動後の以下の操作はコンテナ内で実行します。

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
| `$SPADI_LOCAL/src/nestdaq` | `nestdaq-build.sh` |
| `$SPADI_LOCAL/src/nestdaq-user-impl` | `nestdaq-user-impl-build.sh` |
| `$SPADI_LOCAL/src/artemis` | `artemis-build.sh` |

```bash
hul-common-lib-build.sh
amaneq-build.sh
openfpgaloader-build.sh
sitcp-utility-build.sh
nestdaq-build.sh
nestdaq-user-impl-build.sh
artemis-build.sh
```

上は依存順の一覧です。変更したコンポーネントと、それに依存するコンポーネントだけ再ビルドしてください。標準の並列数は `NPROC=4` で、例えば `NPROC=2 nestdaq-build.sh` のように変更できます。SiTCP utility はソース内で make を実行し、それ以外の掲載ヘルパーは `$SPADI_LOCAL/build/<project>` を使用します。`root-build.sh` は提供していません。ROOT のソースは参照・個別開発用に保持されています。

## 上流の最新ソースを試す

clone と build は別操作です。clone ヘルパーは既存ソースを上書きしません。現在のソースを保存し、同名ディレクトリがないことを確認してから、意図的に最新ソースへ切り替える場合だけ実行します。

```bash
nestdaq-clone-latest.sh
nestdaq-build.sh
```

通常の準備はイメージに固定されたソースを使用します。clone による最新ソースは固定版の検証範囲外です。ARTEMIS の clone ヘルパーは上流の既定ブランチを取得するので、通常のイメージで使う固定 `develop` コミットと同一とは限りません。

## 再ビルド後の確認

```bash
spadi-env.sh
ls -l "$SPADI_LOCAL/StrLRTDC/bin/set_tdcmask"
command -v AmQStrTdcSampler
command -v STFBuilder
command -v TimeFrameBuilder
command -v FileSink
command -v artemis
```

ローカルの `bin` と `lib` はイメージ側より先に検索されます。LR 用マスクヘルパーは、LR と HR の混同を避けるためイメージ側のフルパスを選びます。再ビルドした LR コマンドを個別に確認する場合は `$SPADI_LOCAL/StrLRTDC/bin/set_tdcmask` を明示してください。版情報レポーターはイメージの版を表示し、ローカルの改変内容は記録しません。ソースのコミットとビルドログも保存してください。

Dockerfile、CI、SIF の生成・公開を変更する場合は [コンテナ保守ガイド](container-maintainer-guide.md)を参照してください。

## AMANEQ の LR-TDC を NestDAQ で1チャンネル読み出す

**IP 192.168.10.16、チャンネル102だけ unmask** する例です。番号は0始まりです。1-Gbps Str-LRTDC ファームウェアを使い、DIP1 = 0（デフォルト IP）、DIP3 = 1（スタンドアロン）に設定します。下側 DCRv2 メザニンの102へ信号を接続してください。

ホストの Ethernet インターフェースには `192.168.10.1/24` などのアドレスを設定します。Linux 側から UDP 4660（RBCP 制御）と TCP 24（SiTCP データ）で到達できる必要があります。WSL2 では Windows 側のインターフェースと Linux 側の経路を確認してください。同じ AMANEQ を読み出している他のプログラムは停止しておきます。

```text
AMANEQ ch102 → AmQStrTdcSampler-0 → STFBuilder-0
            → TimeFrameBuilder-0 → FileSink-0 → 00/run000001.dat
```

AMANEQ の実機は1台です。Sampler、STFBuilder、TimeFrameBuilder、FileSink はコンテナ内で動く4つのソフトウェアプロセスです。

Valkey、パラメータ、トポロジー、プラグイン、tmux のヘルパーは RARiS 再生と共通です。実機用には Sampler と STFBuilder を使用し、FileSink で TF/STF レコードを保存します。

### MZN-D の読み戻しに関する制約

実機 FW ID `0x60c4`、バージョン `2.10`（16進表記 `2.A`）で、MZN-D への書き込みは正常応答でも読み戻しが `0xffffffff` となる症状を確認しています。[公式 HDL](https://github.com/AMANEQ-official/strtdc-src/blob/71c188a74c93a7d06cb9e803d50360b05495e730/lrtdc-impl/strLrTdc.vhd#L685) は MZN-D の Read 分岐で誤って MZN-U を判定しています。書き込み失敗と断定できませんが、内部マスクも独立には確認できません。ヘルパーは `Mask verification failed at 10300000` で停止します。これを成功と扱わず、修正ファームウェアまたは独立した実データ検証で設定を確認してください。実機の NestDAQ 取得は未検証です。

### 端末でサービスを準備する

コンテナ内で：

`cat config.sh` は現在の設定を表示します。変更する場合は `vim config.sh` などで編集してから準備を開始してください。

```bash
cd "$SPADI_LOCAL/scripts/nestdaq/amaneq-lrtdc-1ch"
cat config.sh
ping -c 3 192.168.10.16
./run-start.sh
```

`run-start.sh` は FEE マスクの設定と読み戻し確認、Valkey、パラメータ、トポロジー、4つのプロセスの準備を行い、すべてのプロセスが **Idle** になるまで待ちます。この時点では読み出しを開始しません。以降の初期化・開始・停止・run 番号の変更はブラウザで操作します。

### ブラウザで初期化する

ホストのブラウザで **http://localhost:8081/daq-webctl.html** を開きます。WSL2 の場合も Windows 側のブラウザから開きます。

1. **State Summary** に `AmQStrTdcSampler`、`STFBuilder`、`TimeFrameBuilder`、`FileSink` がそれぞれ1プロセスずつ表示され、すべて **Idle** であることを確認します。**Show details** で個々の状態も表示できます。
2. **Wait Device Ready** と **Wait Ready** のチェックを外します。以下では各ボタンを押した後に状態を確認して進めます。
3. **Auto increment at RUN-Stop** のチェックを外します。サービスを個別に Stop するため、チェックがあるとクリックのたびに run 番号が増えます。
4. **RUN number** の **New value** に `1` を入力して **Send** を押し、**Next : 1** を確認します。保存済みの番号は使わないでください。
5. **Select command target** のサービスとインスタンスを両方 **all** にします。
6. **Init Device and Connection** を押し、4つのプロセスすべてが **Device-Ready** になるまで待ちます。
7. **Init Task** を押し、4つのプロセスすべてが **Ready** になるまで待ちます。

ブラウザの再読み込み後も、上の3つのチェックを外してください。

### ブラウザで読み出しを開始する

サービス選択では **all を解除**し、表のサービスだけを選びます。インスタンスは **all** のままにします。下流から順に **Run** を押し、選んだデバイスが **Running** になってから次へ進みます。

| 順番 | 選ぶサービス | 操作 |
|---|---|---|
| 1 | `FileSink` | **Run** → **Running** |
| 2 | `TimeFrameBuilder` | **Run** → **Running** |
| 3 | `STFBuilder` | **Run** → **Running** |
| 4 | `AmQStrTdcSampler` | **Run** → **Running** |

Sampler の Run で AMANEQ への TCP 接続が開き、読み出しが始まります。4つのプロセスすべての **Running** と **Error = 0** を確認してください。run 1 の保存先はホストの `workspace/spadi/rawdata/amaneq-lrtdc-1ch/00/run000001.dat` です。

### ブラウザで停止し、次の run を始める

上流から `AmQStrTdcSampler` → `STFBuilder` → `TimeFrameBuilder` → `FileSink` の順にサービスを1つずつ選び、**Stop** を押します。それぞれ **Ready** になるまで待ち、次の Stop まで1秒程度空けます。最後に FileSink が **Ready** になれば、トレーラー書き込みとファイル close が完了しています。

次の取得では **New value** に未使用の番号（例：`2`）を入力して **Send** を押します。サービスとインスタンスを **all** にし、**Reset Task** → すべてのプロセス **Device-Ready**、**Reset Device** → すべてのプロセス **Idle** の順に確認します。その後、初期化と開始の手順を繰り返します。run 番号は取得中に変更しないでください。

作業を終えるときはブラウザですべてのプロセスを Stop し、サービスとインスタンスを **all** にして **End** を押します。プロセスが **Exiting** または一覧から消えたことを確認し、tmux の `control` ウィンドウで `./run-cleanup.sh` を実行して対象セッションを閉じます。このヘルパーは稼働中のプロセスが残っている場合は終了を拒否します。ブラウザを閉じるだけでは収集は停止しません。

### 設定と保存データ

FEE の Main-U、Main-D、MZN-U、MZN-D のマスクは `ffffffff ffffffff ffffffff ffffffbf` です。102は MZN-D の bit 6 で、1が mask、0が unmask です。他の0〜127入力はすべて mask します。停止中に設定だけを行う場合は `./fee-setup.sh` を実行してください。

IP、最初の run 番号、保存先、ポートは NestDAQ 側の `config.sh` で編集します。ここにある `AMANEQ_IP` が FEE ヘルパーにも渡されます。マスク値は `scripts/fee/amaneq-lrtdc-1ch/config.sh` にあります。起動後の run 番号はブラウザで設定します。準備時には `RUN_NUMBER` の既存出力を拒否し、ブラウザからの Run でも FileSink の `openmode=create` が上書きを防ぎます。番号重複による FileSink の異常があれば収集を進めず、ログを確認してください。稼働中のセッションの設定は変更しないでください。

デフォルトは Valkey `127.0.0.1:6380`（DB0: 登録情報、DB1: メトリクス、DB2: パラメータ）、Web 状態表示 `http://localhost:8081/daq-webctl.html`、データ転送ポート5599〜5601、任意の DQM モニター用 PUB ポート5602です。モニターが接続していなくても、FileSink に DQM チャンネルの定義が必要です。RARiS のデフォルトとは分けています。この設定専用の Valkey DB を使い、他の稼働中の設定と共用しないでください。停止後も Valkey は再利用のため残します。

通常の収集停止は上記のブラウザ操作で行います。`run-stop.sh` はブラウザが使えない場合の停止・終了に使用します。通常の End 後には `run-cleanup.sh` を使います。上流から止めて下流の処理時間を確保し、FileSink の PostRun、トレーラー書き込み、ファイル close を待ってからデバイスと tmux を終了します。エラーやタイムアウト時は調査用に tmux を残します。固定版 upstream は最後の不完全なフレームや FileSink の PostRun に残った入力を破棄する場合があり、run 境界での無損失は保証しません。ログとデリミタのフラグを確認してください。入力がなくてもハートビートデリミタが記録されるため、ファイルの増加だけでは102のヒットを確認できません。保存ファイルは FileSink のヘッダー・トレーラーと TF/STF レコードを含み、以前の `strdaq` の生ストリームとは形式が異なります。

マスク設定には LR-TDC 用の `set_tdcmask` を使用します。`fee-setup.sh` もこのコマンドで4バンクを一括設定し、`read_register` で読み戻します。取得を停止してから実行してください。

```bash
/opt/spadi/StrLRTDC/bin/set_tdcmask 192.168.10.16 ffffffff ffffffff ffffffff ffffffbf
```

## tmux だけで端末とログを操作する

AMANEQ の準備後、コンテナ内で `./run-attach.sh` を実行します。RARiS も、その設定ディレクトリの同名ヘルパーで接続できます。

| ウィンドウ | 用途 |
|---|---|
| `control` | 設定確認、`./run-status.sh`、End 後の `./run-cleanup.sh` を実行するシェル |
| `webctl` | DAQ Web Controller のログ |
| `sampler` | AMANEQ Sampler のログ |
| `STF0` | STFBuilder のログ |
| `TFB0` | TimeFrameBuilder のログ |
| `sink0` | FileSink のログ |

**Ctrl-b** を押して離してから、次のキーを押します。

| キー | 操作 |
|---|---|
| `w` | ウィンドウ一覧から選択 |
| `n` / `p` | 次 / 前のウィンドウ |
| `0` | `control` に移動 |
| `[` | 過去のログをスクロール（矢印キー / PageUp、`q` で戻る） |
| `d` | セッションから離れる。収集と Web Controller は継続 |

初期化時と収集中に、Web の **State Summary / Show details** で各プロセスが1つずつあることと、tmux の各ログにエラーがないことを確認します。終了後もウィンドウを残すため、ウィンドウ数だけで正常動作を判断せず、終了コードとログを確認してください。ブラウザが使えない場合は `control` で `./run-stop.sh` を実行できます。

Valkey は共通ヘルパーが管理するバックグラウンドサービスです。デフォルトのログは `control` で `tail -n 50 /tmp/spadi-valkey-6380.log` として確認できます（ポート変更時はファイル名も変わります）。ログ確認・端末操作に xterm、`DISPLAY`、X11 転送は不要です。停止後も Valkey は再利用のため残します。

## RARiS AC-LGAD のファイル再生

```bash
cd "$SPADI_LOCAL/scripts/nestdaq/raris-ac-lgad"
./rawdata-download.sh
./run-start.sh
./run-status.sh
./run-attach.sh
# Ctrl-b d で離れます。
```

3個の STFBFilePlayer と1個の TimeFrameBuilder を起動します。`http://localhost:8080/daq-webctl.html` で対象サービスを選択し、run 番号を設定して **Init Device and Connection → Init Task → Run** の順に状態を確認しながら進めます。デフォルト構成に FileSink はありません。TFB 出力 `tcp://127.0.0.1:5501` には利用する下流プロセスを接続してください。Web 制御で Stop → Reset Task → Reset Device を行い、対象を all にして End でプロセスを終了してから、`./run-stop.sh` で tmux セッションを閉じます。通常の変更はこの設定の `config.sh` で行います。

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

## Appendix: SPADI-A DAQ マニュアルとの対応

[公式マニュアルの DAQ の実行方法](https://www.rcnp.osaka-u.ac.jp/~spadi/wiki/?SPADI-A%20DAQ%20マニュアル/ソフトウェア/DAQの実行方法)、[NestDAQ スクリプトの編集](https://www.rcnp.osaka-u.ac.jp/~spadi/wiki/?SPADI-A%20DAQ%20マニュアル/ソフトウェア/DAQの設定/NestDAQスクリプトの編集)、[FEE スクリプトの編集](https://www.rcnp.osaka-u.ac.jp/~spadi/wiki/?SPADI-A%20DAQ%20マニュアル/ソフトウェア/DAQの設定/FEEスクリプトの編集)を基にしています。サービスと FEE の準備、プロセス数とログの確認、ブラウザでの Init → Run → Stop → Reset → End の流れを踏襲します。端末は1つの tmux セッションで管理します。

| 公式マニュアルの役割 | このコンテナでの対応 |
|---|---|
| `init.sh`：Redis と Web Controller | `common/start-valkey.sh` と `common/tmux-start.sh` の `webctl` ウィンドウ |
| `fee_scripts/config_modules.sh`：FEE 設定 | AMANEQ の `fee-setup.sh` と FEE 側 `setup.sh`（このスタンドアロン LR 例では入力マスクを設定） |
| `mq-param.sh`、`topology.sh` | `common/apply-parameters.sh`、`common/apply-topology.sh` |
| `tf.sh`、`run-stf-tf.sh`、`start_device.sh` | AMANEQ の `run-start.sh`、`common/tmux-start.sh`、`common/start-device.sh` |
| 各 xterm のログ確認 | `run-attach.sh` で同じ tmux セッションの各ウィンドウを確認 |
| Web の **End** 後の後片付け | AMANEQ の `run-cleanup.sh`（対象セッションのみ終了） |

`run-start.sh` が必要な準備をまとめて行うため、共通ヘルパーを個別に実行する必要はありません。古い例の HR メザニン初期化、MIKUMARI Primary 操作、廃止済みの拡張マスクはこの LR スタンドアロン設定にコピーしません。固定版 Sampler の LR 型指定は `TdcType=1` です。
