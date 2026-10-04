# 定量試験の再実行（Windows Python、Docker不要）

Python 3.10以降と標準ライブラリだけを使います。`benchmark.py`はキーを
環境変数`OPENAI_API_KEY`からだけ読みます。`.env`、設定ファイル、コマンド引数、
ソースコードにはキーを保存しません。HTTPエラー本文やリクエストヘッダーも記録しません。

PowerShellでリポジトリのルートに移動します。

```powershell
cd C:\Users\kobayash\Documents\codex\spadi-containers-second-trial
git switch research/ai-monitor-pilot
python experiments/ai-monitor-pilot/test_benchmark.py
python experiments/ai-monitor-pilot/benchmark.py download
```

`python`がPATHにない場合は、インストール済みPythonの絶対パスに置き換えてください。
今回の実行ではCodexに付属するWindows Python 3.12.14を使用しました。

```powershell
$python = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $python --version
```

以下の`python ...`は`& $python ...`でも実行できます。PowerShellのスクリプト実行ポリシーを
変更する必要はありません。

## 保存済み試験を確認する

大量の観測入力は、元のJSONバイト列を保持する`frozen-inputs.zip`に保存しています。
別のPCへcloneした後に保存済み試験の検証・集計を再実行するときは展開してください。

```powershell
python -m zipfile -e experiments/ai-monitor-pilot/results/quantitative-v1/frozen-inputs.zip experiments/ai-monitor-pilot/results/quantitative-v1
python experiments/ai-monitor-pilot/benchmark.py report
```

展開後の入力ハッシュは`freeze.json`と一致します。日本語の集計・AWS申請補足文案は
`results/quantitative-v1/RESULTS-ja.md`、全60件の実行状況は`outcome-summary.json`にあります。

## 新しい試験を作る

既存の凍結結果は上書きできません。新しい出力先を指定します。

```powershell
$out = '.local/repeat-01'
python experiments/ai-monitor-pilot/benchmark.py prepare --output $out
python experiments/ai-monitor-pilot/benchmark.py conventional --output $out
```

公開データは固定リビジョンからダウンロードし、既存の3つのSHA-256と
8,470フレームの総数を照合します。各ソースの前半だけでID増分、FEM、メッセージ数、
データ量しきい値を決めます。後半は評価用です。ストリーム間の同期は仮定しません。

`prepare`で判定条件・プロンプト・モデル・入力・正解・実装のハッシュを凍結します。
変更があれば評価は拒否されます。今回の凍結結果は
`results/quantitative-v1/freeze.json`にあります。

## APIキーを非表示入力する

キーがない場合、APIコマンドはリクエストを送信せず終了します。
キーはチャットに貼らず、同じPowerShellで次を実行してください。

```powershell
$secret = Read-Host 'OPENAI_API_KEY' -AsSecureString
$env:OPENAI_API_KEY = [System.Net.NetworkCredential]::new('', $secret).Password
Remove-Variable secret
```

これはそのPowerShellと子プロセスだけに設定します。値を表示するコマンドは実行しません。
試験終了後は次で解除できます。

```powershell
Remove-Item Env:OPENAI_API_KEY
```

今回のみ、ユーザーが許可してWindowsユーザー環境変数に一時保存しました。
実行用PowerShellがその値を自身の環境変数へ引き継ぎ、Pythonは環境変数から読みました。
今回の保存分は試験終了後に削除します。通常の再実行には永続保存は必要ありません。

## 少数ケースから本試験へ

```powershell
python experiments/ai-monitor-pilot/benchmark.py pilot --output $out --budget-usd 0.10
Get-Content "$out/pilot-usage.json"
```

開発用5ケース（未加工1件と人工異常4種類を各1件）で試します。
`pilot-usage.json`にAPI報告の入力・出力・キャッシュ済みトークン、実測待ち時間、
料金表から計算した費用見積もり、評価60ケースへの線形外挿を保存します。
費用は請求書の実額ではありません。公式料金の取得日とURLは`protocol.json`にあります。
モデルは`gpt-4.1-mini-2025-04-14`に固定しています。

5件が成功し、使用量と予測を確認してから次を実行します。

```powershell
python experiments/ai-monitor-pilot/benchmark.py evaluate --output $out --budget-usd 1.00
python experiments/ai-monitor-pilot/benchmark.py report --output $out
Get-Content "$out/REPORT.md"
```

予算はコマンドごとの上限です。未実行分の入力バイト数、付加トークンの余裕、
最大出力から保守的な費用枠を確保し、超過する場合は新規リクエストを送信しません。
送信済みリクエスト（出力検証失敗を含む）は再送せず、結果を1件ごとに保存します。HTTP・通信・出力検証の
失敗時は停止し、自動リトライしません。出力検証失敗後も未送信ケースを試す場合は同じ`evaluate`コマンドをもう一度実行します。
今回もこの方法で全60ケースを1回ずつ試しました。失敗応答の本文は保存していないため、
拒否理由の事後診断には限界があります。失敗ケースを成功扱いにせず、未完の種類の
検出率は`null`にします。通信失敗時に使用量が返らなければ、請求額は不明です。

## 保存物と評価の読み方

- `integrity.json`: 実ファイルのハッシュ、構造、ID増分、時刻の整合性。
- `protocol.json` / `freeze.json`: 判定条件、採点条件、プロンプト、凍結ハッシュ。
- `inputs.json`: 検出器に渡す観測レコードだけ。元の位置や正解は含みません。
- `labels.json`: 種類、元フレーム位置、ファイル内バイト位置、観測列の採点対象位置。
- `conventional.json`: データ量判定と構造ルール判定の個別出力・時間。
- `ai-pilot.json` / `ai-evaluation.json`: AIの個別出力、API報告モデル・使用量・時間。
- `pilot-usage.json` / `evaluation-usage.json`: 使用量と費用推計。
- `metrics.json` / `REPORT.md`: 集計と限界。

検出は注入対象位置に重なる警報だけを数え、種類識別には正しい種類も要求します。
人工欠落の採点位置は欠落直後の観測レコード、重複は後のコピー、順序交換は交換した
2レコード、ヘッダー破損は当該レコードです。無関係な位置への警報に検出の点は与えません。
ヘッダー破損はmagic・総長・ヘッダー長・usecの4パターンをバイト単位で実際に変更します。
元データと`labels.json`から再現できます。欠落・重複・順序交換も実レコードの列を変更します。

従来手法とAIは同じヘッダー、デコード値、観測バイト長、ペイロードハッシュを受け取ります。
AIには元のペイロード全体、正解、注入位置、ルール判定の出力を渡しません。
独立したレコード境界を保持するため、破損した連続バイト列からの再同期性能は未測定です。

未加工12区間の警報と人工異常への検出を分けます。従来手法だけでは後半4,236フレーム、
133区間すべてにも警報検査を行います。この広い検査とAIの選択12区間は範囲が違います。
未加工の警報は自然異常候補であり、真の異常とも誤警報とも断定しません。
同じrunの前半・後半であり、別runでの汎化、真のburst、自然故障に対する精度・再現率、
イベントレート、DAQのストリーミング性能は測っていません。
4種類を組み合わせた異常や高度なヘッダー破損も今回の対象外です。

AWS申請に使う場合は、この範囲と未測定項目を併記してください。Submitは行いません。
