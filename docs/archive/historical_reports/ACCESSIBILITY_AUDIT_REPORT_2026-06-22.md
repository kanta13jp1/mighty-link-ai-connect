# アクセシビリティ監査レポート 2026-06-22

- 対象WBS: T799
- 対象画面: 公開デモ `index.html`
- 基準: WCAG 2.2 AA を主対象
- 実行日: 2026-06-22
- レーン: Antigravity + Gemini / VSCode + Codex

## 結論

公開デモの主要画面について、axe-core 4.11.4 の WCAG 2.0/2.1/2.2 A/AA タグ監査を実行し、修正前4件から修正後0件まで改善した。あわせて、プロジェクト固有の静的アクセシビリティゲートを追加し、スキップリンク、主要フォームラベル、フォーカスリング、タブ/進捗バー/チャート/動画のアクセシブル名、横スクロール領域のキーボード到達性を継続検証できるようにした。

## 修正前

実行コマンド:

```powershell
npx --yes @axe-core/cli file:///C:/Users/kanta/GitHub/mighty-link-ai-connect/index.html --chrome-path C:\Users\kanta\.browser-driver-manager\chrome\win64-150.0.7871.24\chrome-win64\chrome.exe --chromedriver-path C:\Users\kanta\.browser-driver-manager\chromedriver\win64-150.0.7871.24\chromedriver-win64\chromedriver.exe --tags wcag2a,wcag2aa,wcag21a,wcag21aa,wcag22aa --save exports/a11y_t799_before.json
```

結果:

- `scrollable-region-focusable`: 1件
- `target-size`: 3件
- 合計: 4件

## 修正内容

- ナビゲーションと言語切替リンクのタッチターゲットを `min-height: 32px` / `min-width: 32px` に拡張。
- 全主要インタラクティブ要素に `:focus-visible` の明示フォーカスリングを追加。
- スキップリンクを追加し、`main#top` へキーボードで直接移動できるようにした。
- Engineer/Job入力欄とフィードバックコメント欄に明示ラベルを追加。
- 横スクロールが必要な候補者比較テーブルのラッパーへ `tabindex="0"` と説明ラベルを追加。
- 装飾用ヒーロー動画をアクセシビリティツリーから除外し、意味のあるStory動画にはラベルを付与。
- レーダーチャートの `canvas` に `role="img"`、説明ラベル、fallback textを追加。
- スコア進捗バーへ `role="progressbar"`、`aria-valuemin/max/now`、軸ごとのラベルを追加し、JSアニメーション中も更新するようにした。
- Q&A/ロードマップ切替に `tablist` / `tab` / `tabpanel` と `aria-selected` を追加。

## 修正後

実行コマンド:

```powershell
npx --yes @axe-core/cli file:///C:/Users/kanta/GitHub/mighty-link-ai-connect/index.html --chrome-path C:\Users\kanta\.browser-driver-manager\chrome\win64-150.0.7871.24\chrome-win64\chrome.exe --chromedriver-path C:\Users\kanta\.browser-driver-manager\chromedriver\win64-150.0.7871.24\chromedriver-win64\chromedriver.exe --tags wcag2a,wcag2aa,wcag21a,wcag21aa,wcag22aa --save exports/a11y_t799_after.json --exit
```

結果:

- axe violations: 0
- 静的ゲート: `python scripts/check_accessibility_static.py --json-output exports/a11y_t799_static.json`
- 静的ゲート結果: 14/14 PASS
- pytest: `tests/test_accessibility_static.py` を追加

## 残リスク

自動監査はアクセシビリティ問題の一部しか検出できないため、公開・有償ローンチ前には次の手動確認を行う。

- キーボードのみで主要導線を操作できること。
- スクリーンリーダーでフォーム、タブ、結果、比較テーブルの読み上げ順が自然であること。
- 実データ表示時に日本語テキスト、長いスキル名、エラー状態がUIからはみ出さないこと。

## 参照

- W3C WCAG 2.2: https://www.w3.org/TR/WCAG22/
- Deque axe-core documentation: https://www.deque.com/axe/core-documentation/api-documentation/
- 成果物: `exports/a11y_t799_before.json`, `exports/a11y_t799_after.json`, `exports/a11y_t799_static.json`
