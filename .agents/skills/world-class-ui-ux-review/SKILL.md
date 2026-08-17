---
name: world-class-ui-ux-review
description: Execute uncompromising, rigorous UI/UX audits with live interaction routing checks, duplicate navigation detection, vertical stack verification, syntax/runtime error zero-tolerance, and Figma REST API Design Token sync to eliminate UI drift.
---

# World-Class UI/UX Review Skill (Rigorous Interactive & Quality Audit)

単なる静的コード検証にとどまらず、**実際のユーザー操作（縦並びレイアウト、クリック遷移、ナビゲーション重複、タブ切り替え、レイアウト破綻、JavaScript構文・実行時エラーゼロ、Markdown/Mermaidプレビュー描画）の完全動作を検証**し、甘い自己評価（形式的な満点）を徹底的に排除する厳格な UI/UX 監査プロトコルです。

---

## 🎯 必須検証チェックリスト（甘さの徹底排除・7大ゲート）

レビュー実行時は、以下の**「実動品質 7 大ゲート」**を必ず検証し、1 つでも不備があれば減点・即時指摘します：

1. **JavaScript 構文 ＆ 実行時エラーゼロ・ゲート (Syntax & Zero-Error Gate)**:
   - 全 `<script>` タグ内に構文エラー（余分な `}`、未定義呼び出し等）が一切なく、`node --check` が完全パスすること。
   - ブラウザコンソールに uncaught exception（`pageerror`）が 0 件であること。
2. **垂直スタック・サイドバーレイアウト検証 (Vertical Stack Gate)**:
   - サイドメニュー項目が `flex-direction: column` で整然と縦並びに並んでいるか。横並び（2カラム崩れ）や文字見切れがないか。
   - 「ホーム」「営業メールマッチング」「管理者ダッシュボード」「勤怠管理」「適性アンケート」「自己診断デモ」「初期セットアップ」「研修ガイド」の全 8 項目が漏れなく表示されているか。
3. **ナビゲーション重複チェック (Duplicate Menu Gate)**:
   - ヘッダー、サイドバー、フッター、ページ内コンテンツ間で同一の機能リンクが重複して混乱を招いていないか。フッターに重複メニュー列が残存していないか。
4. **ルーティング・タブ遷移の実動チェック (Interactive Route & View Unification Gate)**:
   - 全てのメニュー項目をクリックした際に、意図した専用ビューが正確に表示され、無関係な要素が残留しないか。
   - 「研修ガイド」等の主要機能が不自然なモーダルポップアップではなく、統一されたタブビュー（`<section class="app-tab-view">`）として統合されているか。
5. **ドキュメント ＆ シーケンス図 リッチ描画ゲート (Rich Markdown & Mermaid Gate)**:
   - ドキュメントリンクが Raw テキスト露出（生Markdownや未パースMermaidテキスト）にならず、Marked.js / Mermaid.js によりグラフィック・HTMLとして美しくレンダリングされているか。
   - リンクが不要に新規タブを増殖させず、同一画面または同一タブ内で戻るナビゲーション（← ホームに戻る）が正常機能するか。
6. **Figma ワイヤーフレーム全画面同期 & 配置ガイド (Figma Location Gate)**:
   - ホーム、営業マッチング、勤怠、診断、管理画面、研修ガイドの全画面が Figma 上のどのファイル（URL）、どのレイヤーに展開されているかをユーザーに明確に提示できるか。
7. **過大評価の防止と客観的採点 (Objective Score Gate)**:
   - 形式的な満点（100点）を禁止し、実動作・エルゴノミクス・認知負荷の観点からシビアに採点（実態ベースの厳格評価）。

---

## 🎨 Figma ワイヤーフレームの配置・インポート手順

Figma 上のワイヤーフレームは以下の方法で完全に確認・利用可能です：

1. **Figma ファイル情報**:
   - **プロジェクトファイル**: `Mighty Skill-Bridge Antigravity User Guide` / `Untitled` (URL: `https://www.figma.com/design/aiQt3c1Cenru4x6GMcLuL5`)
   - **生成ワイヤーフレーム SVG**: [`exports/figma_wireframes/mighty_link_full_wireframe_artboard.svg`](file:///c:/Users/kanta/GitHub/mighty-link-ai-connect/exports/figma_wireframes/mighty_link_full_wireframe_artboard.svg) (全 6 画面統合アートボード)
2. **手動インポート / ドラッグ＆ドロップ**:
   - [`exports/figma_wireframes/mighty_link_full_wireframe_artboard.svg`](file:///c:/Users/kanta/GitHub/mighty-link-ai-connect/exports/figma_wireframes/mighty_link_full_wireframe_artboard.svg) を Figma の任意のキャンバスへドラッグ＆ドロップすることで、全 6 画面のベクターアートボードが即座に展開されます。
3. **Figma Live Plugin Bridge による自動描画**:
   - Figma 上で Live Plugin を実行した状態で `python scripts/send_to_figma.py --svg exports/figma_wireframes/mighty_link_full_wireframe_artboard.svg` を実行すると、キャンバス中央にアートボードが直接挿入されます。
