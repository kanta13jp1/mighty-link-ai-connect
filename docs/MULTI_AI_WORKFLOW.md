# Multi-AI 開発ワークフロー

更新日: 2026-07-13
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

2026-07-13 セッション確認メモ（T893）:

- Anthropic Claude Codeのoverview、memory、settings、securityを確認した。共有ルールは短い `CLAUDE.md` / `AGENTS.md`、反復手順はskills、機械的な強制はhooksへ分ける現行方針と、このプロジェクトの3レーン分担は整合する。
- OpenAI Codexは公式Docs MCPと公式WebでAGENTS.md、best practices、MCPを確認した。Codex manual helperは配布レスポンスの検証ヘッダー欠落で取得できなかったため、公式Docsへフォールバックした。恒久指示、対象限定MCP、反復skill、テストと受入前レビューをT893へ反映した。
- GitHub Issues/Projects/ActionsとGoogle Sheets `batchUpdate` を確認した。Issueを作業記録、ProjectをStatus・日付の横断ビューとし、`scripts/sync_wbs_to_github.py` で対象WBSだけを冪等同期する。Sheetsの正本同期とCalendarの完了イベント削除は従来どおり維持する。
- Google Gemini/Workspace/Firebase、Microsoft Foundry、Meta Llama、AWS Bedrock、Apple ML/HIG、Kimi、MiMo、DeepSeek、xAI、Seedance/BytePlus、Slack、Notion、Obsidian、Unity、Figma、Canva、Reddit、InsForge、Firecrawl、Discord、Stripe、Supabase、お名前.comの公式入口を確認した。今回のGitHub同期タスクに採用変更はなく、レジストラ=お名前.com、バックエンド=Firebase、DB=Supabaseを維持する。
- WBSは `WBS_REVIEW_2026-07-13` の判断に沿って再ベースラインした。旧7/1・7/3レビューは現行判断へ統合し、過去版はGit履歴だけに残す。

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
