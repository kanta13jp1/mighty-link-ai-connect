# 6/2 社長プレゼン Canva / Figma リデザイン手順 + 8 枚コピペカード

作成日: 2026-05-23
オーナー: VSCode + Claude Code レーン (docs / コピペカード生成) / 実 Canva / Figma 操作は人間 + Antigravity レーン
対応 WBS: **T658-extend** (NotebookLM PPTX → Canva/Figma リデザイン)
関連: [PREP](CEO_PRESENTATION_PREP_2026-06-02.md) / [DECISION_PACK](CEO_PRESENTATION_DECISION_PACK_2026-06-02.md) / [DISCUSSION_POINTS](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md) (T605) / [QA_PACK](CEO_PRESENTATION_QA_PACK_2026-06-02.md) (T607) / [OPS_DISCUSSION](CEO_PRESENTATION_OPS_DISCUSSION_2026-06-02.md) (T606) / [PRESHARE_MEMO](CEO_PRESENTATION_PRESHARE_MEMO_2026-06-02.md) (T614) / [POST_DECISION_ROADMAP](CEO_PRESENTATION_POST_DECISION_ROADMAP_2026-06-02.md) (T615)

---

## このドキュメントの位置づけ

[exports/knowledge_flow/mighty_skill_bridge_ceo_presentation_2026-06-02.pptx](../exports/knowledge_flow/mighty_skill_bridge_ceo_presentation_2026-06-02.pptx) (NotebookLM CLI + python-pptx 自動生成、8 枚) を、Canva (推奨) または Figma のテンプレートを使って **デザイン的に作り直す** ための完全手順書。

ユーザー (kanta13jp@gmail.com) が 2026-05-23 に「FigmaかCanvaのTemplateで作成し直すことはできますか？」と要望。本書は (1) Canva PPTX import + テンプレート適用フロー、(2) Figma Slides 代替パス、(3) **全 8 枚のコピペ専用カード** を提供し、社長プレゼン当日のクオリティを劇的に高める。

Claude Code は実際に Canva/Figma を直接操作しないため、**人間 (寛太) または Antigravity Browser Agent** が本書に従って差し替えを実行する handoff 形式とする (HANDOFF-14)。

---

## 0. MCP 自動化版あり (推奨、2026-05-23 追加)

**手動作業を完全自動化したい場合は [MCP_CANVA_FIGMA_SETUP_GUIDE_2026-06-02.md](MCP_CANVA_FIGMA_SETUP_GUIDE_2026-06-02.md) を参照** (所要 5-10 分、Canva MCP 経由でテキスト投入 + ブランドカラー指定 + PPTX/PDF export 自動化)。

本書 (CANVA_FIGMA_GUIDE) は MCP セットアップが詰まった場合 / Canva MCP の機能制約に当たった場合のフォールバック手順として有効。8 枚コピペカード自体は MCP 版でも本書の内容を流用する。

---

## 1. 推奨パス: Canva PPTX インポート (最短 30 分 / 最高クオリティ)

### なぜ Canva が最推奨か

- **PPTX 直接インポート対応** — 既存の `mighty_skill_bridge_ceo_presentation_2026-06-02.pptx` をドラッグ＆ドロップするだけでテキストが保持される
- **プレミアムテンプレート豊富** — 「ダークモード / テクノロジー / AI」系で **Mighty Skill-Bridge の Seedance シネマティック UI** と親和性高い
- **「全ページに適用」機能** — テンプレートを一括適用、個別調整不要
- **無料プランで十分** — 無料 Canva アカウントで PPTX import + 基本テンプレートは全て使える

### 手順 (寛太 or Antigravity 実行、所要 30 分)

| Step | アクション | 所要 |
| --- | --- | --- |
| 1 | [exports/knowledge_flow/mighty_skill_bridge_ceo_presentation_2026-06-02.pptx](../exports/knowledge_flow/mighty_skill_bridge_ceo_presentation_2026-06-02.pptx) をローカル PC にダウンロード | 1 分 |
| 2 | Canva (https://www.canva.com/) を開き、`k-umezawa@ml-mightylink.com` (or `kanta13jp@gmail.com`) でログイン | 1 分 |
| 3 | トップ右上の「アップロード」→「メディアをアップロード」で PPTX ファイルをドラッグ＆ドロップ | 2 分 |
| 4 | インポート完了後、自動でプレゼン編集画面に遷移。8 枚のスライド全てがテキスト保持で取り込まれていることを確認 | 1 分 |
| 5 | 左サイドバー「テンプレート」タブで以下キーワード検索: `dark technology AI`、`サイバー`、`ネオン プレゼン`、`tech startup pitch` | 3 分 |
| 6 | 候補から **ダーク背景 + ネオンアクセント + テクノロジカル** なテンプレートを 1 つ選択 → 「全ページに適用 (スタイルのみ)」をクリック | 1 分 |
| 7 | 全 8 枚にテンプレートが適用される。テキストが切れている / 重なっている箇所を手動調整 | 10 分 |
| 8 | 後述の **「Mighty Skill-Bridge ブランドカラー設定」** を Canva の「ブランドキット」 (or 直接カラー指定) で適用 | 5 分 |
| 9 | スライド 2 / 3 / 4 に対して、後述「公開デモ画面スクショ差し込み手順」で実画面を貼り付け | 5 分 |
| 10 | 完成後、右上「共有」→「ダウンロード」で PPTX / PDF 両方をエクスポート、`exports/knowledge_flow/` 配下に `mighty_skill_bridge_ceo_presentation_2026-06-02_canva.pptx` として保存 | 1 分 |

---

## 2. Mighty Skill-Bridge ブランドカラー設定

縦統合型シネマティックダッシュボード UI ([Seedance ブランドループ動画](../scripts/generate_seedance_brand_video.py)) と統一感を持たせる:

| 用途 | カラーコード | 16 進 |
| --- | --- | --- |
| ベース背景 (最も濃い) | サイバーブラック | `#0d0e15` |
| サブ背景 / カード | ディープネイビー | `#161824` |
| プライマリ強調 (タイトル / アイコン) | ネオンブルー | `#00f0ff` |
| セカンダリ強調 (CTA / 数値強調) | ネオングリーン | `#39ff14` |
| 文字 (見出し) | クールホワイト | `#f1f5ff` |
| 文字 (本文) | グレーホワイト | `#c5cae0` |
| 注意 / リスク | ネオンレッド (R 系強調) | `#ff3366` |

**Canva 設定方法**: 左サイドバー「スタイル」→「カラー」→「カスタムカラーを追加」で上記 7 色を登録 → 「全ページに適用」で背景・テキストカラーを一括変更。

**Figma 設定方法**: 「Styles」→「Color」→「+ Create style」で上記 7 色を `mighty/cyber-black` 等の命名で登録。

---

## 3. 公開デモ画面スクショ差し込み手順 (推奨ページ: スライド 2-4)

スライドのリアリティを上げる:

1. ブラウザで `https://kanta13jp1.github.io/mighty-link-ai-connect/` を 1920x1080 で開く
2. スクショ取得 (Windows: `Win+Shift+S` で範囲指定、Mac: `Cmd+Shift+4`)
3. **必須スクショ 3 枚**:
   - 公開 URL トップ画面 (Seedance ブランドループ動画が再生中の状態) → スライド 2
   - Google Sheets `Mighty-Link AI Connect WBS` 開いた状態 (5 タブ見える状態) → スライド 3
   - NotebookLM notebook (`75521ea6-...`) ソース一覧画面 → スライド 4
4. Canva の各スライドに「アップロード」→「画像を挿入」で配置
5. **角丸 16px + 影 (ぼかし 24px / 透明度 30%)** をかけて立体感を出す (Canva の「エフェクト」で設定)

---

## 4. Figma 代替パス (デザイナー的な仕上げを目指す場合)

Canva ではなく Figma を選ぶ理由:

- **より細かいデザイン制御** — Auto Layout / Constraints / Variants
- **既存の Figma デザインシステム流用** — マイティ・リンクが Figma を使っている場合
- **2026 リリースの Figma Slides** — Figma がプレゼン専用機能を出した (https://www.figma.com/slides/)

### 手順

| Step | アクション |
| --- | --- |
| 1 | Figma (https://www.figma.com/) を開き、ログイン |
| 2 | 「+ Create new」→「Figma Slides」 (or プレゼンテンプレート) で新規作成 |
| 3 | 上記「2. Mighty Skill-Bridge ブランドカラー設定」を Styles に登録 |
| 4 | 後述「8 枚コピペカード」の各スライドを Figma フレームに転記 |
| 5 | スライド 2-4 に公開デモスクショを配置 |
| 6 | エクスポート: 「File」→「Export」で全フレームを PNG / PDF / PPTX 形式で書き出し |

**Figma Slides の利点**: 共同編集が即座 (URL 共有のみ、Drive 不要)、プレゼンモードが洗練 (Speaker Notes + Timer)、Component 化が容易。

**Canva との使い分け**: 短時間 (30 分以内) で美麗化したい → Canva。デザイナー的な細部こだわり (2-4 時間) → Figma。

---

## 5. 8 枚コピペ専用カード (Canva / Figma にそのまま貼る)

各カードは:
- **スライドタイトル** (h1 相当)
- **要点 3 つ** (箇条書き)
- **話すメモ** (寛太がスピーカーノートに入れる)
- **見せる証跡 URL / ファイル** (画面に小さく表示 or 寛太が口頭で言う)
- **社長への質問** (CTA、スライド下部に強調表示)

元データ: [exports/knowledge_flow/notebooklm_ceo_slide_outline.md](../exports/knowledge_flow/notebooklm_ceo_slide_outline.md) (2026-05-23 22:23 NotebookLM 生成)

---

### 📇 Slide 1: 本日決めたいこと

**Title**: 本日決めたいこと — 方針・優先順位・次アクション

**Key Points** (3 つ):
- 実際の企画・サービス内容の最終決定ではなく、**今後の方向性と優先順位、次アクション**を決める場
- 現在までのプロトタイプと開発基盤の **「実際にやった状態」** を共有
- 決定事項を打ち合わせ直後に **WBS / Sheets / Calendar へ即時反映** することの合意

**話すメモ**:
> 本日は最終的なサービス内容の発表ではなく、社長に今後の方向性を決めていただくための判断材料と、開発基盤の到達点を見ていただく場として設定しました。本日の決定事項は、そのままシステムへ即時反映できる準備を整えています。

**見せる証跡**:
- 本日のアジェンダ (PRESHARE_MEMO 当日アジェンダ短文の引用)

**社長への質問**:
> 本日のゴールとして「方針決定と次回アクションの明確化」を設定してよろしいでしょうか?

**デザインメモ**: ダーク背景 + 中央に大きく「本日決めたいこと」のタイトル。3 要点は左寄せの箇条書き、社長への質問は下部にネオンブルー強調枠。

---

### 📇 Slide 2: 現在の到達点と公開デモ

**Title**: 現在の到達点と公開デモ — Seedance シネマティック UI 完成

**Key Points**:
- **縦統合型シネマティックダッシュボードへ刷新した UI** で、Seedance API 生成の最上部ブランドループ動画 + 非同期化された下部動画プレビューを実装
- 動画生成の非同期待機・ブラウザ側ポーリング対応、外部 API 課金へのガード機能 (管理ダッシュボード `/admin`) の実装
- AI 制限時のフォールバック + 公開 URL 保護 (Public Demo Guard) + Favicon / Chrome DevTools 対応など開発環境の洗練も完了

**話すメモ**:
> 実際に公開 URL で動くデモをご覧ください。Seedance 風の縦統合型シネマティック UI に刷新し、Seedance API で生成したブランドループ動画を配置しました。経歴書と案件票からフィット診断を行い、非同期での動画生成や意図しない外部 API への課金ガード、AI 制限時のフォールバック設計も備えており、デモ環境の安定性が向上しています。

**見せる証跡**:
- 公開 URL: `https://kanta13jp1.github.io/mighty-link-ai-connect/`
- 外部 API 利用ダッシュボード: `http://127.0.0.1:8000/admin`

**社長への質問**:
> 最初の対象業務 (解決したい課題) として、採用 / 営業 / SES 案件配属のどれが一番良さそうでしょうか?

**デザインメモ**: スライドの右半分に公開 URL スクショ (Seedance ブランドループ動画再生中)。左半分に 3 要点を箇条書き。下部に URL を等幅フォントで小さく。

---

### 📇 Slide 3: Google Workspace 連携による進捗管理基盤

**Title**: Google Workspace 連携 — 5 タブ Sheets + Calendar アクションビュー

**Key Points**:
- WBS / サマリーに加え、**遅延タスクや期限間近の予定を色で可視化するガントチャート風 WBS Timeline**、「課題管理表」「QA 表」を含む **計 5 タブ Sheets 一括自動生成**
- Google Calendar 連携で **完了済みイベントを自動削除**しアクションビューとして運用
- OAuth アカウント検証 (`k-umezawa@ml-mightylink.com`) によるセキュアな API 連携固定

**話すメモ**:
> 開発の進捗や発生した課題・QA は、遅延が一目でわかるガントチャート風のタイムラインを含む Google スプレッドシートの 5 タブに自動同期されます。カレンダーは完了した予定が自動で削除されるため、これからやるべきアクションが明確になります。これにより経営報告と進捗管理が大幅に高速化されます。

**見せる証跡**:
- Google Sheets ID: `1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8`
- Google Calendar: `Mighty Skill-Bridge 開発計画`

**社長への質問**:
> この Google Workspace 連携機能は、社内運用に留めますか? それとも顧客への提供価値の一部としますか?

**デザインメモ**: 5 タブを横並びアイコンで視覚化 (Mighty-Link WBS / WBS Summary / WBS Timeline / 課題管理表 / QA 表)。下部に Calendar の「完了→削除」フローを矢印図で。

---

### 📇 Slide 4: 開発ナレッジ連携の実績とデモ

**Title**: 開発ナレッジ連携 — NotebookLM / Notion / GitHub / Slack / Obsidian

**Key Points**:
- NotebookLM での資料要約・プレゼン作成 (**本説明用の PPTX も自動生成して Drive 共有済み**)
- Notion での連携証跡ページ作成 + GitHub Issues でのタスク管理
- Slack 投稿案、Obsidian ローカル vault 等の連携成果物生成

**話すメモ**:
> 開発中の知識や議事録を NotebookLM や Notion 等に連携する仕組みを実際に作りました。実は、このプレゼンの構成案や PPTX 資料自体も NotebookLM に入力資料を読み込ませて自動で作成しています。**さらに本日の差し替えバージョンは Canva のプレミアムテンプレートで再デザインしています。**

**見せる証跡**:
- 自動生成 PPTX (Drive): `https://docs.google.com/presentation/d/1XGHnQHBpJyyhh_Y3I2lq2UThPRC-2dcL/edit`
- Notion 証跡ページ: `https://www.notion.so/3671d736b9db818aaa33da0a5f1a3951`

**社長への質問**:
> NotebookLM / Slack / Notion / Obsidian のうち、6/2 以降の開発フローに正式導入したい優先順位はありますか?

**デザインメモ**: 4 ツールロゴ (NotebookLM / Notion / Slack / Obsidian) を横並び。各ロゴの下に「採用 / 保留 / 後回し / 不要」のチェックボックスを灰色で配置 (当日に社長が指で挿す想定)。

---

### 📇 Slide 5: サービス方向性の選択肢 (判断マトリクス)

**Title**: サービス方向性 3 択 — A / B / C のどれを育てるか

**Key Points**:
- **方向性 A**: AI フィット診断支援 (想定対象: 営業 / 人材担当 / エンジニア)
- **方向性 B**: Workspace 連携型 PM 支援 (想定対象: 経営 / PM / 現場責任者)
- **方向性 C**: AI PoC 高速構築支援 (想定対象: 新規事業 / 営業企画 / 開発責任者)

**話すメモ**:
> 現在のプロトタイプをどのサービスとして育てるかの選択肢です。デモでお見せしたマッチング推しなら A 案、WBS 同期推しなら B 案、開発の速さや AI 基盤推しなら C 案になります。即決が難しければ「D: 保留」で 5-7 営業日以内に追加面談で確定する選択肢もあります。

**見せる証跡**:
- [判断マトリクス表](CEO_PRESENTATION_DECISION_PACK_2026-06-02.md#判断マトリクス) (DECISION_PACK の表をスクショ or 引用)

**社長への質問**:
> このプロトタイプを何のサービスとして育て、最初に見せるべき相手は **社内 / 既存顧客 / 見込み顧客** のどれにすべきでしょうか?

**デザインメモ**: 3 列カード (A / B / C) を横並び。各カード上部に方向性名、下部に対象ユーザー。「D: 保留」は 4 番目の薄い色のカードで右端に小さく。

---

### 📇 Slide 6: 運用・リスクの論点と公開範囲

**Title**: 運用・リスク — 公開範囲 / 個人情報 / 共有範囲

**Key Points**:
- プロトタイプの公開 URL の許容範囲の確認 (外部公開時は認証層の追加)
- 個人情報 (経歴書等) の取り扱いと法務確認の要否
- Slack や Notion へ流す情報の共有範囲の設定

**話すメモ**:
> 今後の開発と運用を進めるにあたり、情報の公開範囲やセキュリティルールを決めたいと思います。個人情報を取り扱う場合の法務確認の要否や、公開 URL への認証層追加のボーダーラインの確認です。

**見せる証跡**:
- Slack 進捗投稿案: [exports/knowledge_flow/slack_ceo_update.md](../exports/knowledge_flow/slack_ceo_update.md)
- リスク登録: [data/issues_tracker.tsv](../data/issues_tracker.tsv) (R9 個人情報 / R10 公開 URL 認証層)

**社長への質問**:
> 公開 URL は社長共有のみか、社内か、外部共有まで許容しますか? また、個人情報取り扱いの法務確認時期はいつとしますか?

**デザインメモ**: スライド左半分に「公開範囲」3 段階 (社長共有 / 社内 / 外部) の段階図、右半分に「個人情報」のリスク警告アイコン (ネオンレッド `#ff3366` 強調)。

---

### 📇 Slide 7: 6/2 以降の優先開発機能と体制

**Title**: 6/2 以降の優先機能 + 3-tool 開発体制

**Key Points**:
- 最初の 2 週間で実装する **最優先機能** の決定
- **3-tool 体制** (Antigravity / Codex / Claude Code) における API 月額コスト上限
- 寛太の関与度とチーム拡大 (顧客 3 社同時パイロット時などの追加採用シナリオ)

**話すメモ**:
> 決定した方向性に向けて、今後の 2 週間でどこにリソースを集中するかをすり合わせたいと思います。また、AI ツールを 3 つ並走させる現在の開発体制のコスト上限や追加採用の基準についても決めさせてください。

**見せる証跡**:
- WBS 上の「決定後ロードマップ枠」: [CEO_PRESENTATION_POST_DECISION_ROADMAP_2026-06-02.md](CEO_PRESENTATION_POST_DECISION_ROADMAP_2026-06-02.md) (T615)

**社長への質問**:
> 今後の最優先開発機能として、**スコア根拠強化 / 案件ストック管理 / WBS 内製化** などのうち、どれを一番優先しますか? また、開発用 AI の月額コスト上限はいくらに設定しますか? (¥10,000 / ¥30,000 / ¥50,000)

**デザインメモ**: 3 tools (Antigravity / Codex / Claude Code) を横並びアイコンで。各アイコンの下にコスト上限スライダー風のデザイン。下部に「最優先機能」3 候補のラジオボタン UI。

---

### 📇 Slide 8: 次アクションと WBS への即時反映

**Title**: 次アクション — 議事録 → WBS / Calendar / 課題管理表へ即時反映

**Key Points**:
- 本日の **決定事項と保留事項** の整理
- 決定された **Phase 7 の WBS、Google Calendar、課題管理表等への即時反映** の実施
- **次回レビュー日** の設定 (隔週 30 分定例化の確認)

**話すメモ**:
> 本日決まったサービス方針や優先順位は、この議事録テンプレートに入力し、打ち合わせ直後にすぐ Phase 7 の WBS やカレンダー、課題管理表等のシステムへ即時反映させます。Codex レーンが [POST_DECISION_ROADMAP](CEO_PRESENTATION_POST_DECISION_ROADMAP_2026-06-02.md) の対応セクションを `data/WBS.tsv` に flip するだけで Phase 7 が立ち上がります。

**見せる証跡**:
- 議事録テンプレート: [CEO_PRESENTATION_DECISION_PACK_2026-06-02.md 議事録テンプレート](CEO_PRESENTATION_DECISION_PACK_2026-06-02.md#議事録テンプレート)
- Notion 用意思決定 DB インポート CSV: [exports/knowledge_flow/notion_decision_log.csv](../exports/knowledge_flow/notion_decision_log.csv)

**社長への質問**:
> 未決定で保留にしてよい事項はありますか? また、次回のアクションとして **定例レビュー (隔週 30 分)** の機会をいただけますでしょうか?

**デザインメモ**: スライド上部に議事録テンプレのスクショ。中央に矢印で「WBS / Calendar / 課題管理表」へ流れる図。下部にカレンダーアイコンで「次回 6/16 想定」と表示。

---

## 6. 実行チェックリスト (Antigravity / 人間が Canva 操作する際の確認)

- [ ] PPTX ファイルがローカル PC にダウンロード済 (`exports/knowledge_flow/mighty_skill_bridge_ceo_presentation_2026-06-02.pptx`)
- [ ] Canva アカウント (`k-umezawa@ml-mightylink.com` 推奨) でログイン済
- [ ] PPTX を Canva にアップロード → 8 枚スライドがテキスト保持で取り込まれた
- [ ] テンプレート選定: ダークモード + テクノロジー系 + AI 親和性
- [ ] 「Mighty Skill-Bridge ブランドカラー」7 色をブランドキットに登録
- [ ] 公開デモスクショ 3 枚を撮影してスライド 2-4 に配置
- [ ] 各スライドの「社長への質問」がスライド下部に強調表示されていることを確認
- [ ] スピーカーノートに各スライドの「話すメモ」を貼り付け
- [ ] エクスポート: `mighty_skill_bridge_ceo_presentation_2026-06-02_canva.pptx` + `mighty_skill_bridge_ceo_presentation_2026-06-02_canva.pdf` を `exports/knowledge_flow/` に保存
- [ ] Google Drive にアップロード (k-umezawa@ml-mightylink.com 所有) → URL を `exports/knowledge_flow/mighty_skill_bridge_ceo_presentation_2026-06-02.json` の `canva_drive_url` フィールドに追加 (Codex に依頼)
- [ ] [FINAL_REVIEW_CHECKLIST B-1 〜 B-6](CEO_PRESENTATION_FINAL_REVIEW_CHECKLIST.md) に項目 B-7 (Canva 版 PPTX が Drive で開ける) を追加

---

## 7. Canva インポートでうまくいかない場合の Plan B

### B-1: テキストレイアウト崩れ

- 原因: NotebookLM 自動生成 PPTX のテキストボックスサイズが Canva テンプレと合わない
- 対処: 各スライドで「サイズに合わせて文字を縮小」を Canva の「テキスト」→「自動調整」で適用

### B-2: 日本語フォントが崩れる

- 原因: Canva の英語テンプレートが日本語非対応のフォントを使っている
- 対処: 「Noto Sans JP」「源ノ角ゴシック」「Hiragino Sans」のいずれかに一括変更 (Canva の「フォント」→「すべてのテキストに適用」)

### B-3: テンプレート適用で要点が見えなくなる

- 原因: テンプレートのデコレーション要素が前面に来てテキストを覆う
- 対処: テンプレートのデコレーション要素を「右クリック」→「最背面へ移動」、テキストを「最前面へ移動」

### B-4: 全 8 枚通しで時間内に終わらない

- 対処: **スライド 1 + 5 + 8 のみ Canva 化** (本日決めたいこと / 判断マトリクス / 次アクション = 当日のキーセクション)。スライド 2-4 / 6-7 は既存 PPTX のまま使用、Canva 化は 6/16 以降にじっくり

---

## 8. 関連 docs と最新化フロー

- 本書は 6/2 当日まで Canva リデザイン作業の進行記録として使う
- 6/2 終了後、本書の「実行チェックリスト」と「Plan B」は完遂内容に置換、「8 枚コピペカード」は次回プレゼン時のテンプレとしてそのまま残す
- 方向性確定後の Phase 7 プレゼン (例: 6/16) でも本書のコピペカードフォーマットを再利用可能

---

## 9. Codex への handoff キュー

- **HANDOFF-14**: Canva 完成版 PPTX を Drive にアップロード後、`exports/knowledge_flow/mighty_skill_bridge_ceo_presentation_2026-06-02.json` に `canva_drive_url` フィールドを追加
- **HANDOFF-15** (任意): `scripts/generate_ceo_presentation_deck.py` に `--style canva-export` オプションを追加し、Canva にインポートしやすい平 PPTX (デコレーション最小) を出力できるようにする
- **HANDOFF-16** (任意): 公開デモスクショ自動取得スクリプト `scripts/capture_demo_screenshots.py` を新規 (Playwright 経由)、Canva 差し込み用画像 3 枚を `exports/knowledge_flow/screenshots/` に出力

---

## 更新履歴

| 日付 | 変更者 | 内容 |
| --- | --- | --- |
| 2026-05-23 | Claude Code | 初版作成 (T658-extend、Canva PPTX import 手順 + Figma 代替パス + 全 8 枚コピペカード + ブランドカラー定義 + Plan B + Codex handoff) |
