# Ten-Pass Self Review

実施日: 2026-08-13 JST

各回で観点を変え、問題を見つけた場合は次の回へ進む前に修正した。単に同じ画面を10回見た記録ではない。

## Review 01: 公式出典と最新性

- 指摘: Codexの版番号バッジが一般Changelogを開き、`0.147.0`の直接証拠まで一段遠かった。
- 修正: バッジを公式GitHubの`rust-v0.147.0`リリースへ直結し、一般Changelogは出典台帳に残した。
- 証拠: 公式URL 37件を2026-08-13に再取得。36件がHTTP 200。ChatGPT料金ページのみBot保護で403となったが、公式URL自体は維持した。

## Review 02: 公式アイコンの真正性

- 指摘: 旧画面は文字アイコンや汎用記号が混ざり、製品を視覚的に識別しにくかった。
- 修正: 各社の公式プロパティから取得した5点を`assets/product-icons/`へ保存し、出典を`ICON_SOURCES.md`と画面内の出典台帳に記載した。
- 証拠: Chromiumで5画像の`naturalWidth`と`naturalHeight`が0より大きいことを確認。最小でもCodexの48x48で、カード表示42x42を満たす。

## Review 03: 比較対象のスコープ

- 指摘: リハーサル版は9製品まで増え、発表対象である5製品の説明が浅くなっていた。
- 修正: Codex、Claude Code、Claude Cowork、Kiro、Antigravityの5製品へ限定し、Devin、Cursor Agent、Windsurf、Copilot Workspaceを現行UIとデータから削除した。
- 証拠: `test_exact_product_scope`と`test_removed_rehearsal_products_are_absent`が対象集合と旧名称の不在を検証する。

## Review 04: 選定に使える情報か

- 指摘: 機能の羅列だけでは、利用者が自分の仕事から候補を絞れなかった。
- 修正: コード、ナレッジワーク、仕様駆動、Web画面検証、自動化SDKのシナリオ絞り込みと全文検索を追加した。各カードに「選ぶ理由」と「別候補も見る条件」を併記した。
- 証拠: ブラウザ操作でシナリオ切替、検索、カード表示件数、選択状態を確認した。

## Review 05: 料金と利用枠の誠実さ

- 指摘: 旧データに、公式根拠のない固定日次回数や月次PUが含まれていた。
- 修正: 公開価格はプラン表記に限定し、変動する上限はモデル、作業量、地域、共有capacityで変わると明記した。
- 証拠: `test_variable_limits_are_not_fabricated`が旧来の架空表記を禁止する。

## Review 06: 詳細比較の十分性

- 指摘: 向いている仕事と機能名だけでは、導入・運用・安全性の差を判断できなかった。
- 修正: 操作面、持続指示、拡張、MCP、Browser、並列実行、SDK、証拠、安全境界、導入注意を含む13軸へ拡張した。
- 証拠: 2製品選択時に13行が生成されることをChromiumで確認し、全製品のキー集合を自動テストで固定した。

## Review 07: バージョン表記の意味

- 指摘: モデル版と製品版を混同する恐れがあり、Antigravityのラベルも`Antigravity 2.0`と版番号`2.8.0`が競合して見えた。
- 修正: ラベルを`Antigravity`に統一。Claude Coworkはモデル版を代用せず、`公開版番号なし（SaaS）`と明記した。
- 証拠: 4製品の数値版とCoworkの非公開表記を`EXPECTED_VERSIONS`で検証する。

## Review 08: アクセシビリティと操作安全性

- 指摘: 出典台帳には同じ「公式ブログ」等のリンク名が並び、スクリーンリーダーのリンク一覧だけでは製品を判別しにくかった。
- 修正: 各リンクへ`製品名: 出典種別を開く`の`aria-label`を付けた。比較は最大2件、状態は`aria-pressed`、結果は`aria-live`で通知する。
- 証拠: キーボードフォーカス、reduced motion、ARIA属性、3件目を拒否する状態文を自動・ブラウザ双方で確認した。

## Review 09: デスクトップ表示

- 指摘: 情報量が多いため、更新、動画、ブログ、比較操作の視線順序が崩れるリスクがあった。
- 修正: 1440x900で、製品名と版番号、適合条件、更新、メディア、詳細、比較操作の順にカードを固定。2列で本文幅を確保した。
- 証拠: `assets/review/desktop-1440x900.png`を目視確認。ページ幅1440pxに対してdocument幅1440px、コンソールエラー0件だった。

## Review 10: モバイルと敵対的最終確認

- 指摘: 詳細カードと40本の出典リンクにより、390px幅で横スクロールや重なりが起きる可能性があった。
- 修正: カードを1列化し、版番号を独立行、比較表だけを内部スクロール領域にした。第三候補、空検索、古い製品名、架空上限、欠損画像を最終確認項目に含めた。
- 証拠: `assets/review/mobile-390x844.png`を目視確認。viewport幅390pxとdocument幅390pxが一致し、5アイコン読み込み、40出典リンク、コンソールエラー0件を確認した。比較表示は`assets/review/comparison-1440x900.png`で確認した。

## Final Gate

- `python -m unittest discover -s tests -v`: 11 tests
- `node --check app.js`: pass
- `node --check product-data.js`: pass
- Chromium 1440x900 and 390x844: pass
- Maximum comparison selection: 2 products
- Detailed comparison rows: 13
- Source links rendered: 40
