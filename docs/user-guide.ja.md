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

Valkey、パラメータ、トポロジー、プラグイン、tmux のヘルパーは RARiS 再生と共通です。実機用には Sampler と STFBuilder を使用し、FileSink で TF/STF レコードを保存します。

```bash
cd "$SPADI_LOCAL/scripts/nestdaq/amaneq-lrtdc-1ch"
cat config.sh
ping -c 3 192.168.10.16
./run-start.sh
./run-status.sh
./run-attach.sh
# Ctrl-b d で離れます。収集は続きます。
./run-stop.sh
ls -lh "$SPADI_LOCAL/rawdata/amaneq-lrtdc-1ch/00/run000001.dat"
```

`run-start.sh` は FEE のマスク設定と読み戻し確認、RedisTimeSeries 付き Valkey の起動、パラメータとトポロジーの登録、4プロセスの起動を行います。DeviceReady → Ready → Running の遷移を待ち、下流を先に動かしてから Sampler が TCP 接続します。ブラウザで改めて Run を押す必要はありません。`run-status.sh` は各デバイスの実際の状態を表示し、`run-attach.sh` で sampler、STF0、TFB0、sink0 のログを確認できます。

FEE の Main-U、Main-D、MZN-U、MZN-D のマスクは `ffffffff ffffffff ffffffff ffffffbf` です。102は MZN-D の bit 6 で、1が mask、0が unmask です。他の0〜127入力はすべて mask します。停止中に設定だけを行う場合は `./fee-setup.sh` を実行してください。

IP、run 番号、保存先、ポートは NestDAQ 側の `config.sh` で編集します。ここにある `AMANEQ_IP` が FEE ヘルパーにも渡されます。マスク値は `scripts/fee/amaneq-lrtdc-1ch/config.sh` にあります。次の取得では `RUN_NUMBER` を新しい番号に変更してください。既存の出力ファイルがあれば開始を拒否し、FileSink も `openmode=create` を使用します。稼働中のセッションの設定は変更しないでください。

デフォルトは Valkey `127.0.0.1:6380`（DB0: 登録情報、DB1: メトリクス、DB2: パラメータ）、Web 状態表示 `http://localhost:8081/daq-webctl.html`、データ転送ポート5599〜5601、任意の DQM モニター用 PUB ポート5602です。モニターが接続していなくても、FileSink に DQM チャンネルの定義が必要です。RARiS のデフォルトとは分けています。この設定専用の Valkey DB を使い、他の稼働中の設定と共用しないでください。停止後も Valkey は再利用のため残します。

停止には `run-stop.sh` を使ってください。上流から止めて下流の処理時間を確保し、FileSink の PostRun、トレーラー書き込み、ファイル close を待ってからデバイスと tmux を終了します。エラーやタイムアウト時は調査用に tmux を残します。固定版 upstream は最後の不完全なフレームや FileSink の PostRun に残った入力を破棄する場合があり、run 境界での無損失は保証しません。ログとデリミタのフラグを確認してください。入力がなくてもハートビートデリミタが記録されるため、ファイルの増加だけでは102のヒットを確認できません。保存ファイルは FileSink のヘッダー・トレーラーと TF/STF レコードを含み、以前の `strdaq` の生ストリームとは形式が異なります。

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
