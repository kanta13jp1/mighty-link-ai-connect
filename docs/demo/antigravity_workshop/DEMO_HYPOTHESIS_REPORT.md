# Antigravityライブデモ 10仮説検証レポート

実施日: 2026-08-08
対象: `docs/demo/antigravity_workshop/output/index.html`

## 目的

8月26日の社内研修で、合成ヒアリングメモから生成した提案画面を短時間で確認できるようにする。見た目だけでなく、入力事実との一致、人による最終判断、安全な出力範囲、デスクトップとモバイルの実描画を検証する。

## 検証結果

| 仮説 | 合否 | 合格条件 | 実測・証拠 |
| --- | --- | --- | --- |
| H1 入力事実を保つ | PASS | 会社情報、課題、提案、3スコア、次アクションが入力と一致し、判定を創作しない | 必須14項目すべて存在。「高適合」「ROI」「削減率」「導入決定」は0件 |
| H2 判断状態がすぐ分かる | PASS | 会社名、レビュー状態、送付制限を上部に表示 | 「提案判断サマリー」「営業責任者レビュー待ち」「社外送付不可」を表示 |
| H3 視線順序が固定される | PASS | 課題、提案、スコア、次アクションの順に並ぶ | section IDのDOM順が指定4項目と一致 |
| H4 公式ブランド色を守る | PASS | `#00A5E3`と`#EF7E00`を使用する | 2色をアクセントに限定し、背景は中立色で構成 |
| H5 スコアを説明できる | PASS | 82、76、68を参考値として示し、最低値を確認事項へ接続 | progressbar 3件。データ準備68点を「確認優先」として次アクションへ接続 |
| H6 人の判断を外さない | PASS | レビュー担当と最終判断を明示する | レビュー待ち、営業責任者レビュー、顧客送付は人が行うことを表示 |
| H7 安全なデモに閉じる | PASS | 合成データ、外部参照なし、実行要素なし | `SYNTHETIC_DATA_ONLY`あり。外部URL 0、script/form/input/iframe 0 |
| H8 デスクトップ1画面に収まる | PASS | 1440x900でページスクロール、重なり、文字溢れがない | scroll 1440x900、主要領域重なり0、文字溢れ0、4 section表示 |
| H9 モバイル幅で破綻しない | PASS | 390x844で横スクロール、重なり、文字溢れがない | scrollWidth 390、重なり0、文字溢れ0。全体高は1701pxから1432pxへ15.8%短縮 |
| H10 構造を読み上げ可能にする | PASS | landmark、見出し階層、progressbar ARIAを持つ | header/main/footer、h1 1件、h2 4件、ARIA progressbar 3件、section 4件 |

## 証拠

- [デスクトップ 1440x900](../../../exports/antigravity_demo_hypothesis_evidence/desktop_1440x900.png)
- [モバイル 390x844](../../../exports/antigravity_demo_hypothesis_evidence/mobile_390x844.png)
- [Playwright実測値](../../../exports/antigravity_demo_hypothesis_evidence/render_metrics.json)
- 自動検証: `python scripts/run_antigravity_live_demo.py`
- 回帰テスト: `python -m pytest tests/test_antigravity_live_demo.py -q`

## 限界

- 2つの代表viewportで検証しており、全端末・全ブラウザの網羅ではない。
- DOMとARIAは検証したが、実機スクリーンリーダーによる利用者試験は未実施。
- 8月26日のライブ実行ではAntigravityがHTMLを再生成するため、実行後に同じ検証コマンドとブラウザ確認を行う。
