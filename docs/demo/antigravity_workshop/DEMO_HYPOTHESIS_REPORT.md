# Antigravityライブデモ 10仮説検証レポート

実施日: 2026-08-08
対象: 3段階プロンプト、完成版予備サイト、GitHub Pages公開専用リポジトリ

## 検証結果

| 仮説 | 合否 | 合格条件 | 実測・証拠 |
| --- | --- | --- | --- |
| H1 変化が理解できる | PASS | 作成、改善、公開が別プロンプトで進む | 3ファイルに責務を分離し、各段階でブラウザ確認を要求 |
| H2 最初は小さく作れる | PASS | Prompt 1はHTML/CSSと画像だけを生成 | JavaScript、commit、pushを禁止 |
| H3 機能追加を実演できる | PASS | Prompt 2で絞り込みと参加候補選択を追加 | 件数`4,1,1,1,1`、2件選択をPlaywrightで確認 |
| H4 デザイン変更を実演できる | PASS | Prompt 2で公式色とレスポンシブ構成を追加 | `#00A5E3`、`#EF7E00`、デスクトップ1列、モバイル1列を確認 |
| H5 本番と公開先を分離できる | PASS | Prompt 3のremoteを専用リポジトリへ限定 | リポジトリURLとPages URLを完全一致で検証 |
| H6 人が公開を決める | PASS | 正確な承認文言まで書込操作をしない | `公開してもよいですか？`で停止し、`公開して`のみ許可 |
| H7 公開データが安全である | PASS | 合成データ標識、秘密・個人情報なし | `SYNTHETIC_DATA_ONLY`を必須化し、違反時はfail-closed |
| H8 回線障害でも続行できる | PASS | 完成版が外部依存なしでローカル動作 | 外部JS/CSS、API、永続ストレージなし |
| H9 画面が崩れない | PASS | 1440x900と390x844で横溢れ・文字溢れ・console errorなし | 幅は各viewportと一致、画像読込成功、カード4件表示 |
| H10 公開後まで検証できる | PASS | push後にHTTPSと主要機能を再確認 | 専用Pagesの初期デプロイ成功、公開確認手順をPrompt 3へ固定 |

## ブラウザ実測

| 項目 | Desktop 1440x900 | Mobile 390x844 |
| --- | ---: | ---: |
| clientWidth / scrollWidth | 1440 / 1440 | 390 / 390 |
| scrollHeight | 1620 | 2549 |
| 文字溢れ | 0 | 0 |
| console error | 0 | 0 |
| 表示カード | 4 | 4 |

インタラクションはカテゴリ件数`4,1,1,1,1`、参加候補2件、選択名「AIで仕事を整理する / データを見える形にする」を確認した。

## 証拠

- [デスクトップ](../../../exports/antigravity_demo_hypothesis_evidence/desktop_1440x900.png)
- [モバイル](../../../exports/antigravity_demo_hypothesis_evidence/mobile_390x844.png)
- [インタラクション](../../../exports/antigravity_demo_hypothesis_evidence/interaction_1440x900.png)
- [Playwright実測値](../../../exports/antigravity_demo_hypothesis_evidence/render_metrics.json)
- 自動検証: `python scripts/run_antigravity_live_demo.py`
- 回帰テスト: `python -m pytest tests/test_antigravity_live_demo.py -q`

## 残余リスク

会場回線、GitHub Actionsの待ち時間、Antigravity UIの更新は制御できない。90秒で進展がなければ完成版と読み取り専用プロンプトへ切り替え、公開処理は本番リポジトリでは実施しない。
