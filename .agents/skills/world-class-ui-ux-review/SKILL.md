---
name: world-class-ui-ux-review
description: Execute uncompromising, rigorous UI/UX audits with live interaction routing checks, duplicate navigation detection, vertical stack verification, syntax/runtime error zero-tolerance, and Figma REST API Design Token sync to eliminate UI drift.
---

# World-Class UI/UX Review Skill (Rigorous Interactive & Quality Audit)

単なる静的コード検証にとどまらず、**実際のユーザー操作（縦並びレイアウト、クリック遷移、ナビゲーション重複、タブ切り替え、レイアウト破綻、JavaScript構文・実行時エラーゼロ、Markdown/Mermaidプレビュー描画、同一タブ内遷移・タブ増殖防止）の完全動作を検証**し、甘い自己評価（形式的な満点）を徹底的に排除する厳格な UI/UX 監査プロトコルです。

---

## 🎯 必須検証チェックリスト（実動品質 7 大ゲート）

レビュー実行時は、以下の**「実動品質 7 大ゲート」**を必ず自動テストおよびブラウザ実動で検証し、1 つでも不備があれば減点・即時指摘します：

1. **JavaScript 構文 ＆ 実行時エラーゼロ・ゲート (Syntax & Zero-Error Gate)**:
   - 全 `<script>` タグ内に構文エラー（余分な `}`、未定義呼び出し等）が一切なく、`python scripts/find_js_syntax_errors.py` (Node.js `--check`) が全スクリプトブロックで完全パスすること。
   - ブラウザコンソールに uncaught exception（`pageerror`）が 0 件であること。
2. **垂直スタック・サイドバーレイアウト検証 (Vertical Stack Gate)**:
   - サイドメニュー項目が `flex-direction: column` で整然と縦並びに並んでいるか。横並び（2カラム崩れ）や文字見切れがないか。
   - 「ホーム」「営業メールマッチング」「管理者ダッシュボード」「勤怠管理」「適性アンケート」「自己診断デモ」「初期セットアップ」「研修ガイド」の全 8 項目が漏れなく表示されているか。
3. **ナビゲーション重複チェック (Duplicate Menu Gate)**:
   - ヘッダー、サイドバー、フッター、ページ内コンテンツ間で同一の機能リンクが重複して混乱を招いていないか。フッターに重複メニュー列が残存していないか。
4. **ルーティング・タブ遷移の実動チェック (Interactive Route & View Unification Gate)**:
   - 全てのメニュー項目をクリックした際に、意図した専用ビューが右側メインエリアで排他表示され、無関係な要素が残留しないか。
   - 「研修ガイド」等の主要機能が旧モーダル（`#training-modal`）ではなく、専用タブビュー（`<section id="training-section" class="app-tab-view internal-section">`）として統合されていること（`tests/test_training_modal_ui.py` で検証）。
5. **ドキュメント ＆ シーケンス図 リッチ描画・単一タブゲート (Rich Markdown/Mermaid & Single Tab Gate)**:
   - ドキュメントリンクが Raw テキスト露出（生Markdownや未パースMermaidテキスト、HTMLソースのテキスト化）にならず、Marked.js / Mermaid.js によりグラフィック・HTMLとして美しくレンダリングされているか。
   - 内部資料リンクに `target="_blank"` が付いておらず、同一タブ内でシームレスに遷移・復帰できること（`tests/test_doc_single_tab_flow.py` でタブ数 1 を検証）。
6. **Figma ワイヤーフレーム全 8 画面同期 & 配置ガイド (Figma Location Gate)**:
   - 全 8 画面（①ホーム、②営業マッチング、③管理者ダッシュボード、④勤怠管理、⑤適性アンケート、⑥自己診断デモ、⑦初期セットアップ、⑧研修ガイド）の SVG アートボードが生成され、Figma 上の配置情報が明記されているか。
7. **過大評価の防止と客観的採点 (Objective Score Gate)**:
   - 形式的な満点（100点）を禁止し、実動作・エルゴノミクス・認知負荷・テスト通過エビデンスの観点からシビアに採点（実態ベースの厳格評価）。

---

## 🎨 Figma ワイヤーフレームの構成・展開情報

全 8 画面のワイヤーフレームは [`scripts/generate_figma_wireframes.py`](file:///c:/Users/kanta/GitHub/mighty-link-ai-connect/scripts/generate_figma_wireframes.py) により完全生成され、以下の構成で展開されます：

1. **Figma プロジェクト情報**:
   - **プロジェクト URL**: [Figma Project - Mighty Skill-Bridge](https://www.figma.com/design/aiQt3c1Cenru4x6GMcLuL5)
   - **対象 Page**: `Page 1`
2. **生成 SVG アートボード一覧 (`exports/figma_wireframes/`)**:
   - `00_home_fit_simulator.svg` (Frame 0: ホーム / AIフィットシミュレーター)
   - `01_sales_matching_hub.svg` (Frame 1: 営業メールAIマッチング & 提案ハブ)
   - `02_admin_dashboard.svg` (Frame 2: 管理者統合ダッシュボード & 監査ログ)
   - `03_attendance_management.svg` (Frame 3: 勤怠管理 & 36協定AI解析)
   - `04_survey_assessment.svg` (Frame 4: 従業員適性・状況アンケート)
   - `05_aptitude_demo.svg` (Frame 5: 自己診断デモ & 面談活用ガイド)
   - `06_onboarding_setup.svg` (Frame 6: 初期セットアップ & アカウント有効化)
   - `07_training_guide_curriculum.svg` (Frame 7: 社内役割別研修ガイド 3コース統合タブ)
   - `mighty_link_full_wireframe_artboard.svg` (全画面統合マスターアートボード: 6200x2200)
3. **展開手順**:
   - **ドラッグ＆ドロップ**: [`exports/figma_wireframes/mighty_link_full_wireframe_artboard.svg`](file:///c:/Users/kanta/GitHub/mighty-link-ai-connect/exports/figma_wireframes/mighty_link_full_wireframe_artboard.svg) を Figma キャンバスへドラッグ＆ドロップ。
   - **Live Plugin Bridge**: Figma 上でプラグインを開いた状態で `python scripts/send_to_figma.py --svg exports/figma_wireframes/mighty_link_full_wireframe_artboard.svg` を実行。
