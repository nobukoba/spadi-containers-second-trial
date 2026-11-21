# RARiS の ARTEMIS Offline／Online 解析

このチュートリアルを含む新しい `spadi-user-full` を使います。ARTEMIS、ROOT、
NestDAQ と C++ コンパイラーが必要ですが、検出器ハードウェアは不要です。公開
RARiS run 20 の３個の FileSink v1 STF ファイルを解析します。ヒストグラムの
チャンネル、TDC、TOT は未較正の生値であり、較正済み時間や電荷ではありません。

コンテナ内で作業領域を準備し、データを取得して Offline 解析します。
準備コマンドは既存の設定を上書きしません。以前のイメージからコピーした
レシピがある場合は、新しいイメージの `config.sh` と比較してから固定済み
マニフェストを利用してください。

```bash
spadi-prepare-local.sh
cd "$SPADI_LOCAL/scripts/nestdaq/raris-ac-lgad"
./rawdata-download.sh
mkdir -p "$SPADI_LOCAL/raris-results"
/opt/spadi/scripts/artemis/raris-ac-lgad/run.sh offline \
  "$SPADI_LOCAL/raris-results/offline.root"
```

Offline は３ソースの STF ID を照合し、最初のファイル終端で停止します。共通の
2,815 STF を解析し、ソース 01 にだけある末尾 25 STF は含みません。入力エラーや
ゼロ件はコマンド失敗になります。ROOT ファイルには `channel`、`tdc`、`tot` と
TF／HBF／ヒットのカウンターが入ります。

Online は同じコンテナ内の２つのシェルを使います。まず既存のリプレイを起動します。

```bash
cd "$SPADI_LOCAL/scripts/nestdaq/raris-ac-lgad"
./run-start.sh
./run-status.sh
```

別のシェルで、DAQ の RUN より**先に**受信側を開始します。

```bash
/opt/spadi/scripts/artemis/raris-ac-lgad/run.sh online \
  "$SPADI_LOCAL/raris-results/online.root"
```

ホストのブラウザーで `http://127.0.0.1:8080` を開き（Docker ではポート 8080 を
公開）、Control Targets の両方を `all` のままにして、各状態遷移の完了後に
INIT DEVICE、INIT TASK、RUN を順に押します。INIT DEVICE は CONNECT コマンドを送ります。
受信開始から 30 秒以内に RUN してください。余裕が必要なら Online コマンドの前に
`RARIS_TIMEOUT_MS=120000` を設定します。TF が 30 秒間届かなければ受信を終了して
保存します。ゼロ件なら失敗し、途中終了も比較によって検出します。サンプルでは
2,815 TF、33,780 ソース HBF、68,956 ヒット、全ヒストグラムの差分ゼロを期待します。

```bash
/opt/spadi/scripts/artemis/raris-ac-lgad/compare.sh \
  "$SPADI_LOCAL/raris-results/offline.root" \
  "$SPADI_LOCAL/raris-results/online.root"
root -l "$SPADI_LOCAL/raris-results/online.root"
```

`TFB_DECIMATION_FACTOR=1000` は別の `decimator` チャンネルに適用されます。
ポート 5501 の `out` は間引かれません。不完全 TF の出力が無効なので、ソース 01
だけの末尾 25 STF は出力されません。実際の出力はリプレイのタイミングに依存する
ため、件数やビンが一致しない場合は比較失敗として扱ってください。

終了後、最初のシェルでリプレイを停止します。

```bash
cd "$SPADI_LOCAL/scripts/nestdaq/raris-ac-lgad"
./run-stop.sh
```

Redis／Valkey が残る場合は、この実行で起動したもので、他の作業が利用していない
ことを確認してから停止してください。結果ファイルは不要になったら削除できます。
タイムアウト時は DAQ 状態、ポート 5501、入力パス、RUN より前に受信を開始したかを
確認してください。実データとリプレイの HBF 並び順の根拠は
[調査記録](../experiments/raris-ordering/README.md)にあります。

```bash
/opt/spadi/scripts/artemis/raris-ac-lgad/test-actual.sh \
  "$SPADI_LOCAL/rawdata/raris_ac_lgad_202603" \
  "$SPADI_LOCAL/raris-results/online.root"
```

データ取得先のリビジョンは `container-interfacing-nestdaq-eicrecon` の `ccf94e725389b5d32b2cd167312deb88c6461eba` です。SHA-256 は `config.sh` に記載しています。
