# バイト列復旧・反復再生の追加試験

前回のフレーム境界を保持した試験に追加して、連続バイト列の破損と復旧を測定した。公開3ファイル8,470フレームの既存ハッシュを照合し、最初の半分だけから参照値を決めた。
評価前に実装・入力・正解・評価条件をハッシュで固定。評価は後半の12区間を基に未加工12ケースと人工介入96ケースを作成。512/4096/65536バイトの読み取りで同じケースを再試験した。検出器は連続バイト列と開発用参照だけを受け取り、境界・注入位置・正解は採点側に分離した。

## 復旧と検出（4096バイト読み取り）

| 人工介入 | strict 全イベント検出ケース | resync 全イベント検出ケース | strict 無変更レコード復旧 | resync 無変更レコード復旧 |
|---|---:|---:|---:|---:|
| missing | 12/12 | 12/12 | 756/756 | 756/756 |
| duplicate | 12/12 | 12/12 | 780/780 | 780/780 |
| reorder | 12/12 | 12/12 | 768/768 | 768/768 |
| header_magic | 12/12 | 12/12 | 291/756 | 756/756 |
| header_length | 12/12 | 12/12 | 343/756 | 756/756 |
| garbage | 12/12 | 12/12 | 344/768 | 768/768 |
| payload_truncation | 0/12 | 0/12 | 359/756 | 744/756 |
| mixed | 12/12 | 12/12 | 480/756 | 756/756 |

読み取りサイズ間で採点と警報位置が一致: {'strict': True, 'resync': True}。

復旧は元の無変更レコードのSHA-256と出現回数の一致で採点する。破損レコードは無変更レコードの分母から除外し、削除データを復元したとは主張しない。複合ケースでは欠落・重複・ヘッダー破損の3イベントすべての位置と種類が必要。

## 未加工データの候補警報

- strict: 12区間、警報0件、無変更レコード復旧768/768。
- resync: 12区間、警報0件、無変更レコード復旧768/768。

これは自然異常の正解ではなく、警報0件でも正常とは断定しない。

## Windowsホストでの反復処理性能

Python 3.12.14、Windows-11-10.0.26200-SP0。各条件3試行の中央値。コーパスは事前にメモリへ読み込み、各パスでレコード抽出・ハッシュ計算・64件の重複履歴・ID差検査を行った。各ソース/再生回で状態をリセットする。

| 方法 | 反復係数 | 処理フレーム/試行 | 秒（中央値） | フレーム/秒（中央値） | MiB/秒（中央値） |
|---|---:|---:|---:|---:|---:|
| strict | 1 | 8,470 | 0.0204 | 415,746 | 95.82 |
| strict | 10 | 84,700 | 0.1646 | 514,714 | 118.63 |
| strict | 100 | 847,000 | 1.5562 | 544,292 | 125.44 |
| resync | 1 | 8,470 | 0.0155 | 546,720 | 126.00 |
| resync | 10 | 84,700 | 0.1552 | 545,716 | 125.77 |
| resync | 100 | 847,000 | 1.5556 | 544,487 | 125.49 |

繰り返しは同じ8,470フレーム。100倍再生も847,000件の独立データや実故障ではない。I/O・ネットワーク・AWS・実時間DAQの性能を示す値ではない。

## メモリ（時間測定とは別試行）

- strict / 1倍: Python追跡ピーク 29,908バイト。
- strict / 100倍: Python追跡ピーク 29,908バイト。
- resync / 1倍: Python追跡ピーク 29,908バイト。
- resync / 100倍: Python追跡ピーク 29,908バイト。

tracemalloc開始前に読み込んだコーパスとプロセス全体のRSSは含まない。処理器の追加Python割当だけを測っており、全体メモリ使用量とは呼ばない。

## 申請への使い方と限界

申請には、この実測値を「ローカルで再現可能な監視・復旧の予備検証」として使用できる。AI診断の前段に必要なデータ整合性監視について、破損後に継続できる範囲と処理コストを定量化した。
AWSクレジットによる今後の課題は、独立runと専門家確認済み故障の収集、曖昧・欠落・矛盾する文脈に対する診断、クラウド上の並列処理・実運用I/Oの測定である。今回AWSを必要とした／AWSでこの速度を達成したとは主張しない。
前回のAI結果は維持しており、AIの優位性は未確認。今回API呼出し・トークン・追加API費用は0。AWS申請のSubmitは実行していない。

- Same public run; no natural fault truth or independent run.
- Repeated workload does not increase unique record or independent fault count.
- Resynchronization uses development header constraints and next-header plausibility; not a payload decoder or authenticated framing proof.
- All byte mutations and combinations are artificial; no actual detector burst tested.
- FileSink envelope is inspected before replay; envelope corruption and network transport are untested.
- Windows host performance only; AWS, network, disk and real-time DAQ throughput unmeasured.
- No new AI calls or AI superiority measurement.
