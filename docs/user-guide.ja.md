# SPADI コンテナのユーザー向けガイド

**Language: [English](user-guide.md) | 日本語**

インストール済みソフトウェアの利用には `spadi-user-*` を使います。以下の AMANEQ の例には FEE 制御と NestDAQ の両方が必要なので、**spadi-user-daq** または **spadi-user-full** を選んでください。ソース編集・ビルドは[開発者向けガイド](developer-guide.ja.md)に分けています。

## コンテナの起動

### Apptainer（64 bit Linux / Windows WSL2）

64 bit Linux (x86_64) に Apptainer をインストールします。WSL2 では Linux 側の端末で実行してください。ホスト側で：

```bash
curl -fL -O \
  https://github.com/nobukoba/spadi-containers-second-trial/releases/download/latest/spadi-user-daq.sif
mkdir -p "$PWD/workspace"
apptainer shell --cleanenv --bind "$PWD/workspace:/workspace" \
  --shell /opt/spadi/spadi-shell.sh spadi-user-daq.sif
```

### Docker（Linux からの実機読み出し）

Docker を起動した Linux ホストで：

```bash
docker pull --platform linux/amd64 \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-user-daq:latest
mkdir -p "$PWD/workspace"
docker run --rm -it --platform linux/amd64 --network host \
  -e LOCAL_UID="$(id -u)" -e LOCAL_GID="$(id -g)" \
  -v "$PWD/workspace:/workspace" \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-user-daq:latest
```

`--network host` により AMANEQ への接続とホストからの Web 制御を利用します。Windows では上の Apptainer / WSL2 手順を使ってください。macOS の一般的な Docker 利用は [README](../README.ja.md) に記載しています。

どちらも SPADI 環境を自動で読み込み、`/workspace` に移動します。ここに保存したファイルはホストの `workspace` に残ります。`exit` で終了し、同じ起動コマンドで再開できます。以下の設定には新しいヘルパーを含むイメージが必要です。

## 実行設定の編集用コピーを準備する

コンテナ内で：

```bash
spadi-prepare-runtime.sh
```

イメージに含まれる実行設定を `$SPADI_LOCAL/scripts` にコピーし、`$SPADI_LOCAL/rawdata` を作ります。既存ファイルは上書きしません。ソースの取得、コンパイル、`spadi-prepare-local.sh` は不要です。

以前の作業領域を更新する場合は、使用中のセッションを止め、古い `scripts/nestdaq/common` を別名に退避してから準備ヘルパーを実行してください。新しい共通スクリプトを取得した後、退避したファイルと比較して必要な変更を反映します。FEE 側の古い `amaneq-lrtdc-1ch/setup.sh` も、IP 引数を受け取る新しい版に更新してください。編集済みの各 `config.sh` は保持します。

## AMANEQ の LR-TDC を NestDAQ で1チャンネル読み出す

**IP 192.168.10.16、チャンネル102だけ unmask** する例です。番号は0始まりです。1-Gbps Str-LRTDC ファームウェアを使い、DIP1 = 0（デフォルト IP）、DIP3 = 1（スタンドアロン）に設定します。下側 DCRv2 メザニンの102へ信号を接続してください。

ホストの Ethernet インターフェースには `192.168.10.1/24` などのアドレスを設定します。Linux 側から UDP 4660（RBCP 制御）と TCP 24（SiTCP データ）で到達できる必要があります。WSL2 では Windows 側のインターフェースと Linux 側の経路を確認してください。同じ AMANEQ を読み出している他のプログラムは停止しておきます。

```text
AMANEQ ch102 → AmQStrTdcSampler-0 → STFBuilder-0
            → TimeFrameBuilder-0 → FileSink-0 → 00/run000001.dat
```

AMANEQ の実機は1台です。Sampler、STFBuilder、TimeFrameBuilder、FileSink はコンテナ内で動く4つのソフトウェアプロセスです。

Valkey、パラメータ、トポロジー、プラグイン、tmux のヘルパーは RARiS 再生と共通です。実機用には Sampler と STFBuilder を使用し、FileSink で TF/STF レコードを保存します。

### 端末でサービスを準備する

コンテナ内で：

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

作業を終えるときはブラウザですべてのプロセスを Stop した後、コンテナの端末で `./run-stop.sh` を実行してプロセスと tmux を終了します。調査には `./run-status.sh` と `./run-attach.sh` を使います。tmux は **Ctrl-b d** で離れられます。ブラウザを閉じるだけでは収集は停止しません。

### 設定と保存データ

FEE の Main-U、Main-D、MZN-U、MZN-D のマスクは `ffffffff ffffffff ffffffff ffffffbf` です。102は MZN-D の bit 6 で、1が mask、0が unmask です。他の0〜127入力はすべて mask します。停止中に設定だけを行う場合は `./fee-setup.sh` を実行してください。

IP、最初の run 番号、保存先、ポートは NestDAQ 側の `config.sh` で編集します。ここにある `AMANEQ_IP` が FEE ヘルパーにも渡されます。マスク値は `scripts/fee/amaneq-lrtdc-1ch/config.sh` にあります。起動後の run 番号はブラウザで設定します。準備時には `RUN_NUMBER` の既存出力を拒否し、ブラウザからの Run でも FileSink の `openmode=create` が上書きを防ぎます。番号重複による FileSink の異常があれば収集を進めず、ログを確認してください。稼働中のセッションの設定は変更しないでください。

デフォルトは Valkey `127.0.0.1:6380`（DB0: 登録情報、DB1: メトリクス、DB2: パラメータ）、Web 状態表示 `http://localhost:8081/daq-webctl.html`、データ転送ポート5599〜5601、任意の DQM モニター用 PUB ポート5602です。モニターが接続していなくても、FileSink に DQM チャンネルの定義が必要です。RARiS のデフォルトとは分けています。この設定専用の Valkey DB を使い、他の稼働中の設定と共用しないでください。停止後も Valkey は再利用のため残します。

通常の収集停止は上記のブラウザ操作で行います。`run-stop.sh` は作業終了時の後片付けと、ブラウザが使えない場合の停止に使用します。上流から止めて下流の処理時間を確保し、FileSink の PostRun、トレーラー書き込み、ファイル close を待ってからデバイスと tmux を終了します。エラーやタイムアウト時は調査用に tmux を残します。固定版 upstream は最後の不完全なフレームや FileSink の PostRun に残った入力を破棄する場合があり、run 境界での無損失は保証しません。ログとデリミタのフラグを確認してください。入力がなくてもハートビートデリミタが記録されるため、ファイルの増加だけでは102のヒットを確認できません。保存ファイルは FileSink のヘッダー・トレーラーと TF/STF レコードを含み、以前の `strdaq` の生ストリームとは形式が異なります。

## RARiS AC-LGAD のファイル再生

```bash
cd "$SPADI_LOCAL/scripts/nestdaq/raris-ac-lgad"
./rawdata-download.sh
./run-start.sh
./run-status.sh
./run-attach.sh
# Ctrl-b d で離れます。
```

3個の STFBFilePlayer と1個の TimeFrameBuilder を起動します。`http://localhost:8080/daq-webctl.html` で対象サービスを選択し、run 番号を設定して **Init Device and Connection → Init Task → Run** の順に状態を確認しながら進めます。デフォルト構成に FileSink はありません。TFB 出力 `tcp://127.0.0.1:5501` には利用する下流プロセスを接続してください。Web 制御で Stop / Reset を行ってから `./run-stop.sh` でセッションを終了します。通常の変更はこの設定の `config.sh` で行います。

## ディレクトリ構造

以下の構造をすべて手作業で作る必要はありません。コンテナ内で実行するヘルパーが、次のタイミングで作成します。

| 操作 | 作成されるもの |
|---|---|
| `spadi-prepare-runtime.sh` | `/workspace/spadi/scripts/` 以下にイメージ内のヘルパーと設定をコピーし、`/workspace/spadi/rawdata/` を作成 |
| AMANEQ の `./run-start.sh` | 保存先の `rawdata/amaneq-lrtdc-1ch/00/` を作成。収集はまだ開始しない |
| ブラウザで FileSink を **Run** | 指定した run のデータファイル（例：`00/run000001.dat`）を作成 |

準備ヘルパーは既存ファイルを上書きしません。編集済みの `config.sh` も保持します。`/opt/spadi/` はイメージに含まれる領域です。デフォルトの `/workspace/spadi/` に作られたファイルは、ホスト側の `workspace/spadi/` に残ります。`SPADI_LOCAL` や `RAWDATA_DIR` を変更した場合は、その設定先を使います。

```text
/opt/spadi/                           # イメージ内。SIF では読み取り専用
├── bin/                              # デバイス、FEE レジスタ操作
├── lib/                              # ライブラリ、プラグイン、RedisTimeSeries
└── scripts/
    ├── spadi-prepare-runtime.sh
    ├── fee/amaneq-lrtdc-1ch/          # config.sh、setup.sh：入力マスク
    └── nestdaq/
        ├── common/                   # 共通のサービス・パラメータ・トポロジー・制御
        ├── amaneq-lrtdc-1ch/
        │   ├── config.sh
        │   ├── fee-setup.sh
        │   ├── run-start.sh
        │   ├── run-stop.sh
        │   ├── run-status.sh
        │   └── run-attach.sh
        └── raris-ac-lgad/             # 再生ヘルパー、rawdata-download.sh

/workspace/spadi/                     # SPADI_LOCAL。ホストの workspace/spadi
├── scripts/                          # 実行設定の編集用コピー
│   ├── fee/amaneq-lrtdc-1ch/
│   └── nestdaq/{common,amaneq-lrtdc-1ch,raris-ac-lgad}/
└── rawdata/
    ├── amaneq-lrtdc-1ch/00/run000001.dat
    └── raris_ac_lgad_202603/{00,01,02}/run000020.dat
```

リポジトリでは設定は `scripts/fee` と `scripts/nestdaq`、準備ヘルパーは `scripts/runtime/spadi-prepare-runtime.sh` にあります。[公式ハードウェアガイド](https://spadi-alliance.rcnp.osaka-u.ac.jp/ug-amaneq/firmware/strlrtdc/strlrtdc/)と[固定リビジョン](../versions/versions.env)も参照してください。
