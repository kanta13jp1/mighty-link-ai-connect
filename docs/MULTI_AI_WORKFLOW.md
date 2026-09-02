# Multi-AI 開発ワークフロー

更新日: 2026-07-13
担当レーン: Codex  
関連: [WBS.md](WBS.md) / [WBS_SYNC_GUIDE.md](WBS_SYNC_GUIDE.md) / [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) / [CODEX_CONTINUATION_NOTES.md](CODEX_CONTINUATION_NOTES.md)

---

## 目的

Mighty-Link AI Connect は、Antigravity + Gemini、Codex、Claude Code の三つを役割分担して使う。各セッションで同じ品質ゲートを通し、WBS、課題管理表、QA表、Google Sheets、Google Calendar、GitHub Issues、GitHub Project の状態がずれないようにする。

この文書は毎回の開発開始から closeout までの標準手順を定義する。古いモデル名、未確認の未来機能、解決済みの暫定ブロッカー、古い同期件数は現行ガイドとして残さない。

---

## レーン分担

| レーン | 主担当 | 使う場面 |
| --- | --- | --- |
| Antigravity + Gemini | UI、マルチモーダル、ブラウザ確認 | フロントエンド polish、画像・動画・音声を含むデモ、視覚確認、Gemini API の現行モデルを使う検証 |
| Codex | 実装、同期、自動化、GitHub | FastAPI、Firebase/Supabase、Google Workspace API、CI、GitHub CLI、WBS/Sheets/Calendar同期、public demo guard |
| Claude Code | ドキュメント、レビュー、triage | 仕様・議事録・Runbook、WBS網羅性監査、PRレビュー、課題/QAの整理、古いdocsの削除判断 |

競合しそうなときは、WBSの該当タスクと `data/WBS.tsv` を正本にする。ドキュメントだけで状況を確定せず、最後に同期スクリプトと GitHub の状態で確認する。

---

## セッション開始ゲート

1. `docs/` の関連文書を読む。今回の作業に直接関係する要件、設計、Runbook、WBSを優先する。
2. 公式ドキュメントの最新版を確認する。広い一覧を毎回確認しつつ、今回の作業に影響するものは必ず根拠として使う。
3. 今日完了するWBSタスクを一つ決める。不足タスクが見つかった場合は `data/WBS.tsv` に追加し、同じセッションで完了できる範囲なら完了まで進める。
4. 課題やQAが発生したら、`data/issues_tracker.tsv` と `data/qa_tracker.tsv` に反映する。
5. secret、OAuth token、実メール本文、個人連絡先、FTP/DB/Stripeの認証情報は GitHub、Sheets、Issue、Slack、Notion、NotebookLM、docs に記録しない。

---

## 公式Docs確認対象

毎セッションで以下を確認する。作業対象に該当しないものは「影響なし」として扱い、docsに長い引用や古いモデル名を残さない。

| 領域 | 公式確認先 |
| --- | --- |
| Anthropic / Claude Code | Claude Code overview、memory、settings、security |
| OpenAI / Codex | Codex overview、AGENTS.md、best practices、MCP、Codex manual |
| Google / Gemini / Workspace | Gemini models、context caching、Sheets batchUpdate、Firebase docs |
| Microsoft | Microsoft Foundry、Azure OpenAI / Foundry Models |
| Meta / Llama | Llama docs、Meta公開ページ、公式Llama GitHub |
| Amazon | Amazon Bedrock user guide |
| Apple | Machine Learning、Human Interface Guidelines |
| xAI / Grok | xAI docs |
| Kimi / Moonshot | Kimi API docs |
| MiMo | XiaomiMiMo/MiMo 公式GitHub |
| DeepSeek | DeepSeek API docs |
| ByteDance / BytePlus | Seedance、BytePlus ModelArk docs |
| GitHub | Issues、Projects、Actions、Pages、secrets |
| Slack | Slack Developer Docs |
| Notion | Notion API docs |
| Obsidian | Obsidian Help |
| Unity | Unity docs / Unity Manual |
| Figma | Figma REST / Plugin docs |
| Canva | Canva Apps SDK docs |
| Reddit | Reddit Devvit docs |
| InsForge | InsForge docs、`https://insforge.dev/skill.md` |
| Firecrawl | Firecrawl docs |
| Discord | Discord Developer docs |
| Stripe | Billing、Customer Portal、Tax、API reference |
| Supabase | Supabase docs、changelog、RLS、Postgres upgrade notes |
| お名前.com | お名前.comヘルプ、ドメイン/DNS/WordPress/FTP関連 |

2026-07-18 セッション確認メモ（T897 / T879）:

- Google Calendar API events リファレンスを確認した（T879）。終日イベントは `start.date`/`end.date` で終了日が排他的という仕様は `sync_wbs_to_calendar.py` の現行実装（終了日+1日）と一致。`eventLabelVersion`/会議データの `createRequest` 推奨は現行の全日イベント同期には影響なし。採用変更なし。

- Anthropic Claude Codeのmemory docsを確認した。`CLAUDE.md` から `@AGENTS.md` をインポートする現行構成は引き続き公式推奨どおり。auto memoryのMEMORY.md読込上限（200行/25KB）に留意。採用変更なし。
- OpenAI Codex docsの所在変更を検出した: `developers.openai.com/codex/guides/agents-md` は `learn.chatgpt.com/docs/agent-configuration/agents-md` へ308恒久リダイレクトされる。AGENTS.mdはグローバル→プロジェクトの階層マージ（近接優先）と `AGENTS.override.md` に対応。旧URLはリダイレクトで到達可能なため一覧は変更せず、次回以降は新URLを直接参照してよい。
- Google Sheets `batchUpdate` を確認した。バッチのアトミック性（1件失敗で全体不適用）とfield maskの選択的更新の推奨は `scripts/sync_wbs_to_sheets.py` の現行方針と整合。採用変更なし。
- GitHub Issues/Projects、Sheetsの正本同期、Calendarの完了イベント削除の運用は2026-07-13（T893）の判断を維持する。
- WBSは `WBS_REVIEW_2026-07-13` の再ベースラインを維持しつつ、T897で未完了タスクの日程を2026-07-18基準へ引き直した（`scripts/recalculate_wbs_schedule.py`、検証は UAT TS-23）。

2026-07-19 セッション確認メモ（T862_1）:

- **Stripe（重要・要追跡）**: 従量課金の公式Docsを確認。Stripeは**新規の従量課金実装では Billing Meters ではなく Metronome を推奨**する方針に更新（Billing Meters は既存実装向けに継続提供。Connect/Checkout/Adaptive Pricing/Workflows との完全互換が必要な場合は Billing Meters を継続）。T791（Billing Meters API 前提・未着手）に影響しうるため R143 を起票。T791実装開始時に公式Dashboard/Docsで最終方式を再判定する（AGENTS.mdの「実装開始時にAPI version再確認」方針に包含）。当プロダクトは Customer Portal（解約：T807）/Checkout 互換を要するため、現時点では Billing Meters 継続が有力。採用は実装開始時に確定。
- Anthropic Claude Code docs（memory/settings）を確認。`CLAUDE.md`→`@AGENTS.md` インポート構成とローカル専用設定（`.claude/settings.local.json`/`CLAUDE.local.md`非コミット）は公式推奨どおり。採用変更なし。
- Supabase / Firebase: サーバーレス構成（インフラ固定費¥0）の前提に変更なし。有償化判断（T862）のコスト材料は `COST_REPORT_2026-06.md` を正とする。採用変更なし。
- お名前.com / GitHub / Sheets / Calendar 運用は 2026-07-13（T893）・2026-07-18（T897/T899）の判断を維持。採用変更なし。

---

## WBSと同期

`data/WBS.tsv` が正本。`docs/WBS.md` は `python scripts/generate_wbs_md.py` で再生成する。

完了したタスクは次を行う。

1. `data/WBS.tsv` の状態を `完了` にする。
2. `docs/WBS.md` を再生成する。
3. 必要な課題/QAを tracker TSV に反映する。
4. `python scripts/sync_wbs_to_github.py TXXX --dry-run` 後、同じIDを実同期する。
5. `python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8` を実行する。
6. `python scripts/sync_wbs_to_calendar.py` を実行する。完了済みWBSに紐づくCalendarイベントは削除される。

---

## closeout

プロジェクト挙動またはdocsを変えたセッションでは、次を実行する。

```powershell
python scripts/generate_knowledge_flow_demo.py
python scripts/sync_wbs_to_github.py TXXX --dry-run
python scripts/sync_wbs_to_github.py TXXX --report exports/github_wbs_sync_report.json
python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8
python scripts/sync_wbs_to_calendar.py
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
```

NotebookLM向けdocsを変更した場合は、追加で次を実行する。

```powershell
python scripts/sync_docs_to_notebooklm.py --skip-asks --skip-source-refresh --source-timeout-seconds 60
python scripts/generate_ceo_presentation_deck.py
python scripts/upload_notebooklm_docs_to_drive.py
```

最後に commit、push `main`、`main` から `master` へ反映し、GitHub Pages のCEO共有URLを守る。
