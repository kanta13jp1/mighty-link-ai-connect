# Multi-AI 開発ワークフロー

更新日: 2026-06-23
担当レーン: VSCode + Codex  
関連: [WBS.md](WBS.md) / [WBS_SYNC_GUIDE.md](WBS_SYNC_GUIDE.md) / [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) / [CODEX_CONTINUATION_NOTES.md](CODEX_CONTINUATION_NOTES.md)

---

## 目的

Mighty-Link AI Connect は、Antigravity + Gemini、VSCode + Codex、VSCode + Claude Code の三つを役割分担して使う。各セッションで同じ品質ゲートを通し、WBS、課題管理表、QA表、Google Sheets、Google Calendar、GitHub Issues、GitHub Project の状態がずれないようにする。

この文書は毎回の開発開始から closeout までの標準手順を定義する。古いモデル名、未確認の未来機能、解決済みの暫定ブロッカー、古い同期件数は現行ガイドとして残さない。

---

## レーン分担

| レーン | 主担当 | 使う場面 |
| --- | --- | --- |
| Antigravity + Gemini | UI、マルチモーダル、ブラウザ確認 | フロントエンド polish、画像・動画・音声を含むデモ、視覚確認、Gemini API の現行モデルを使う検証 |
| VSCode + Codex | 実装、同期、自動化、GitHub | FastAPI、Firebase/Supabase、Google Workspace API、CI、GitHub CLI、WBS/Sheets/Calendar同期、public demo guard |
| VSCode + Claude Code | ドキュメント、レビュー、triage | 仕様・議事録・Runbook、WBS網羅性監査、PRレビュー、課題/QAの整理、古いdocsの削除判断 |

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

2026-07-03 時点の確認メモ:

- Codex manual は `fetch-codex-manual.mjs` で最新版を取得してから、AGENTS.md、MCP、skills、GitHub連携の判断に使う。
- GitHub Projects は Project #1 `Mighty Skill-Bridge` を正とし、Issueを追加したらStatusをDoneまで更新する。
- Gemini API の現行安定版は 3.5 Flash / 3.1 Flash-Lite。Gemini 2.0 系はシャットダウン済み。本番既定は `gemini-3.5-flash`（QA-89）で、T780 の移行評価はGA後（2026-07-09〜）に実施する。
- Stripe Customer Portal は、サブスクリプション管理、支払方法、請求書、解約を顧客が管理できるHosted UIとして扱う。T829でアプリ側セッションAPIとdry-run導線を整備済みで、T807でStripe Dashboard live有効化・本番検証を完了する。
- Supabase Postgres 14 はサポート終了日（2026-07-01）を超過済み。公式ガイドはPostgres 17への移行を主対象に案内しており、T811（バージョン確認・計画）とT837（アップグレード実行）を最優先で完了する。
- InsForge は導入判断前に `skill.md` を確認する。現行バックエンド方針は Firebase、DBは Supabase のままにする。
- OWASP WSTG / ZAP 相当の外部疑似診断はT805で実施済み。High 0 / secret-like値露出 0 を維持し、T835でFirebase Hosting本番URLのCSP等ヘッダhardeningを完了済み。GitHub Pagesは任意HTTPヘッダを設定できないためcontrolled demo mirrorとして扱う。
- WBSスケジュールは 2026-07-03 に再ベースライン済み（T859、[WBS_REVIEW_2026-07-03.md](WBS_REVIEW_2026-07-03.md)）。ローンチ2026-07-08・Phase 7-9最終完了2026-07-15をアンカーとし、人間依存ゲートの必着日はR111で追跡する。

---

## WBSと同期

`data/WBS.tsv` が正本。`docs/WBS.md` は `python scripts/generate_wbs_md.py` で再生成する。

完了したタスクは次を行う。

1. `data/WBS.tsv` の状態を `完了` にする。
2. `docs/WBS.md` を再生成する。
3. 必要な課題/QAを tracker TSV に反映する。
4. `python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8` を実行する。
5. `python scripts/sync_wbs_to_calendar.py` を実行する。完了済みWBSに紐づくCalendarイベントは削除される。
6. GitHub Issue と Project #1 を更新する。

---

## closeout

プロジェクト挙動またはdocsを変えたセッションでは、次を実行する。

```powershell
python scripts/generate_knowledge_flow_demo.py
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

---

## 今回の反映

- T827として、毎セッションの公式Docs確認対象と3ツール運用ゲートを再整備した。
- T805として、非破壊の外部ペネトレーション疑似診断を実施し、High 0 / secret-like値露出 0 を確認した。
- T835として、Firebase Hosting本番URLにCSP / X-Content-Type-Options / Referrer-Policy / Permissions-Policy / frame protection / HSTSを設定し、R94/SEC-008を解決した。
