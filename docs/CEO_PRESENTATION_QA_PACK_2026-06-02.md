# 6/2 社長打ち合わせ 想定 QA パック (T607)

作成日: 2026-05-22
オーナー: VSCode + Claude Code レーン
対応 WBS: **T607** 想定QA (5/29-5/30 予定 → 5/22 前倒し完遂)
関連: [CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md) (T605) / [CEO_PRESENTATION_DECISION_PACK_2026-06-02.md](CEO_PRESENTATION_DECISION_PACK_2026-06-02.md) (T611) / [CEO_PRESENTATION_PREP_2026-06-02.md](CEO_PRESENTATION_PREP_2026-06-02.md)

---

## このドキュメントの位置づけ

社長から想定される質問について、**回答方針** + **保留 (即答できない / 6/2 で決めない) 時の対応** + **関連論点番号** ([T605 DISCUSSION_POINTS](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md)) を構造化した QA 集。

進行役 (人間/Codex) は本書の `QA-x` 番号順で当日想定問答を予習し、社長から想定外の質問が出たら **保留 → 議事録テンプレートへ転記 → 6/9 までに回答** のフローで運用する。

[CEO_PRESENTATION_PREP_2026-06-02.md](CEO_PRESENTATION_PREP_2026-06-02.md) の `想定質問と回答方針` セクション (6 行) は導入用の simplified 版。本書がフル版。

---

## 構成

| カテゴリ | QA 番号 | 件数 |
| --- | --- | --- |
| サービス方向性 | QA-01 〜 QA-04 | 4 |
| 技術 / AI | QA-05 〜 QA-08 | 4 |
| 運用 / コスト | QA-09 〜 QA-12 | 4 |
| リスク / セキュリティ | QA-13 〜 QA-16 | 4 |
| 連携ツール採用 | QA-17 〜 QA-19 | 3 |
| ロードマップ / 体制 | QA-20 〜 QA-22 | 3 |

合計 22 QA。

---

## サービス方向性

### QA-01: 「これは結局、何のサービスになるのか?」

**関連論点**: [D-1 サービス方向性](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md#d-1-サービス方向性)

**回答方針**: 「**6/2 で決めるため、現時点では確定していません**」と先に断る。その上で「3 つの方向性 (A: AI フィット診断 / B: Workspace 連携型 PM / C: AI PoC 高速構築) を比較できる状態にしました」と切り返し、[判断マトリクス](CEO_PRESENTATION_DECISION_PACK_2026-06-02.md#判断マトリクス) を即座に開く。

**保留時の対応**: 社長が即決しない場合は D-1 を保留扱いにし、5-7 営業日以内の追加面談で確定する旨を議事録に明記。Codex レーンに `docs/POST_CEO_FOLLOWUP_2026-06-XX.md` 起票を handoff。

---

### QA-02: 「誰がこれを使うのか? お客さんの誰?」

**関連論点**: [D-2 対象ユーザー](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md#d-2-対象ユーザー-フェルソナ)

**回答方針**: A (社内利用者) / B (既存顧客) / C (見込み顧客) / D (A+B 併用) の 4 択を提示。サービス方向性により推奨が変わる旨を補足:
- 方向性 A (AI フィット診断) → 社内営業 + 人材担当が最初
- 方向性 B (PM 支援) → 経営陣 / PM 層
- 方向性 C (PoC 構築) → 既存顧客 / 見込み顧客の開発責任者

**保留時の対応**: D-1 と一括で保留可。ただし「最低限、社内パイロットは始められる」と提示し、社内利用は即着手可能とする。

---

### QA-03: 「他社の同じようなサービスとどう違うのか?」

**関連論点**: D-1 (補足質問)

**回答方針**: マイティ・リンクのコアビジョン「人 × ビジネス × テクノロジーを力強く繋ぐ」を体現する点 (README.md, ANTIGRAVITY_GUIDE.md:5) を軸に、以下の差別化軸を提示:
1. **マルチモーダル評価** — Gemini Omni で経歴書 PDF + ポートフォリオ画像 + 動画を一体評価 ([requirements.md:12, 28-37](requirements.md))
2. **4 軸スコアリング** — Skill / Culture / Growth / Performing で単純キーワードマッチを超える
3. **Workspace ネイティブ統合** — Sheets / Calendar / Drive と本日確認できるレベルの実連携

**保留時の対応**: 競合分析の網羅性が不足している場合は「方向性確定後 1 週間で競合 5 社の比較表を作る」と返し、Claude Code レーンに competitor research タスクを起票。

---

### QA-04: 「いつまでに最初のお客様に提供できる?」

**関連論点**: [D-3 最優先機能](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md#d-3-最優先機能-62--616-の-2-週間で作るもの)

**回答方針**: 「**社内パイロットなら 6/16 (2 週間後) から開始可能**」と明示。3 つの段階を提示:
- 6/16: 社内パイロット
- 7/14: 既存顧客 3 社へのクローズドベータ
- 9/1: 限定的な公開 (方向性により変動)

**保留時の対応**: 顧客向け公開時期はマイティ・リンクの営業計画次第なので保留可。社内パイロットだけは無条件で 6/16 開始を約束。

---

## 技術 / AI

### QA-05: 「Gemini が止まったら、サービスも止まるのか?」

**関連論点**: [D-4 AI エンジン選定方針](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md#d-4-ai-エンジン選定方針-2026-05-22-新規論点)

**回答方針**: 「**止まりません**」と即答。deterministic fallback パイプラインを実装済 ([BACKEND_AI_PIPELINE.md](BACKEND_AI_PIPELINE.md), [CODEX_CONTINUATION_NOTES.md:69-111](CODEX_CONTINUATION_NOTES.md)) で、Gemini quota 切れ中でも `AI_FORCE_MOCK=1` で 4 軸スコアが算出される。**当日デモが Gemini quota 切れ状態 (5/27 18:48 復帰待ち) なので、deterministic fallback 動作を実際に見せられる** ことを強調。

**保留時の対応**: 完全マルチクラウド AI 化 (Claude / GPT 同時待機) を求められた場合は QA-06 で再回答。

---

### QA-06: 「Gemini 以外の AI も使えるのか? Claude や ChatGPT は?」

**関連論点**: [D-4 AI エンジン選定方針](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md#d-4-ai-エンジン選定方針-2026-05-22-新規論点)

**回答方針**: 「**開発体制では既に 3-tool 並走中**」と説明 ([MULTI_AI_WORKFLOW.md](MULTI_AI_WORKFLOW.md)):
- Antigravity + Gemini (主開発)
- VSCode + Codex / GPT-5.5 (実装 PR / sync スクリプト)
- VSCode + Claude Code (architect / docs / 調停)

サービス本体で使う AI と開発で使う AI は別問題と区別。**サービス本体は現時点で Gemini 単一**だが、A/B/C の選択肢を D-4 で提示。

**保留時の対応**: D-4 保留可。3 ヶ月以内に各エンジンの cost / latency / 精度を計測した上で再判断するという落とし所を提示。

---

### QA-07: 「AI の判定根拠は説明できるのか? ブラックボックスではないか?」

**関連論点**: [D-3 最優先機能](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md#d-3-最優先機能-62--616-の-2-週間で作るもの) (選択肢 A: AI スコア根拠の説明強化)

**回答方針**: 「**現状でも structured payload で根拠を返している**」と即答。`/api/match` レスポンスに `matched_skills`, `missing_skills`, 4 軸スコア根拠が含まれる ([CODEX_CONTINUATION_NOTES.md:74-78](CODEX_CONTINUATION_NOTES.md))。さらに `/api/audit/recent` で AI 判定 JSONL ログが取得可能 ([T305 完了](data/WBS.tsv))。「6/16 までに UI 上で根拠を見せる機能 (D-3 選択肢 A) を最優先で実装可能」と提案。

**保留時の対応**: なし。即答カテゴリ。

---

### QA-08: 「Gemini 3.5 Pro はまだ来ないのか? Pro の方が精度高いだろう」

**関連論点**: [D-4](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md#d-4-ai-エンジン選定方針-2026-05-22-新規論点), [Risks & Blockers R1](CEO_PRESENTATION_PREP_2026-06-02.md#risks--blockers-2026-05-22-時点)

**回答方針**: **重要な訂正**: 「**Gemini 3.5 Flash が Gemini 3.1 Pro を 4 倍速で上回ることが I/O 2026 で公表されました**」と先制。Pro 公開を待つ必要は薄く、Flash で出荷可能。**R1 リスクは HIGH から MED に降格済** ([MULTI_AI_WORKFLOW.md Best Practices Refresh](MULTI_AI_WORKFLOW.md#best-practices-refresh-2026-05-22))。

**保留時の対応**: Pro が将来公開された際の switch コスト見積を「方向性確定後に提示する」と返答。

---

## 運用 / コスト

### QA-09: 「月いくらかかる? 運用コストは?」

**関連論点**: [O-2 課金モデル仮説](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md#o-2-課金モデル仮説)

**回答方針**: **現状 = ほぼゼロ** (Google AI Pro / Ultra アカウントの baseline quota 内、Workspace は既存契約)。本格運用時の見積は方向性により以下のレンジ:
- 方向性 A (AI 診断): 月 ¥10,000-¥50,000 (Gemini API + Drive 容量)
- 方向性 B (PM 支援): 月 ¥5,000-¥30,000 (Workspace 中心、AI 使用控えめ)
- 方向性 C (PoC 構築): 月 ¥30,000-¥150,000 (案件数に比例)

**保留時の対応**: 詳細見積は方向性確定後 1 週間で出すと約束。

---

### QA-10: 「課金モデルは? 売上はどう立てるのか?」

**関連論点**: [O-2 課金モデル仮説](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md#o-2-課金モデル仮説)

**回答方針**: PREP.md:77 で「6/2 まで決め打ちしない」と既に確定済の領域。ただし 4 つの仮説 (月額 SaaS / 案件あたり従量 / 顧問契約 / 一括導入) を提示し、方向性別の親和性を 1 表で説明。

**保留時の対応**: O 系 (Optional) 論点。当日深掘りせず議事録に「課金モデルは別途検討」と記載。

---

### QA-11: 「どこまでマイティ・リンク社内で運用するのか? 誰が WBS を更新するのか?」

**関連論点**: 関連 D-2 / O-4 / [運用論点 T606](CEO_PRESENTATION_PREP_2026-06-02.md)

**回答方針**: 「**現状の WBS 更新者は寛太 + Codex レーン**」と明示。3-tool 体制下で:
- WBS.tsv 書き込み = Codex のみ ([MULTI_AI_WORKFLOW.md 競合解決ルール](MULTI_AI_WORKFLOW.md))
- Sheets 同期 = `python scripts/sync_wbs_to_sheets.py` (自動化済)
- 進捗確認 = 社長は Sheets / Calendar を見るだけで良い

**保留時の対応**: 社内追加採用 (O-4) があれば運用役割を再分担する旨を補足。

---

### QA-12: 「6/2 以降の開発体制は? 寛太さん 1 人で続けるのか?」

**関連論点**: [O-4 チーム拡大シナリオ](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md#o-4-チーム拡大シナリオ)

**回答方針**: 「**現状は寛太 + 3 AI ツール (Antigravity+Gemini / Codex / Claude Code) で並走**」と明示。3 AI 並走で人 1 名相当 × 3 の効率が出ている根拠を示す ([MULTI_AI_WORKFLOW.md day-by-day オーナーシップ表](MULTI_AI_WORKFLOW.md#day-by-day-オーナーシップ))。追加採用が必要になる閾値 (例: 顧客 3 社同時パイロット時) を提示。

**保留時の対応**: O-4 は Optional。当日触れず議事録だけ残す。

---

## リスク / セキュリティ

### QA-13: 「個人情報や経歴書を扱うが、漏洩リスクはないのか?」

**関連論点**: [T622 権限・情報管理](CEO_PRESENTATION_PREP_2026-06-02.md), 関連 [D-5 公開範囲](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md#d-5-公開範囲)

**回答方針**: 4 重防御を即座に提示:
1. **公開 URL は限定共有** (社長共有 URL のみ、外部公開禁止)
2. **OAuth は Workspace アカウント `k-umezawa@ml-mightylink.com` 固定** ([T647 完了](data/WBS.tsv), `python scripts/verify_google_workspace_account.py` で検証)
3. **認証情報マスキング有効** (ANTIGRAVITY_GUIDE.md:61-62 Credential Masking)
4. **AI 判定 JSONL ログはローカル保存** ([T305](data/WBS.tsv))、外部送信なし

**保留時の対応**: 「正式運用前に法務 / コンプラ確認が必要」と社長判断を引き出し、Notion 議事録 DB に該当タスクを起票。

---

### QA-14: 「公開 URL が落ちたらデモはどうするのか?」

**関連論点**: [F-1 / F-2 バックアップ](CEO_PRESENTATION_FINAL_REVIEW_CHECKLIST.md), [T613 デモバックアップ](data/WBS.tsv)

**回答方針**: 「**5 重のバックアップ導線を準備済**」と即答 ([DECISION_PACK デモ障害時の代替導線](CEO_PRESENTATION_DECISION_PACK_2026-06-02.md#デモ障害時の代替導線)):
1. ローカル `python src/app.py` で起動
2. `data/WBS.tsv` を直接見せる
3. `exports/mighty_development_plan.ics` で Calendar 内容説明
4. `exports/knowledge_flow/backup/` のスクショ集
5. デモ動画 (Antigravity 復帰後 5/27 以降に Omni で生成予定)

**保留時の対応**: なし。即答カテゴリ。

---

### QA-15: 「Slack / Notion で社長宛のメンションが流れるが、誰が読む権限を持つのか?」

**関連論点**: [T622 権限・情報管理](data/WBS.tsv)

**回答方針**: 「**Slack 連携は 6/2 時点で未開通**」と先制 ([R3](CEO_PRESENTATION_PREP_2026-06-02.md#risks--blockers-2026-05-22-時点))。Slack CLI/MCP 未露出 → live send はしない。Notion は MCP 経由で証跡ページのみ作成、社長個人宛の通知は飛ばさない。「正式採用前に通知範囲・閲覧権限を社長確認」のフローを D-6 で確定する。

**保留時の対応**: D-6 保留可。「採用判断後 1 週間以内に権限マトリクスを作る」と返答。

---

### QA-16: 「GitHub Project ボードを見たい」

**関連論点**: [R2](CEO_PRESENTATION_PREP_2026-06-02.md#risks--blockers-2026-05-22-時点), Issues #5/#8

**回答方針**: 「**読み取り権限の OAuth scope 復旧待ち**」と説明 ([INTEGRATION_DEMO_EVIDENCE_2026-06-02.md:68-77](INTEGRATION_DEMO_EVIDENCE_2026-06-02.md)). ブラウザでの `gh auth refresh -s project` 承認が必要 (人間ブロック)。代替として GitHub Issues #1-#11 一覧を見せる。

**保留時の対応**: R2 mitigation 発動。デモから Project ボードを **明確に除外**する旨を社長へ通知 (R2 が 5/27 までに未解決の場合)。

---

## 連携ツール採用

### QA-17: 「NotebookLM は本当に役に立つのか?」

**関連論点**: [D-6 連携ツール採用判断](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md#d-6-連携ツール採用判断-notebooklm--slack--notion--obsidian)

**回答方針**: 「**今この場で実演できます**」と提示。notebook `75521ea6-...` に 14 docs 投入済、Agent Brief と CEO Slide Outline 取得済 ([CEO_PRESENTATION_PREP_2026-06-02.md:174-184](CEO_PRESENTATION_PREP_2026-06-02.md))。具体的価値: 「次回打ち合わせ前に **NotebookLM に質問するだけで論点が出る** 状態を作れる」。

**保留時の対応**: D-6 NotebookLM を「**採用**」に振る前提で社長合意を取りたい。「保留」「後回し」になった場合は CLI 認証維持コスト (月 0 円) のみ継続。

---

### QA-18: 「Slack や Notion を全社で導入したらどうか?」

**関連論点**: [D-6](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md#d-6-連携ツール採用判断-notebooklm--slack--notion--obsidian)

**回答方針**: 「**現状は本プロジェクトの連携実験スコープ内**」と慎重に範囲を切る。全社導入は (a) 既存利用ツールとの重複、(b) 月額コスト、(c) セキュリティ審査が必要なため、本プロジェクトの判断とは分離する。社長から「全社採用したい」と言われた場合は「別議題として 6/16 までに専用検討会を設定」を提案。

**保留時の対応**: 全社採用は **本プロジェクト判断外** として議事録分離。

---

### QA-19: 「Obsidian って何? 開発者向けノートアプリ?」

**関連論点**: [D-6](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md#d-6-連携ツール採用判断-notebooklm--slack--notion--obsidian)

**回答方針**: 「**マークダウンベースのローカルナレッジツール**」と説明。本プロジェクトでは ADR / プロンプト資産 / 個人メモを溜める用途 ([DEVELOPMENT_KNOWLEDGE_FLOW.md](DEVELOPMENT_KNOWLEDGE_FLOW.md))。公式記録は `docs/` (Git 管理) に上げる運用なので、社長は Obsidian 自体を意識する必要はない。

**保留時の対応**: D-6 Obsidian を「**個人メモ運用に限定**」で合意取得が最も省力 (社長判断不要)。

---

## ロードマップ / 体制

### QA-20: 「6/2 で決まったら、次は何を作るのか?」

**関連論点**: [T615 決定後ロードマップ枠](data/WBS.tsv), [O-1 WBS UI 内製化](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md#o-1-wbs-ui-内製化)

**回答方針**: 「**方向性別に 3 つのロードマップ枠を準備済**」(T615 は次セッション完遂予定)。
- 方向性 A → AI スコア根拠 UI + 案件ストック管理
- 方向性 B → WBS UI 内製化 + Sheets 進捗自動取り込み
- 方向性 C → 顧客名差し替えテンプレート機能

決定 1 週間以内に WBS Phase 7 を起票し、Sheets/Calendar へ即反映する。

**保留時の対応**: D-1 が保留なら本 QA も自動的に保留。後追い面談で確定。

---

### QA-21: 「次回はいつ会えるか?」

**関連論点**: 当日アジェンダ ([T614 事前送付メモ](data/WBS.tsv))

**回答方針**: 6/16 (T615 ロードマップ整理直後の 2 週間後) を第一候補として提示。社長の予定により 6/9 or 6/23 を予備候補。

**保留時の対応**: なし。即答カテゴリ。

---

### QA-22: 「寛太は今、何時間くらいこれに使っているのか? 持続可能か?」

**関連論点**: [O-4 チーム拡大](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md#o-4-チーム拡大シナリオ)

**回答方針**: 「**3-tool 体制で平均 1 日 2-3 時間程度**」を提示 (実数は寛太側で当日確認)。Antigravity + Codex + Claude Code が並走するため、寛太は orchestrator 役で工数を抑えられている。「顧客 3 社同時パイロット時に追加採用検討」(QA-12 と同じ閾値)。

**保留時の対応**: 持続可能性に懸念があれば「O-4 採用論点を 6/16 で議題化」と返答。

---

## 当日の保留フロー (即答できない質問のハンドリング)

社長から想定外の質問が出た場合の標準フロー:

1. **即座に保留宣言**: 「即答できないので、議事録に残して 6/9 までに回答します」と明言。
2. **議事録テンプレートに転記** ([CEO_PRESENTATION_DECISION_PACK_2026-06-02.md 議事録テンプレート](CEO_PRESENTATION_DECISION_PACK_2026-06-02.md#議事録テンプレート) の `2. 保留事項` セクション)。
3. **当日中に Claude Code レーンへ起票**: `docs/CEO_FOLLOWUP_2026-06-02.md` (新規ファイル) に保留質問リストを記載。
4. **6/9 までに回答**: Codex レーンが事実関係を調査、Claude Code が回答を docs 化、寛太から社長へ送付。

**禁止事項**:
- 即興で見立てを答えて後で訂正する (信頼コスト大)
- 「持ち帰り検討します」とだけ言って期日を切らない (フォローアップ抜け)

---

## 当日の機材 / 画面操作チェックリスト

進行役 (人間 + Codex) が QA に即応するため、以下の画面を事前に開いておく:

- [ ] 公開デモ URL (`https://kanta13jp1.github.io/mighty-link-ai-connect/`)
- [ ] ローカル FastAPI (`http://localhost:8000`) — `AI_FORCE_MOCK=1` で起動
- [ ] Google Sheets `Mighty-Link WBS`
- [ ] Google Calendar `Mighty Skill-Bridge 開発計画`
- [ ] PowerPoint (`mighty_skill_bridge_ceo_presentation_2026-06-02.pptx`) と Drive 共有 URL
- [ ] NotebookLM notebook `75521ea6-6b9b-47b2-9508-50050d8ab2d5`
- [ ] GitHub Issues 一覧
- [ ] [DECISION_PACK 判断マトリクス](CEO_PRESENTATION_DECISION_PACK_2026-06-02.md#判断マトリクス) (D-1 即対応)
- [ ] [DISCUSSION_POINTS](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md) (進行表)
- [ ] **本書** (想定 QA 即参照)

---

## 更新履歴

| 日付 | 変更者 | 内容 |
| --- | --- | --- |
| 2026-05-22 | Claude Code | 初版作成 (T607 完遂、22 QA + 保留フロー + 機材チェックリスト) |
