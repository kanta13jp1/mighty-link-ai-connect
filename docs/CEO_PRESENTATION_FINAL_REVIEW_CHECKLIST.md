# 6/2 社長プレゼン 最終レビュー チェックリスト (T663)

作成日: 2026-05-22  
オーナー: VSCode + Claude Code レーン (本ファイルの維持) / 各項目のオーナーは表内に明記  
ターゲット: 2026-06-02 (火) CEO 打ち合わせ

---

## 使い方

- 各行に `Status` 列を設け、`pending` / `in_progress` / `pass` / `fail` / `n/a` のいずれかで記入する。
- 5/30 EOD までに `pass` または `n/a` のいずれかになっていることを目標とする (Hard gate 項目は 6/1 EOD)。
- `fail` の項目は **必ず別途 Issue 化** し、`risk:ceo-blocker` ラベルを付ける。
- Final review は **6/1 21:00 JST** に Claude Code レーンが全項目を読み合わせて sign-off。

---

## A. デモ環境 (5/30 EOD まで pass)

| # | チェック | 確認方法 | オーナー | 期限 | Status | 備考 |
|---|---|---|---|---|---|---|
| A-1 | 公開デモ URL `https://kanta13jp1.github.io/mighty-link-ai-connect/` が Skill-Bridge UI を返す (README fallback ではない) | `python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/` exit code 0 | Codex | 5/30 | pending | |
| A-2 | ローカル FastAPI (`python src/app.py`) が `http://127.0.0.1:8000/api/health` で `{ "status": "healthy" }` を返す | `Invoke-WebRequest http://127.0.0.1:8000/api/health` | Codex | 5/30 | pending | |
| A-3 | `AI_FORCE_MOCK=1` で起動した場合の `/api/health` が `ai_force_mock: true` を返す | 上記環境変数付き起動後の確認 | Codex | 5/30 | pending | リハーサル外では mock 維持 |
| A-4 | サンプル経歴書 + 案件票で `/api/match` が 4 軸スコアを返す | curl or UI 操作 | Codex | 5/30 | pending | |
| A-5 | UI の radar chart が 4 軸を正しく描画 (T202) | ブラウザ目視 | Antigravity | 6/1 | pending | quota refresh 後 |

## B. PowerPoint / NotebookLM 成果物 (5/25 EOD まで pass)

| # | チェック | 確認方法 | オーナー | 期限 | Status | 備考 |
|---|---|---|---|---|---|---|
| B-1 | `exports/knowledge_flow/mighty_skill_bridge_ceo_presentation_2026-06-02.pptx` がローカルで開ける | PowerPoint 起動 | Claude review | 5/25 | pending | T658 完了済 |
| B-2 | PPTX が Drive にアップロード済、`k-umezawa@ml-mightylink.com` 所有 | Drive share URL を `exports/knowledge_flow/*.json` (manifest) から確認 | Codex | 5/25 | pending | T657 in-flight |
| B-3 | PPTX のスライド数が 8 枚、表紙〜判断マトリクスまで揃う | PowerPoint 内目視 | Claude review | 5/25 | pending | |
| B-4 | NotebookLM notebook `75521ea6-6b9b-47b2-9508-50050d8ab2d5` が 22 sources Ready | NotebookLM UI スクショ取得 | 人間 | 5/25 | pending | スクショは `exports/knowledge_flow/backup/` |
| B-5 | NotebookLM Agent Brief が最新 docs を反映 | `exports/knowledge_flow/notebooklm_agent_brief.md` mtime と `docs/*.md` mtime 比較 | Codex | 5/26 | pending | T651 |
| B-6 | NotebookLM CEO Slide Outline が PPTX 内容と一致 | `notebooklm_ceo_slide_outline.md` ↔ PPTX 目視 | Claude review | 5/25 | pending | |

## C. WBS / カレンダー / Issues (5/30 EOD まで pass)

| # | チェック | 確認方法 | オーナー | 期限 | Status | 備考 |
|---|---|---|---|---|---|---|
| C-1 | Google Sheets `Mighty-Link WBS` が `data/WBS.tsv` と行一致 | `python scripts/sync_wbs_to_sheets.py --dry-run` で diff=0 | Codex | 5/30 | pending | |
| C-2 | Google Sheets `WBS Summary` の集計値が最新 | Sheets 目視 (Phase 別完了率) | Codex | 5/30 | pending | |
| C-3 | Google Sheets `WBS Timeline` が 6/2 までの帯を表示 | Sheets 目視 | Codex | 5/30 | pending | |
| C-4 | Google Calendar `Mighty Skill-Bridge 開発計画` が未完了・実行中・会議イベントだけを表示 | `python scripts/sync_wbs_to_calendar.py` 出力で `Deleted completed` と `Failed: 0` を確認 | Codex | 5/30 | pending | 完了済みWBSイベントはCalendarから削除し、履歴はSheets/Gitで確認 |
| C-5 | `exports/mighty_development_plan.ics` が最新 commit | git log で確認 | Codex | 5/30 | pending | |
| C-6 | GitHub Issues #1-#11/#13/#14/#16 すべてに最新コメント (進捗 or 完了マーク) | `gh issue list --state all --limit 20` レビュー | Claude | 5/30 | pending | |
| C-7 | GitHub Issues #5/#8 の `read:project` scope 問題が解決 or 6/2 デモから除外明記 | Issue ステータス確認 | 人間 + Claude | 5/27 | pending | 未解決なら **R2 mitigation 発動** |

## D. CLI / MCP 連携証跡 (5/25 EOD まで pass)

| # | チェック | 確認方法 | オーナー | 期限 | Status | 備考 |
|---|---|---|---|---|---|---|
| D-1 | `docs/INTEGRATION_DEMO_EVIDENCE_2026-06-02.md` が最新コミット | git log | Claude | 5/25 | pending | |
| D-2 | Notion 証跡ページが accessible (`3671d736b9db81d3ac3cc7a716699c37` 等) | ブラウザで開く | 人間 | 5/25 | pending | T660 |
| D-3 | Obsidian vault `exports/knowledge_flow/obsidian_vault/` が `.obsidian` 設定込みで揃う | ファイル一覧確認 | Codex | 5/25 | pending | |
| D-4 | Slack post 草稿 `exports/knowledge_flow/slack_ceo_update.md` が最新の連携状況を反映 | git log + 内容目視 | Claude review | 5/25 | pending | live send は **しない** |
| D-5 | Workspace OAuth が `k-umezawa@ml-mightylink.com` で生きている | `python scripts/verify_google_workspace_account.py` exit 0 | Codex | 5/25 | pending | |

## E. 判断材料 / プレゼン本体 (5/29 EOD まで pass)

| # | チェック | 確認方法 | オーナー | 期限 | Status | 備考 |
|---|---|---|---|---|---|---|
| E-1 | `docs/CEO_PRESENTATION_DECISION_PACK_2026-06-02.md` の判断マトリクスが 3 選択肢以上揃う | 目視 | Claude | 5/28 | pending | T611 |
| E-2 | 1 枚絵サマリー (T610) が `exports/knowledge_flow/` または PPTX 内に存在 | ファイル確認 | Antigravity | 5/28 | pending | quota refresh 後 |
| E-3 | 想定 QA 一覧 (T607) が 10 件以上 | 該当 docs 目視 | Claude | 5/29 | pending | |
| E-4 | サービス方向性の選択肢 3 案 (AI 適性診断 / PM-WBS / PoC scaffold) が明記 | DECISION_PACK 目視 | Claude | 5/28 | pending | R1 影響あり |
| E-5 | 当日アジェンダ短文 (T614) が `docs/CEO_PRESENTATION_PREP_2026-06-02.md` 内に存在 | grep "アジェンダ" | Claude | 5/29 | pending | |

## F. バックアップ・障害時導線 (6/1 EOD まで pass = Hard gate)

| # | チェック | 確認方法 | オーナー | 期限 | Status | 備考 |
|---|---|---|---|---|---|---|
| F-1 | 公開 URL 障害時のローカル実行手順が `docs/CEO_PRESENTATION_PREP_2026-06-02.md` に明記 | grep "デモ導線" | Claude | 5/29 | pending | T613 |
| F-2 | デモ各ステップの backup スクショが `exports/knowledge_flow/backup/` に存在 | ls 確認 | Antigravity | 6/1 | pending | quota refresh 後 |
| F-3 | デモ動画 (≤ 3 分) が再生可能 | ローカル再生 | Antigravity | 6/1 | pending | Gemini API現行マルチモーダルモデル、quota refresh 後 |
| F-4 | `.ics` ファイル説明用スクショ | ファイル確認 | Antigravity | 6/1 | pending | |
| F-5 | Slack 連携できない場合の代替説明 (草稿表示) リハーサル済 | dry-run 中に確認 | Claude | 6/1 | pending | R3 mitigation |

## G. 当日運用 (6/2 当日)

| # | チェック | 確認方法 | オーナー | 期限 | Status | 備考 |
|---|---|---|---|---|---|---|
| G-1 | 議事録テンプレートが `docs/CEO_PRESENTATION_DECISION_PACK_2026-06-02.md` に含まれる | 目視 | Claude | 5/30 | pending | T609 |
| G-2 | 決定後の WBS 差し替えフロー (T612) が明記 | 目視 | Claude | 5/30 | pending | |
| G-3 | 決定後ロードマップ枠 (T615) が用意 | 目視 | Claude | 5/30 | pending | |
| G-4 | 当日の役割分担 (司会/操作/議事録/QA) を確定 | docs 内 or 口頭 | 人間 + Claude | 6/1 | pending | |

---

## Final Review (6/1 21:00 JST)

- [ ] A-1 〜 A-5: すべて `pass` (Hard gate)
- [ ] B-1 〜 B-6: すべて `pass`
- [ ] C-1 〜 C-7: すべて `pass` (C-7 が `n/a` の場合はデモから Project ボードを除外する旨を明記)
- [ ] D-1 〜 D-5: すべて `pass`
- [ ] E-1 〜 E-5: すべて `pass`
- [ ] F-1 〜 F-5: すべて `pass` (Hard gate)
- [ ] G-1 〜 G-4: すべて `pass`
- [ ] `git tag ceo-demo-2026-06-02` を打ち、main を凍結 (Codex 担当)
- [ ] dry-run を計測 (目標 ≤ 25 分)

**Go/No-Go 判定**: Hard gate (A 系 + F 系) が全 pass、かつ A-1 + F-3 + B-1 + B-2 が pass であれば Go。それ以外は Claude Code が 6/1 22:00 JST までに human escalation。

---

## 参照

- [MULTI_AI_WORKFLOW.md](MULTI_AI_WORKFLOW.md) — 3-tool 体制・handoff 規約・day-by-day オーナーシップ
- [CEO_PRESENTATION_PREP_2026-06-02.md](CEO_PRESENTATION_PREP_2026-06-02.md) — プレゼン構成・デモ導線
- [CEO_PRESENTATION_DECISION_PACK_2026-06-02.md](CEO_PRESENTATION_DECISION_PACK_2026-06-02.md) — 判断マトリクス
- [INTEGRATION_DEMO_EVIDENCE_2026-06-02.md](INTEGRATION_DEMO_EVIDENCE_2026-06-02.md) — CLI/MCP 連携証跡
- [WBS.md](WBS.md) — T601-T666 全体像

---

## 更新履歴

| 日付 | 変更者 | 内容 |
|---|---|---|
| 2026-05-22 | Claude Code | 初版作成 (T663 deliverable、35 項目 7 セクション) |
